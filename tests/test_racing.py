import time
from starlette.websockets import WebSocketDisconnect
from tests import test_pocketpad as support
from server import steering_direction


class RacingTests(support.ProtocolFixture):
    def test_racing_pedals_alias_without_releasing_a_still_held_key(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            response = self.client.post('/api/profile', json={'profile': 'racing_arrows'}, headers=self.admin)
            self.assertEqual(response.status_code, 200)
            self.room.engine.arm()
            self.send(ws, 0, ['up', 'a', 'left', 'nitro', 'handbrake'])
            self.assertEqual(self.room.engine.held, {'up', 'left', 'shift', 'space'})
            self.send(ws, 1, ['a'])
            self.assertEqual(self.room.engine.held, {'up'})
            self.assertEqual(self.backend.events.count(('up', True)), 1)
            self.assertNotIn(('up', False), self.backend.events)
            self.send(ws, 2, [])
            self.assertIn(('up', False), self.backend.events)

    def test_wheel_hysteresis_switches_and_centres_without_stuck_keys(self):
        self.assertEqual(steering_direction(.18, 0), 0)
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            for seq, value, keys in [(0, .6, {'right'}), (1, .18, {'right'}),
                                     (2, .1, set()), (3, -.7, {'left'}), (4, 0, set())]:
                ws.send_json({'seq': seq, 'buttons': [], 'steering': value})
                ws.receive_json()
                self.assertEqual(self.room.engine.held, keys)
            self.assertEqual(self.backend.events.count(('right', True)), 1)

    def test_legacy_packets_and_new_ack_config(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            ack = self.send(ws, 0, ['left'])
            self.assertEqual(ack['layout'], 'gamepad')
            self.assertEqual(ack['profile'], 'arrows')
            self.assertEqual(self.room.steering, 0)

    def test_phone_profile_selection_disarms_and_clears_held_inputs(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.room.engine.arm()
            self.send(ws, 0, ['a'])
            ws.send_json({'seq': 1, 'buttons': ['a'], 'steering': .8, 'profile': 'racing_wasd'})
            ack = ws.receive_json()
            self.assertEqual(ack['layout'], 'racing')
            self.assertFalse(self.room.engine.armed)
            self.assertFalse(self.room.buttons)
            self.assertFalse(self.room.engine.held)
            self.assertEqual(ack['mapping']['a'], 'w')

    def test_custom_mapping_applies_and_presets_restore_defaults(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            self.send(ws)
            self.room.engine.arm()
            self.send(ws, 1, ['a'])
            response = self.client.post('/api/mapping', json={'mapping': {'a': 'w', 'b': '', 'nitro': 'ctrl'}}, headers=self.admin)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.room.engine.armed)
            self.room.engine.arm()
            self.send(ws, 2, ['a', 'b', 'nitro'])
            self.assertEqual(self.room.engine.held, {'w', 'ctrl'})
            self.client.post('/api/profile', json={'profile': 'racing_arrows'}, headers=self.admin)
            self.assertEqual(self.room.mapping['a'], 'up')
            self.assertFalse(self.room.engine.held)

    def test_invalid_axis_and_mapping_rejected(self):
        for value in [True, 2, -1.01, float('nan'), float('inf'), 10 ** 100, 'left']:
            with self.subTest(value=value):
                with self.client.websocket_connect(self.path, headers=self.origin) as ws:
                    ws.send_json({'seq': 0, 'buttons': [], 'steering': value})
                    with self.assertRaises(WebSocketDisconnect):
                        ws.receive_json()
        for mapping in [{'a': 'win'}, {'launch': 'w'}, {'a': 7}, {}]:
            self.assertEqual(self.client.post('/api/mapping', json={'mapping': mapping}, headers=self.admin).status_code, 400)
        self.assertEqual(self.client.post('/api/mapping', json={'mapping': {'a': 'w'}}).status_code, 403)

    def test_disconnect_clears_axis_and_pedals(self):
        with self.client.websocket_connect(self.path, headers=self.origin) as ws:
            ws.send_json({'seq': 0, 'buttons': ['a'], 'steering': -.9})
            ws.receive_json()
            self.assertIn('left', self.room.buttons)
        self.assertEqual(self.room.steering, 0)
        self.assertEqual(self.room.steer_direction, 0)
        self.assertFalse(self.room.buttons)

    def test_race_routes_and_assets(self):
        for path in ['/race', '/static/race.js', '/static/race-physics.js', '/static/race.css']:
            self.assertEqual(self.client.get(path).status_code, 200)
