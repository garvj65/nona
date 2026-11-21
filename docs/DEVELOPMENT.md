# Development

## Prerequisites

| For | Need |
|---|---|
| Companion | Python 3.10+ (CI uses 3.12). Windows to inject real input; the server and demos run anywhere. |
| JavaScript unit tests | Node 22+ |
| Browser smoke test | Playwright with Chromium |
| Android app | JDK 17 and Android SDK 35. Android Studio is optional; the Gradle 8.11.1 wrapper is checked in and pinned by SHA-256. |

## Run the companion from source

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py                 # http://localhost:8765
.\.venv\Scripts\python.exe run.py --port 8766     # another port
```

| Flag | Purpose |
|---|---|
| `--port N` | Listen port (default 8765) |
| `--profiles-file PATH` | Use a different saved-profile file (default `%LOCALAPPDATA%\NONA\profiles.json`) |
| `--no-browser` | Don't open the dashboard automatically |
| `--https` | Serve HTTPS with the certificates made by `PREPARE_MOTION_HTTPS.bat` (needed for tilt in the browser) |
| `--certfile PATH --keyfile PATH` | Serve HTTPS with your own certificate, which needs the LAN address in its SAN |

`START_WINDOWS.bat` does the same thing for end users. It creates `.venv`, installs once, then launches.

## Test suites

| Suite | Command | Covers |
|---|---|---|
| Python | `python -m unittest discover -s tests -v` | Protocol validation, pairing and origin rules, watchdog, key ownership, mouse lifecycle, profiles and import, Xbox reports (mocked), real HTTPS/WSS certificate checks |
| Node | `node --test tests/race.test.cjs tests/motion.test.cjs tests/mobile.test.cjs` | Racing physics, tilt maths, floating stick and gyro assist |
| Browser | `python tests/browser_smoke.py` | Real Chromium in an Android viewport: touch racing, simulated tilt, move + look + jump, Stop, profile sync, layout geometry and overflow. Saves screenshots to `artifacts/`. |
| Android unit | `cd android && .\gradlew.bat testDebugUnitTest` | HID descriptor and report bounds, input session, 8-way sectors, pulsed steering, gyro maths |
| Android lint | `.\gradlew.bat lintDebug` | Lint must pass; any error fails the build (`abortOnError`) |
| Android UI | `.\gradlew.bat connectedDebugAndroidTest` (emulator) | Pairing screen, Play/Stop, reports, background neutralization, paused resume (uses the debug-only preview link) |

Setup for the browser suite:

```powershell
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
```

Build a test APK with `cd android && .\gradlew.bat assembleDebug`. The output is `android/app/build/outputs/apk/debug/app-debug.apk`.

## Continuous integration

| Workflow | Runs on | Jobs |
|---|---|---|
| [NONA checks](https://github.com/garvj65/nona/actions/workflows/ci.yml) | every push and pull request | Python + Node on Ubuntu **and** Windows (including an install of the optional Xbox adapter with the driver hook disabled); browser smoke on Ubuntu |
| [Android preview](https://github.com/garvj65/nona/actions/workflows/android.yml) | every push and pull request, plus manual runs | `build`: unit tests, lint, debug and release APKs. `native-ui`: emulator UI and lifecycle test. |

Artifacts: `nona-android-preview` (the installable APK, kept for 30 days), `nona-android-instrumentation`, `android-check-reports`, `android-ui-checks` (emulator screenshots and log) and `browser-test-screenshots`.

## Working rules

- **Never leave input held.** Every new input path needs a release path for Stop, timeout, focus loss, disconnect and profile change, and a test that proves it.
- **Keep CI evidence and device evidence apart.** CI can't prove a phone's Bluetooth stack, sensor feel or a game accepting input. Record physical results in [VALIDATION.md](../VALIDATION.md), with the device, OS and build.
- **Keep the protocol backward compatible.** New packet fields are optional and default to neutral. Older packets with only buttons and steering are still accepted. Update [PROTOCOL.md](PROTOCOL.md).
- **No secrets in the repo.** Signing keys, `.pem` files and local CAs are gitignored and must stay that way.
- **Android main-thread timing.** Don't schedule a repeating main-looper message faster than about 15 ms. It keeps Espresso from ever seeing the UI idle, so the emulator test hangs.
- **Changelog.** Add an entry under the next version in [CHANGELOG.md](../CHANGELOG.md).
- **Licensing.** NONA is [Apache-2.0](../LICENSE). Contributions are accepted under the same license. New dependencies must use a license compatible with Apache-2.0 (MIT, BSD and Apache are fine; GPL is not).
