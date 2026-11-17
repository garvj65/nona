# Validation — NONA Android Bluetooth preview 0.6.1

Updated: 2026-11-17. Physical Wi-Fi results were reported on 2026-11-16.

## Android preview evidence

The native Android keyboard/mouse app now builds as an APK. [Android Actions run 44051171819](https://github.com/garvj65/nona/actions/runs/44051171819) passed 11 JVM tests, Android lint, debug/release compilation and an Android 35 emulator UI test. The UI test verifies the device-selection flow, Play/Stop, keyboard reports, background neutralization and paused resume. Its debug-only in-process link sends no Bluetooth or OS input. It cannot establish physical radio compatibility, Windows pairing success, game feel or real sensor latency.

The report/session tests cover descriptor lengths, report bounds, neutral startup, simultaneous input, consumed-once mouse deltas, GET_REPORT state without relative replay, short taps, pause/reconnect behavior and gyro math. The native app requests Bluetooth permissions but no internet/location permission; it requires a selected bonded host and a separate Play action. Callback ordering and permission/lifecycle cleanup were reviewed during implementation. This is not a completed independent security audit.

The redesigned Wi-Fi dashboard and phone controls passed the existing [NONA checks run 44051171867](https://github.com/garvj65/nona/actions/runs/44051171867), including Python/Node tests and Android-emulated Chromium. Dashboard screenshots were also captured at desktop and compact widths, with no horizontal overflow.

Follow [docs/ANDROID_BLUETOOTH.md](docs/ANDROID_BLUETOOTH.md) to install the test APK and record physical Bluetooth acceptance. The native racing profile currently uses keyboard steering; calibrated position-based racing tilt remains available in the existing Wi-Fi controller. Native gyro assistance applies to Move & look.

## 0.6.1 pre-flight changes (no new device evidence)

Made before the owner's first physical 0.6 test, to remove failure modes that would otherwise end that test early. None of these is a physical pass.

- **Bluetooth lifecycle.** AOSP `HidDeviceService` unregisters a HID app whose importance drops below visible. 0.6 also unregistered on every `onStop`, so a screen lock or an OEM full-screen pairing prompt dropped the Windows link. 0.6.1 keeps registration through a `connectedDevice` foreground service while input stays paused, with a ten-minute off-screen cutoff.
- **Reconnect.** 0.6 disconnected any Windows-initiated HID connection unless that computer was already selected in this app session, including the connection Windows opens right after pairing. 0.6.1 accepts it from the remembered computer, or from any bonded computer within 150 s of **Pair a new computer**, and reconnects the remembered computer after registration unless the user tapped Disconnect.
- **Movement.** Per-axis 0.22 thresholds turned forward into forward+strafe once the thumb drifted about 13°. Native and Wi-Fi keyboard movement now use equal 45° sectors with 7.5° hysteresis.
- **Native racing.** Arrow-key steering is pulse-width modulated by stick distance (togglable). The native tick moved from 50 Hz to 100 Hz.

Local checks for this change: 55 Python tests, 23 Node tests, 13 native JVM tests (2 new), and a Kotlin typecheck of main + debug/release sources against the API 35 platform jar. Gradle lint, APK assembly and the emulator UI test still need the Android Actions run.

## Device evidence

On 2026-11-16 the owner reported that physical phone tilt works in both NONA Sprint and JavaScript Racer with a Windows laptop and a Vivo phone using Chrome. The owner believes the phone runs Android 13; the exact model, Android version and Chrome version are not yet confirmed.

| Physical check | Owner-reported result |
|---|---|
| NONA Sprint tilt gameplay | Works |
| JavaScript Racer tilt gameplay through the keyboard bridge | Works |
| Controller RTT | Around 10–40 ms; this is the controller acknowledgement round trip, not measured end-to-end motion-to-display latency |
| Release / stop | Owner later reported it works in 0.4; new mouse/right-button path still needs a physical check |
| Screen lock and deliberate Wi-Fi interruption | Not checked; no interruption yet is not an interruption test |
| Reconnect, rotation and touch fallback | No complete physical result recorded yet |
| Roblox keyboard starter | Controls worked in an unnamed obby, but movement and camera felt restricted; no experience URL or baseline laptop frame-rate report supplied |
| New mobile movement/swipe look/gyro and optional Xbox-driver gameplay | No physical result yet |

These are owner-reported physical results, separate from automated tests. They establish working racing tilt and partial Roblox keyboard compatibility on this setup, not completion of every acceptance check or compatibility with other devices. SuperTuxKart and SuperTux do not run on this laptop and remain blocked targets. Smooth Roblox movement/camera, full lifecycle checks and the eventual packaged v1 remain acceptance gates.

## Existing Wi-Fi automated coverage

- **54 Python tests:** existing protocol/profile/output lifecycle and TLS coverage plus mouse ABI/relative moves, held right-button cleanup/retry, focused output, pointer validation/bounds, no replay, concurrent move/look/jump, profile compatibility and host-only camera settings. Real HTTPS/WSS tests validate certificates: an untrusted client is rejected; a client trusting the generated CA connects.
- **23 Node tests:** 9 racing simulation tests, 8 racing motion tests and 6 mobile-input tests covering floating touch origins, bounded radial input, gyro clutch, screen-space axes, invalid readings, deadband, frame gaps and staleness.

The native Xbox tests use mocked backends. The certificate tests create temporary CAs and do not change Windows or Android trust stores.

## Browser CI

`tests/browser_smoke.py` exercises actual Chromium with an Android-emulated viewport: touch racing, simulated orientation events through Enable tilt/Calibrate, steering plus Gas, sensor-loss release, permission denial, touch fallback, profiles, dual sticks and controller diagnostics. The 0.5 checks add floating movement + swipe look + jump through a fake desktop output backend, no relative-delta replay, simulated gyro clutch/loss/permission denial, and mobile layout geometry. It checks portrait/landscape overflow and saves screenshots for review. See the Actions run for the browser result; adding these assertions alone does not establish a pass.

These are generated sensor events, not readings from real Android hardware. Loopback is a browser secure context; physical phones browsing a laptop LAN IP use the documented trusted HTTPS setup. TLS certificate validation is tested independently over real HTTPS/WSS sockets. See Actions for the actual browser run result; test code alone is not proof of a pass.

## Remaining physical checks

Follow docs/MOTION_TEST.md and docs/MOBILE_CONTROLS.md to finish the new mouse/right-button release, screen-lock, disconnect/reconnect, rotation and touch-fallback checks. Record the exact phone/browser and laptop specifications. Complete docs/ROBLOX_TEST.md in a real experience and compare against laptop keyboard/mouse performance. The new swipe/gyro output needs physical acceptance independently of prior tilt gameplay.

The user requested refinement, validation, review, security checks and packaging after motion and Roblox succeed. Those gates are captured in docs/V1_PLAN.md. This iteration is not a completed security audit or a production v1 Android/Windows bundle. The later phone-as-DualSense PS5 bridge is not implemented here.
