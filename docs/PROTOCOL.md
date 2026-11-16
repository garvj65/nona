# Controller protocol 0.3

Connect to `/ws/controller?token=<per-launch pairing token>` from the controller's own origin. One controller can own the room. Profiles and mappings are room-local, reset on server restart, and are not persisted yet.

A normal packet is a full state snapshot:

```json
{"seq": 42, "buttons": ["a", "nitro"], "steering": -0.45}
```

- `seq`: strictly increasing integer for this WebSocket connection; reset on reconnect.
- `buttons`: at most 10 entries from up, down, left, right, a, b, start, select, handbrake, nitro.
- `steering`: optional finite number from -1 to 1. Missing means 0, preserving starter compatibility.
- `profile`: optional request for arrows, wasd, racing_arrows, or racing_wasd. Changing the preset clears input and disables keyboard mode before acknowledging. This is allowed to the already-paired controller, not to anonymous HTTP requests.

Acknowledgements include the authoritative profile, layout, key mapping and armed state:

```json
{"type":"ack","seq":42,"profile":"racing_arrows","layout":"racing","mapping":{"a":"up","b":"down"},"armed":false}
```

The example mapping is abbreviated; real acknowledgements carry the complete current mapping. The phone sends changes immediately and heartbeats every 100 ms. Wheel-motion messages are throttled to about 40 Hz; button edges are immediate. Acknowledgement RTT is not input-to-display latency.

The host validates the pairing token, same origin, actions, sequence, finite axis range and rate/size limits. A timeout of 800 ms clears axes/buttons and disarms keyboard; normal disconnect does the same. The watchdog checks state/focus every 25 ms. Profile and mapping changes also release owned keys.

Laptop-local `/ws/monitor` provides full `status` packets on changes plus periodic refreshes. `buttons` includes digital directions derived from the axis, while `steering` retains its original proportional value. `/api/profile`, `/api/mapping` and `/api/keyboard` require loopback access, matching origin, and the dashboard admin nonce. The original X-PocketPad-Admin header and pairing storage key are kept for compatibility.

Mapping values use a small allowed set of game keys, not arbitrary commands. An empty mapping value disables that action. Several held actions may map to the same key; the key is released only after all those actions are released.

Local transport currently uses unencrypted HTTP/WS on a trusted LAN. The protocol is not an internet-exposed remote-control service.


## 0.3 additions

Packets can also carry `axes`: `{"lx":0.5,"ly":-0.2,"rx":0,"ry":0,"lt":0,"rt":0.6}`. Stick axes use [-1,1], with Y positive down on the phone; triggers use [0,1]. Missing axes default to zero. The Xbox adapter flips Y to XInput convention. New actions are x, y, lb, rb, lt and rt; all 16 action names are allowed, without duplicates. `disarm:true` is a phone emergency stop. Legacy button/steering packets remain accepted.

`config` acknowledgements include `revision`, `output_mode`, available named profiles, Xbox bindings and tuning. The phone clears held state on revision changes. Status exposes raw axes, effective digital directions, the desired Xbox report and separate virtual-device diagnostics. Desired reports are not proof of OS recognition.

Profiles now persist through the normal launcher; the selected profile itself resets to the safe default on startup. Host-admin routes add /api/profiles, /api/output, /api/output/arm, /api/pad-mapping, /api/tuning and /api/gamepad. Old /api/keyboard remains an arm/stop alias for the selected output.
