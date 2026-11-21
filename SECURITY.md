# Security policy

NONA is input software: whatever controls it can press keys on your PC. This page explains what NONA trusts, what it defends against, its known limits, and how to report a problem.

## Supported versions

NONA is a pre-1.0 preview. Only the latest commit on `main` and the most recent green [Android preview](https://github.com/garvj65/nona/actions/workflows/android.yml) build get fixes.

## Reporting a vulnerability

Report privately: in this repository open **Security → Report a vulnerability**. Please don't open a public issue for a security problem.

Include the version or commit, which path is affected (Wi-Fi companion, Bluetooth app or optional Xbox output), the steps to reproduce, and the impact. You'll get an acknowledgement within 7 days. Fixes ship as a new commit and a changelog entry, with credit unless you'd rather stay anonymous.

## Threat model

### Wi-Fi companion (`server.py`)

| Boundary | Control |
|---|---|
| Who can control the PC | Only the holder of the pairing token. It's random, rotates on every launch and is shown only in the laptop QR code. One controller owns a session at a time. |
| Who can change settings | Dashboard routes accept **loopback connections only**. Write routes also need the same origin and a per-launch admin nonce. Phones can't arm output. |
| Where input goes | Output is off at launch. It must be armed on the laptop, follows the one window that had focus during the 4-second countdown, and stops if that window loses focus. |
| Browser hardening | Every response is sent with a strict Content-Security-Policy (`default-src 'self'`, no inline script, `frame-ancestors 'none'`), `nosniff`, `no-referrer` and `no-store`. The companion also checks the Host header against a list of trusted hosts. |
| Malformed input | Every packet is checked against a schema: strictly increasing sequence numbers, known actions only, finite axes in range, camera deltas of 96 or less. Messages are capped at 1 KB and 120 per second. A bad packet closes the connection. |
| Stuck input | An 800 ms watchdog releases every key, mouse button and axis. Disconnects, focus loss, profile changes and Stop do the same. NONA tracks which keys it owns and retries failed releases. Re-arming is blocked until cleanup succeeds. |
| Imported profiles | Plain data checked against fixed sets of actions, keys and pad targets. A profile can't run commands. |

### Bluetooth app (`android/`)

| Boundary | Control |
|---|---|
| Who receives input | Only a **bonded** computer you chose, or one that connects within 150 seconds of **Pair a new computer**. Connections from any other device are dropped. |
| Permissions | Bluetooth connect and advertise (legacy Bluetooth permissions only up to Android 11), foreground service and notifications. **No internet or location permission.** |
| Stuck input | Input starts neutral and paused. Stop, leaving the screen, losing the connection or changing the profile sends empty reports. Nothing held earlier is replayed. |
| Test builds | The emulator's preview link exists only in the debug source set. Release builds contain only the real Bluetooth link. |

### Optional components

- **Local HTTPS for tilt** (`local_tls.py`): generates a local CA and a server certificate under `%LOCALAPPDATA%\NONA\tls`. NONA never installs trust itself. Private keys stay on the laptop; only the public CA can be downloaded.
- **Virtual Xbox output**: depends on **ViGEmBus 1.22.0**, which is retired upstream. NONA never installs it; you install it yourself after reviewing it. See [GAMEPAD_SETUP.md](docs/GAMEPAD_SETUP.md).

## Known limits

These are deliberate preview trade-offs, listed so nobody mistakes them for guarantees:

1. **The browser path is plain HTTP and WebSocket** on your local network unless you set up local HTTPS. Use it only on a trusted private network. Never forward the port to the internet.
2. **The pairing token is a shared secret for the launch.** Anyone who sees the QR code before you connect can take the controller slot. Per-device pairing is designed in [APP_PAIRING.md](docs/APP_PAIRING.md) but not built yet.
3. **Bluetooth input has no window guard.** The PC treats the phone like a physical keyboard, so input goes to whatever window has focus. Tap Stop before switching apps.
4. **Cleanup after an abrupt failure can't be guaranteed.** If the companion process is killed, or the phone dies mid-press, release depends on Windows. NONA releases on every path it controls.
5. **Debug-signed APKs.** CI builds use a throwaway signing key. A Play Store release needs managed signing.
6. **No independent security audit has been done yet.** One is a gate before v1 ([roadmap](docs/ROADMAP.md)).
