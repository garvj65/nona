import ctypes
import json
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server import create_app
from windows_input import InputEngine, WindowsKeyboard


class FakeKeyboard:
    available = True

    def __init__(self):
        self.window = 41
        self.events = []
        self.fail = False

    def foreground(self):
        return self.window

    def title(self, window):
        return "Test game"

    def send(self, key, pressed):
        if self.fail:
            raise OSError("Injected input rejected")
        self.events.append((key, pressed))


class InputLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeKeyboard()
        self.engine = InputEngine(self.backend)

    def test_reconciles_held_combinations_without_repeating_keydown(self):
        self.engine.arm()
        self.engine.apply({"left", "space"})
        self.engine.apply({"left", "space"})
        self.assertEqual(self.backend.events, [("left", True), ("space", True)])
        self.engine.apply({"right"})
        self.assertEqual(self.backend.events[-3:], [("left", False), ("space", False), ("right", True)])
        self.engine.disarm()
        self.assertEqual(self.backend.events[-1], ("right", False))
        self.assertFalse(self.engine.held)

    def test_changing_foreground_disarms_and_releases_owned_keys(self):
        self.engine.arm()
        self.engine.apply({"w"})
        self.backend.window = 99
        self.engine.apply({"w", "space"})
        self.assertFalse(self.engine.armed)
        self.assertEqual(self.backend.events, [("w", True), ("w", False)])

    def test_rejected_release_is_retried(self):
        self.engine.arm()
        self.engine.apply({"a"})
        self.backend.fail = True
        self.engine.disarm()
        self.assertEqual(self.engine.held, {"a"})
        self.backend.fail = False
        self.engine.apply(set())
        self.assertFalse(self.engine.held)
        self.assertEqual(self.backend.events[-1], ("a", False))

    def test_rejected_press_disarms_and_records_error(self):
        self.engine.arm()
        self.backend.fail = True
        self.engine.apply({"space"})
        self.assertFalse(self.engine.armed)
        self.assertIn("rejected", self.engine.error)

    def test_windows_abi_and_extended_arrow_flags(self):
        class Function:
            def __init__(self, callback):
                self.callback = callback
            def __call__(self, *args):
                return self.callback(*args)
        received = []
        fake_api = SimpleNamespace(
            SendInput=Function(lambda count, ptr, size: received.append((count, ptr._obj.type,
                ptr._obj.ki.wScan, ptr._obj.ki.dwFlags, size)) or 1),
            GetForegroundWindow=Function(lambda: 41),
            GetWindowTextLengthW=Function(lambda _: 0),
            GetWindowTextW=Function(lambda *args: 0),
        )
        with patch("windows_input.sys", SimpleNamespace(platform="win32")), \
                patch("ctypes.WinDLL", return_value=fake_api, create=True):
            adapter = WindowsKeyboard()
            adapter.send("left", True)
            adapter.send("left", False)
            adapter.send("space", True)
        expected_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
        self.assertEqual(received, [(1, 1, 0x4B, 0x9, expected_size),
                                   (1, 1, 0x4B, 0xB, expected_size),
                                   (1, 1, 0x39, 0x8, expected_size)])


class ProtocolFixture(unittest.TestCase):
    def setUp(self):
        self.backend = FakeKeyboard()
        self.app = create_app(engine=InputEngine(self.backend), addresses={"localhost", "127.0.0.1", "192.168.1.10"})
        self.room = self.app.state.room
        self.client = TestClient(self.app, base_url="http://localhost:8765", client=("127.0.0.1", 50000))
        self.client.__enter__()
        self.path = f"ws://localhost:8765/ws/controller?token={self.room.token}"
        self.origin = {"origin": "http://localhost:8765"}
        self.admin = {**self.origin, "x-pocketpad-admin": self.room.admin}

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def send(self, ws, seq=0, buttons=None):
        ws.send_json({"seq": seq, "buttons": buttons or []})
        return ws.receive_json()



