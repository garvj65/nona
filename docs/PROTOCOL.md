# Wi-Fi controller protocol

The protocol between the phone controller and the Windows companion (`server.py`). The Bluetooth app doesn't use it: it sends standard HID reports, described in [ARCHITECTURE.md](ARCHITECTURE.md#android-app-kotlin-api-28-no-third-party-dependencies).

**Design rule:** every controller message is a **complete snapshot** of the phone's state. Nothing is incremental except camera deltas, which are applied once and never replayed.

## Connection

```
GET  /controller#<token>                       phone page; the token stays in the URL fragment
WS   /ws/controller?token=<token>              controller socket
```

| Rule | Behaviour |
|---|---|
| Token | Random for each launch, compared in constant time. A restart invalidates old QR codes. |
| Origin | Must match the host. Cross-origin sockets are closed. |
| Ownership | **One controller at a time.** A second connection is refused while the first holds the slot. |
| Rejection | Any rule failure closes the socket with code **1008**. |

## Controller → companion

```json
{
  "seq": 42,
  "buttons": ["a", "nitro"],
  "steering": -0.45,
  "axes": {"lx": 0.5, "ly": -0.2, "rx": 0, "ry": 0, "lt": 0, "rt": 0.6},
  "pointer": {"dx": 12.5, "dy": -3, "active": true},
  "profile": "racing_arrows",
  "disarm": false
}
```

| Field | Type | Required | Rules |
|---|---|---|---|
| `seq` | integer | yes | Strictly increasing for each connection; resets on reconnect |
| `buttons` | string[] | yes | No duplicates, drawn from the 16 actions below |
| `steering` | number | no | Finite, -1 to 1. Default 0. |
| `axes` | object | no | Keys `lx ly rx ry lt rt`. Sticks run -1 to 1 with **Y positive downward**. Triggers run 0 to 1. Missing axes are 0. |
| `pointer` | object | no | `dx`, `dy` finite with an absolute value of 96 or less (camera deltas, applied once). `active` is a boolean: true while the look area is being touched. |
| `profile` | string | no | A known profile key. Changing it releases all input and disarms output. |
| `disarm` | boolean | no | Phone emergency stop: release all and disarm |

**Actions:** `up down left right a b x y lb rb lt rt start select handbrake nitro`

**Backward compatibility:** older packets with only `seq`, `buttons` and `steering` are still accepted. New fields are optional and default to neutral.

## Companion → controller

Each valid packet gets an acknowledgement with the authoritative configuration:

```json
{"type": "ack", "seq": 42, "profile": "racing_arrows", "layout": "racing", "revision": 7,
 "mapping": {"a": "up", "b": "down", "...": "..."}, "pad_mapping": {"...": "..."},
 "tuning": {"deadzone": 0.12, "sensitivity": 1.0, "invert_y": false},
 "look": {"enabled": false, "sensitivity": 1.0, "hold_right": true},
 "output_mode": "keyboard", "profiles": [/* catalogue */], "armed": false}
```

When `revision` changes, the phone clears its held state. The round-trip time it shows comes from acknowledgements; it isn't the full delay from input to what's on screen.

## Timing and limits

| Parameter | Value |
|---|---|
| Continuous input send rate (phone) | Up to 50 Hz, coalesced. Button edges are sent immediately. |
| Heartbeat (phone) | Every 100 ms |
| Watchdog check (companion) | Every 25 ms |
| Silence timeout | **800 ms** → release all, disarm |
| Maximum message size | 1024 bytes |
| Maximum message rate | 120 per second |

## Derived output

| Profile layout | Keyboard output | Xbox output |
|---|---|---|
| Racing | Steering → left/right: press past 0.22, release below 0.12 | Steering → left stick X; Gas and Brake → triggers |
| Gamepad / Dual stick | Left stick → 8-way directions (45° sectors, 7.5° hysteresis) | Sticks with dead zone and sensitivity; Y flipped to XInput convention |
| Move & look | `pointer` → relative mouse movement; right button held while `active` (if `hold_right`) | — |

When several actions map to one key, the key is released only after **all** of them are released.

## Laptop dashboard API

Read routes (`GET`) and `/ws/monitor` accept **loopback connections only**. Write routes (`POST`) also need the same origin and the per-launch admin nonce in `X-PocketPad-Admin` (the name is kept from an earlier version for compatibility). `/motion-ca.crt` is deliberately public: it's the public certificate the phone downloads.

| Route | Purpose |
|---|---|
| `GET /api/session` · `GET /api/qr` | Pairing details and QR image |
| `POST /api/output/arm` · `POST /api/keyboard` | Arm or stop output (`/api/keyboard` is the older alias) |
| `POST /api/output` | Choose `keyboard` or `gamepad` |
| `POST /api/profile` · `GET /api/current-profile` | Select or read the active profile |
| `GET /api/profiles/{key}` · `POST /api/profiles` | Read or save a profile, and import |
| `POST /api/mapping` · `POST /api/pad-mapping` | Keyboard and Xbox bindings |
| `POST /api/tuning` · `POST /api/look` | Stick tuning and camera settings |
| `POST /api/gamepad` | Connect or disconnect the virtual Xbox device |
| `WS /ws/monitor` | A `status` stream for the dashboard: connection, held buttons, axes, `look_active`, the configuration above and diagnostics |
| `GET /motion-ca.crt` | Public local CA, for tilt setup (404 until `PREPARE_MOTION_HTTPS.bat` has run) |

Every change to profile, bindings, tuning or output releases owned input and disarms output.

## Transport security

Plain HTTP and WebSocket on a trusted local network, or HTTPS and WSS with the [local CA](MOTION_TEST.md). It isn't designed to be exposed to the internet. See [SECURITY.md](../SECURITY.md).
