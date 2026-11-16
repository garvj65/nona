import copy
import ctypes
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from controller_profiles import ProfileStore, templates, validate_profile
from server import create_app
from tests.test_pocketpad import FakeKeyboard
from windows_input import InputEngine, WindowsKeyboard


class PointerBackend(FakeKeyboard):
    def __init__(self):
        super().__init__()
        self.pointer_events = []
        self.mouse_fail = False

    def mouse_right(self, pressed):
        if self.mouse_fail:
            raise OSError('Mouse input rejected')
        self.pointer_events.append(('right', pressed))

    def mouse_move(self, dx, dy):
        if self.mouse_fail:
            raise OSError('Mouse input rejected')
        self.pointer_events.append(('move', dx, dy))


class PointerLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.backend = PointerBackend()
        self.engine = InputEngine(self.backend)
        self.engine.arm()

    def test_fractional_moves_accumulate_once_and_drag_release_resets_remainder(self):
        for _ in range(3):
            self.engine.apply_pointer(.4, -.4, True)
        self.assertEqual(self.backend.pointer_events, [('right', True), ('move', 1, -1)])
        self.engine.apply_pointer(right=False)
        self.assertEqual(self.backend.pointer_events[-1], ('right', False))
        self.assertEqual(self.engine.mouse_remainder, [0, 0])

    def test_focus_loss_releases_keys_and_owned_right_button_before_any_motion(self):
        self.engine.apply({'w'})
        self.engine.apply_pointer(2, 3, True)
        self.backend.window = 99
        self.engine.apply_pointer(100, 100, True)
        self.assertFalse(self.engine.armed)
        self.assertFalse(self.engine.held)
        self.assertFalse(self.engine.right_held)
        self.assertEqual(self.backend.pointer_events, [('right', True), ('move', 2, 3), ('right', False)])

    def test_failed_mouse_release_is_retried_and_prevents_rearming(self):
        self.engine.apply_pointer(right=True)
        self.backend.mouse_fail = True
        self.engine.disarm()
        self.assertTrue(self.engine.right_held)
        with self.assertRaises(RuntimeError):
            self.engine.arm()
        self.backend.mouse_fail = False
        self.engine.apply(set())
        self.assertFalse(self.engine.right_held)
        self.assertEqual(self.backend.pointer_events[-1], ('right', False))

    def test_first_person_moves_without_owning_right_mouse(self):
        self.engine.apply_pointer(5, -4, False)
        self.assertEqual(self.backend.pointer_events, [('move', 5, -4)])
        self.engine.disarm()
        self.assertEqual(self.backend.pointer_events, [('move', 5, -4)])

    def test_windows_mouse_abi_uses_relative_move_and_right_button_flags(self):
        class Function:
            def __init__(self, callback): self.callback = callback
            def __call__(self, *args): return self.callback(*args)
        received = []
        api = SimpleNamespace(
            SendInput=Function(lambda count, ptr, size: received.append(
                (ptr._obj.type, ptr._obj.mi.dx, ptr._obj.mi.dy, ptr._obj.mi.dwFlags, size)) or 1),
            GetForegroundWindow=Function(lambda: 41),
            GetWindowTextLengthW=Function(lambda _: 0),
            GetWindowTextW=Function(lambda *args: 0))
        with patch('windows_input.sys', SimpleNamespace(platform='win32')), \
                patch('ctypes.WinDLL', return_value=api, create=True):
            backend = WindowsKeyboard()
            backend.mouse_right(True)
            backend.mouse_move(-8, 13)
            backend.mouse_right(False)
        size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
        self.assertEqual(received, [(0, 0, 0, 8, size), (0, -8, 13, 1, size), (0, 0, 0, 16, size)])