class ProtocolTests(ProtocolFixture):
    def test_pairing_and_origin_required(self):
        for path, headers in [("ws://localhost:8765/ws/controller?token=wrong", self.origin),
                              (self.path, {"origin": "https://unrelated.example"}),
                              (self.path, {})]:
            with self.subTest(path=path, headers=headers):
                with self.assertRaises(WebSocketDisconnect):
                    with self.client.websocket_connect(path, headers=headers):
                        pass

    def test_second_controller_cannot_take_over_and_reconnect_works(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as first:
            self.send(first)
            with self.assertRaises(WebSocketDisconnect):
                with self.client.websocket_connect(self.path, headers=self.origin):
                    pass
            self.send(first, 1, ["left", "a"])
            self.assertEqual(self.room.buttons, {"left", "a"})
        with self.client.websocket_connect(self.path, headers=self.origin) as second:
            self.assertEqual(self.send(second)["seq"], 0)
        self.assertFalse(self.room.buttons)

    def test_disconnect_releases_keyboard_and_disarms(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            self.send(ws, buttons=["right", "a"])
            time.sleep(.06)
            self.assertEqual(self.room.engine.held, {"right", "space"})
        self.assertFalse(self.room.engine.armed)
        self.assertFalse(self.room.engine.held)
        self.assertIn(("right", False), self.backend.events)
        self.assertIn(("space", False), self.backend.events)

    def test_dead_connection_times_out_and_releases_keyboard(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            self.send(ws, buttons=["up"])
            time.sleep(.06)
            self.assertIn("up", self.room.engine.held)
            time.sleep(.88)
            self.assertFalse(self.room.engine.armed)
            self.assertFalse(self.room.buttons)
            self.assertFalse(self.room.engine.held)
            self.assertFalse(self.room.status()["connected"])

    def test_invalid_packets_close_and_release(self):
        packets = [{"seq": 0, "buttons": ["shell"]}, {"seq": True, "buttons": []},
                   {"seq": 0, "buttons": [{}]}, ["not-an-object"], {"seq": 0, "buttons": ["a"] * 11}]
        for packet in packets:
            with self.subTest(packet=packet):
                with self.client.websocket_connect(self.path, headers=self.origin) as ws:
                    self.room.engine.arm()
                    ws.send_json(packet)
                    with self.assertRaises(WebSocketDisconnect):
                        ws.receive_json()
                self.assertFalse(self.room.engine.armed)
                self.assertFalse(self.room.buttons)

    def test_old_sequence_closes_connection(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.send(ws, seq=10, buttons=["a"])
            ws.send_json({"seq": 9, "buttons": ["left"]})
            with self.assertRaises(WebSocketDisconnect):
                ws.receive_json()
        self.assertFalse(self.room.buttons)

    def test_admin_actions_need_loopback_origin_and_nonce(self):
        self.assertEqual(self.client.post("/api/keyboard", json={"enabled": True}).status_code, 403)
        self.assertEqual(self.client.post("/api/keyboard", json={"enabled": True}, headers=self.admin).status_code, 400)
        remote = TestClient(self.app, base_url="http://localhost:8765", client=("192.168.1.22", 50001))
        self.assertEqual(remote.get("/api/session").status_code, 403)
        self.assertEqual(remote.post("/api/keyboard", json={"enabled": True}, headers=self.admin).status_code, 403)
        self.assertEqual(remote.get("/controller").status_code, 200)
        self.assertNotIn(self.room.token, remote.get("/controller").text)

    def test_profile_change_disarms_and_releases(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.send(ws, buttons=["up"])
            self.room.engine.arm()
            time.sleep(.06)
            response = self.client.post("/api/profile", json={"profile": "wasd"}, headers=self.admin)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.room.engine.held)
            self.assertFalse(self.room.engine.armed)
            self.assertEqual(self.room.profile, "wasd")

    def test_keyboard_arming_waits_for_window_selection(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.send(ws)
            response = self.client.post("/api/keyboard", json={"enabled": True}, headers=self.admin)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.room.engine.armed)
            self.assertGreater(response.json()["countdown"], 3)
            self.backend.window = 88
            self.room.arm_at = time.monotonic() - 1
            time.sleep(.06)
            self.assertTrue(self.room.engine.armed)
            self.assertEqual(self.room.engine.target, 88)
            self.send(ws, seq=1, buttons=["down"])
            time.sleep(.06)
            self.assertEqual(self.room.engine.held, {"down"})

    def test_dashboard_and_static_assets(self):
        for path in ["/", "/controller", "/game", "/static/style.css", "/static/game.js"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["cache-control"], "no-store")
        unknown_host = self.client.get("/controller", headers={"host": "unrelated.example"})
        self.assertEqual(unknown_host.status_code, 400)


if __name__ == "__main__":
    unittest.main()
