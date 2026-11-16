import copy
import json
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
from tests import test_pocketpad as support
from virtual_gamepad import GamepadEngine, VirtualXboxBackend, build_report, neutral_report
from windows_input import InputEngine


class FakePad:
    available = True

    def __init__(self):
        self.connected = False
        self.reports = []
        self.fail = False

    def diagnostics(self):
        return {"supported": True, "package_installed": True, "connected": self.connected, "error": ""}

    def connect(self):
        self.connected = True

    def send(self, report):
        if self.fail:
            raise RuntimeError("Disconnected virtual device")
        self.reports.append(copy.deepcopy(report))

    def disconnect(self):
        self.connected = False


class ProfileStorageTests(unittest.TestCase):
    def test_saved_profile_survives_restart_and_keeps_bindings_layout_and_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'
            store = ProfileStore(path)
            value = templates()['xbox_racing']; value['name'] = 'My native racer'
            value['mapping']['nitro'] = 'ctrl'; value['tuning']['sensitivity'] = 1.3
            key = store.save(value)
            reloaded = ProfileStore(path)
            self.assertEqual(reloaded.get(key), value)
            self.assertEqual(reloaded.catalogue()[-1]['name'], 'My native racer')

    def test_invalid_import_cannot_add_commands_or_override_templates(self):
        store = ProfileStore()
        for mutation in [{'mapping': {'a': 'shell.exe'}}, {'layout': []}, {'output_mode': {}},
                         {'pad_mapping': {'a': 'execute'}}, {'tuning': {'deadzone': float('nan')}}]:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                store.save({**templates()['xbox_standard'], **mutation})
        with self.assertRaises(ValueError):
            store.save(templates()['arrows'], 'arrows')
        self.assertEqual(store.saved, {})

    def test_corrupt_file_is_preserved_and_cannot_be_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'; path.write_text('{broken')
            store = ProfileStore(path)
            self.assertTrue(store.error)
            with self.assertRaises(ValueError): store.save(templates()['arrows'])
            self.assertEqual(path.read_text(), '{broken')

    def test_failed_atomic_replace_keeps_previous_file_and_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'; store = ProfileStore(path)
            store.save(templates()['arrows']); before = path.read_bytes(); saved = copy.deepcopy(store.saved)
            with patch('controller_profiles.os.replace', side_effect=OSError('Disk full')):
                with self.assertRaises(OSError): store.save(templates()['xbox_standard'])
            self.assertEqual(path.read_bytes(), before); self.assertEqual(store.saved, saved)


class XboxMappingTests(unittest.TestCase):
    def test_racing_uses_analog_left_stick_and_independent_trigger_pedals(self):
        profile = templates()['xbox_racing']
        report = build_report({'a', 'b', 'handbrake', 'nitro'}, {}, -.56, profile)
        self.assertAlmostEqual(report['lx'], -.5)
        self.assertEqual((report['lt'], report['rt']), (1, 1))
        self.assertEqual(report['buttons'], ['a', 'x'])

    def test_deadzone_sensitivity_diagonal_clamp_and_inversion(self):
        profile = templates()['xbox_standard']
        profile['tuning'] = {'deadzone': .1, 'sensitivity': 2, 'invert_y': True}
        report = build_report(set(), {'lx': .05, 'ly': .04, 'rx': 1, 'ry': 1, 'rt': .35}, 0, profile)
        self.assertEqual((report['lx'], report['ly']), (0, 0))
        self.assertAlmostEqual(report['rx'] ** 2 + report['ry'] ** 2, 1)
        self.assertLess(report['ry'], 0); self.assertEqual(report['rt'], .35)

    def test_gamepad_focus_change_and_disconnect_failure_return_to_neutral(self):
        focus = support.FakeKeyboard(); backend = FakePad(); backend.connect()
        engine = GamepadEngine(focus, backend); engine.arm()
        engine.apply({**neutral_report(), 'rt': 1, 'lx': .5})
        focus.window = 88; engine.apply({**neutral_report(), 'rt': 1})
        self.assertFalse(engine.armed); self.assertEqual(backend.reports[-1], neutral_report())
        engine.arm(); engine.apply({**neutral_report(), 'rt': 1})
        backend.fail = True; engine.disarm(); self.assertTrue(engine.neutral_pending)
        backend.fail = False; engine.apply(neutral_report()); self.assertFalse(engine.neutral_pending)
        self.assertEqual(backend.reports[-1], neutral_report())

    def test_adapter_uses_vgamepad_api_and_flips_screen_y_to_xinput_y(self):
        calls = []
        class Pad:
            def reset(self): calls.append(('reset',))
            def left_joystick_float(self, **data): calls.append(('left', data))
            def right_joystick_float(self, **data): calls.append(('right', data))
            def left_trigger_float(self, **data): calls.append(('lt', data))
            def right_trigger_float(self, **data): calls.append(('rt', data))
            def press_button(self, **data): calls.append(('button', data))
            def update(self): calls.append(('update',))
        backend = VirtualXboxBackend(); backend.available = True
        module = SimpleNamespace(VX360Gamepad=Pad, XUSB_BUTTON=SimpleNamespace(XUSB_GAMEPAD_A=4096))
        with patch('virtual_gamepad.importlib.import_module', return_value=module): backend.connect()
        backend.send({**neutral_report(), 'lx': .2, 'ly': -.4, 'ry': .3, 'rt': .6, 'buttons': ['a']})
        self.assertIn(('left', {'x_value_float': .2, 'y_value_float': .4}), calls)
        self.assertIn(('right', {'x_value_float': 0, 'y_value_float': -.3}), calls)
        self.assertIn(('button', {'button': 4096}), calls)
        backend.disconnect(); self.assertFalse(backend.connected)
        backend.pad = Pad()
        with patch.object(backend, 'send', side_effect=RuntimeError('Driver lost')):
            with self.assertRaises(RuntimeError): backend.disconnect()
        self.assertFalse(backend.connected)


class AdaptiveProtocolTests(support.ProtocolFixture):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.backend = support.FakeKeyboard(); self.pad_backend = FakePad()
        self.app = create_app(engine=InputEngine(self.backend), gamepad_backend=self.pad_backend,
                              profile_path=Path(self.folder.name) / 'profiles.json', addresses={'localhost', '127.0.0.1'})
        self.room = self.app.state.room
        self.client = TestClient(self.app, base_url='http://localhost:8765', client=('127.0.0.1', 50000))
        self.client.__enter__(); self.path = f'ws://localhost:8765/ws/controller?token={self.room.token}'
        self.origin = {'origin': 'http://localhost:8765'}; self.admin = {**self.origin, 'x-pocketpad-admin': self.room.admin}

    def tearDown(self):
        self.client.__exit__(None, None, None); self.folder.cleanup()

    def test_save_load_export_import_preserves_live_custom_profile(self):
        self.client.post('/api/mapping', json={'mapping': {'a': 'z', 'b': 'x'}}, headers=self.admin)
        saved = self.client.post('/api/profiles', json={'name': 'My platformer'}, headers=self.admin).json()
        key = saved['profile']; self.assertTrue(key.startswith('saved_'))
        self.client.post('/api/profile', json={'profile': 'racing_arrows'}, headers=self.admin)
        loaded = self.client.post('/api/profile', json={'profile': key}, headers=self.admin).json()
        self.assertEqual(loaded['mapping']['a'], 'z'); self.assertEqual(loaded['layout'], 'gamepad')
        exported = self.client.get('/api/current-profile').json()
        imported = self.client.post('/api/profiles', json={'profile': exported['profile']}, headers=self.admin)
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(ProfileStore(Path(self.folder.name) / 'profiles.json').get(key)['mapping']['a'], 'z')

    def test_switching_output_and_profiles_neutralizes_both_engines(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm(); self.send(ws, 0, ['a']); self.assertTrue(self.room.engine.held)
            self.client.post('/api/profile', json={'profile': 'xbox_racing'}, headers=self.admin)
            self.assertFalse(self.room.engine.held); self.assertFalse(self.room.engine.armed)
            self.client.post('/api/gamepad', json={'action': 'connect'}, headers=self.admin)
            self.room.pad.arm()
            ws.send_json({'seq': 1, 'buttons': ['a'], 'steering': .6}); ws.receive_json()
            self.assertEqual(self.pad_backend.reports[-1]['rt'], 1)
            self.client.post('/api/output', json={'mode': 'keyboard'}, headers=self.admin)
            self.assertEqual(self.pad_backend.reports[-1], neutral_report())
            self.assertFalse(self.room.pad.armed)

    def test_dual_axes_are_analog_without_duplicate_dpad_and_disconnect_neutralizes(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.client.post('/api/profile', json={'profile': 'xbox_standard'}, headers=self.admin)
            self.pad_backend.connect(); self.room.pad.arm()
            ws.send_json({'seq': 0, 'buttons': ['a'], 'axes': {'lx': .6, 'ly': -.3, 'rx': -.4, 'rt': .25}})
            ack = ws.receive_json(); self.assertEqual(ack['layout'], 'dualstick')
            report = self.pad_backend.reports[-1]
            self.assertEqual(report['buttons'], ['a']); self.assertGreater(report['lx'], .4)
            self.assertIn('right', self.room.buttons); self.assertNotIn('dpad_right', report['buttons'])
        self.assertEqual(self.pad_backend.reports[-1], neutral_report()); self.assertFalse(self.room.pad.armed)

    def test_phone_emergency_stop_disarms_and_releases_outputs(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm(); self.send(ws, 0, ['a'])
            ws.send_json({'seq': 1, 'buttons': ['a'], 'disarm': True}); ack = ws.receive_json()
            self.assertFalse(ack['armed']); self.assertFalse(self.room.engine.held); self.assertFalse(self.room.buttons)

    def test_gamepad_timeout_neutralizes_right_stick_and_trigger(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.client.post('/api/profile', json={'profile': 'xbox_standard'}, headers=self.admin)
            self.pad_backend.connect(); self.room.pad.arm()
            ws.send_json({'seq': 0, 'buttons': [], 'axes': {'rx': .8, 'rt': .6}}); ws.receive_json()
            self.assertGreater(self.pad_backend.reports[-1]['rx'], .5)
            time.sleep(.9)
            self.assertFalse(self.room.pad.armed)
            self.assertEqual(self.pad_backend.reports[-1], neutral_report())

    def test_invalid_axes_and_optional_backend_failures_do_not_break_keyboard(self):
        for axes in [{'lx': True}, {'rx': float('nan')}, {'lt': -.2}, {'rt': 1.1}, {'command': 0}, []]:
            with self.client.websocket_connect(self.path, headers=self.origin) as ws:
                ws.send_json({'seq': 0, 'buttons': [], 'axes': axes})
                with self.assertRaises(WebSocketDisconnect): ws.receive_json()
        self.assertEqual(self.client.post('/api/output', json={'mode': []}, headers=self.admin).status_code, 400)
        self.assertEqual(self.client.post('/api/gamepad', json={'action': []}, headers=self.admin).status_code, 400)
        with patch.object(self.pad_backend, 'connect', side_effect=RuntimeError('Driver missing')):
            self.assertEqual(self.client.post('/api/gamepad', json={'action': 'connect'}, headers=self.admin).status_code, 400)
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm(); self.send(ws, 0, ['left']); self.assertIn('left', self.room.engine.held)

    def test_profiles_and_gamepad_actions_remain_host_admin_only(self):
        for path, payload in [('/api/profiles', {'name': 'bad'}), ('/api/gamepad', {'action': 'connect'}),
                              ('/api/output', {'mode': 'gamepad'}), ('/api/tuning', {})]:
            self.assertEqual(self.client.post(path, json=payload).status_code, 403)
        self.assertEqual(self.client.get('/controller-test').status_code, 200)