class MobileProfileTests(unittest.TestCase):
    def test_old_profiles_default_to_no_mouse_and_mobile_settings_survive_storage(self):
        old = templates()['arrows']; old.pop('look')
        self.assertFalse(validate_profile(old)['look']['enabled'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'
            store = ProfileStore(path)
            profile = templates()['roblox_mobile']
            profile['look']['sensitivity'] = 1.75
            key = store.save(profile)
            self.assertEqual(ProfileStore(path).get(key), profile)

    def test_camera_import_rejects_nonfinite_or_unbounded_settings_and_wrong_mode(self):
        profile = templates()['roblox_mobile']
        for change in [{'look': []}, {'look': {'command': 'run'}},
                       {'look': {'enabled': 1}}, {'look': {'hold_right': 'yes'}},
                       {'look': {'sensitivity': float('nan')}}, {'look': {'sensitivity': 5}},
                       {'look': {'sensitivity': True}}, {'output_mode': 'gamepad'}, {'layout': 'racing'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_profile({**copy.deepcopy(profile), **change})


class MobileProtocolTests(unittest.TestCase):
    def setUp(self):
        self.backend = PointerBackend()
        self.app = create_app(engine=InputEngine(self.backend), addresses={'localhost', '127.0.0.1'})
        self.room = self.app.state.room
        self.client = TestClient(self.app, base_url='http://localhost:8765', client=('127.0.0.1', 50000))
        self.client.__enter__()
        self.origin = {'origin': 'http://localhost:8765'}
        self.admin = {**self.origin, 'x-pocketpad-admin': self.room.admin}
        self.path = f'ws://localhost:8765/ws/controller?token={self.room.token}'
        self.room.set_profile('roblox_mobile')

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def packet(self, ws, seq=0, **fields):
        ws.send_json({'seq': seq, 'buttons': [], **fields})
        return ws.receive_json()

    def test_move_look_jump_concurrently_and_do_not_replay_relative_deltas(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            self.packet(ws, buttons=['a'], axes={'lx': .6, 'ly': -.6},
                        pointer={'dx': 12, 'dy': -8, 'active': True})
            self.assertEqual(self.room.engine.held, {'w', 'd', 'space'})
            self.assertTrue(self.room.engine.right_held)
            before = list(self.backend.pointer_events)
            time.sleep(.12)
            self.packet(ws, 1, pointer={'active': True})
            self.assertEqual(self.backend.pointer_events, before)
            self.packet(ws, 2)
            self.assertFalse(self.room.engine.right_held)
        self.assertFalse(self.room.engine.armed)
        self.assertFalse(self.room.engine.held)

    def test_stop_and_profile_changes_discard_motion_and_release_drag(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            self.packet(ws, pointer={'active': True})
            self.packet(ws, 1, disarm=True, pointer={'active': True, 'dx': 96})
            self.assertFalse(self.room.look_active)
            self.assertFalse(self.room.engine.right_held)
            self.assertNotIn(('move', 96, 0), self.backend.pointer_events)
            self.room.engine.arm()
            self.packet(ws, 2, pointer={'active': True})
            self.packet(ws, 3, profile='arrows', pointer={'active': True, 'dx': 96})
            self.assertFalse(self.room.engine.right_held)
            self.assertFalse(self.room.engine.armed)

    def test_invalid_camera_packets_cannot_inject_or_leave_held_mouse(self):
        for pointer in [[], {'active': 1}, {'dx': True}, {'dy': None}, {'dx': float('nan')},
                        {'dy': float('inf')}, {'dx': 97}, {'wheel': 1}]:
            with self.subTest(pointer=pointer):
                with self.client.websocket_connect(self.path, headers=self.origin) as ws:
                    self.room.engine.arm()
                    self.packet(ws, pointer={'active': True})
                    ws.send_json({'seq': 1, 'buttons': [], 'pointer': pointer})
                    with self.assertRaises(WebSocketDisconnect): ws.receive_json()
                self.assertFalse(self.room.engine.armed)
                self.assertFalse(self.room.engine.right_held)

    def test_disabled_camera_and_inactive_clutch_ignore_mouse_deltas(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            self.packet(ws, pointer={'dx': 30, 'active': False})
            self.assertFalse(self.backend.pointer_events)
            self.room.set_profile('arrows'); self.room.engine.arm()
            self.packet(ws, 1, pointer={'dx': 30, 'active': True})
            self.assertFalse(self.backend.pointer_events)

    def test_disconnect_and_silence_neutralize_held_drag(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm(); self.packet(ws, pointer={'active': True})
        self.assertFalse(self.room.engine.right_held)
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm(); self.packet(ws, pointer={'active': True})
            time.sleep(.9)
            self.assertFalse(self.room.engine.armed)
            self.assertFalse(self.room.engine.right_held)

    def test_camera_settings_are_host_admin_only_and_release_before_changing(self):
        self.assertEqual(self.client.post('/api/look', json={'enabled': True}).status_code, 403)
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm(); self.packet(ws, pointer={'active': True})
            response = self.client.post('/api/look', headers=self.admin,
                                        json={'enabled': True, 'sensitivity': 2, 'hold_right': False})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.room.engine.armed)
            self.assertFalse(self.room.engine.right_held)
            self.assertEqual(self.room.look['sensitivity'], 2)
        self.assertEqual(self.client.post('/api/look', json={'sensitivity': 100}, headers=self.admin).status_code, 400)


if __name__ == '__main__':
    unittest.main()
