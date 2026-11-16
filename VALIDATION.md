# Validation — NONA motion prototype 0.4

Recorded: 2026-11-16.

## Device evidence

On 2026-11-16 the owner reported that physical phone tilt works in both NONA Sprint and JavaScript Racer with a Windows laptop and a Vivo phone using Chrome. The owner believes the phone runs Android 13; the exact model, Android version and Chrome version are not yet confirmed.

| Physical check | Owner-reported result |
|---|---|
| NONA Sprint tilt gameplay | Works |
| JavaScript Racer tilt gameplay through the keyboard bridge | Works |
| Controller RTT | Around 10–40 ms; this is the controller acknowledgement round trip, not measured end-to-end motion-to-display latency |
| Release / stop and screen lock | Not checked |
| Wi-Fi interruption, reconnect, rotation and touch fallback | No physical result recorded yet |
| Roblox and optional Xbox-driver gameplay | Not tested yet |

These are owner-reported physical results, separate from automated tests. They establish working tilt gameplay on this setup, not completion of every motion acceptance check or compatibility with other devices. SuperTuxKart and SuperTux do not run on this laptop and remain blocked targets. Roblox, full lifecycle checks and the eventual packaged v1 remain acceptance gates.

## Passed locally

- **41 Python tests:** existing protocol/profile/output lifecycle coverage plus local certificate reuse and SANs, public-cert-only serving, preservation of incomplete trust material, and real HTTPS/WSS pairing using certificate verification. An untrusted client is rejected; a client trusting the generated CA connects.
- **17 Node tests:** 9 racing simulation tests plus 8 motion tests for portrait/landscape coordinate mapping, flat/invalid readings, explicit calibration, neutral dead zone, angle limits, time-based smoothing, inversion, screen rotation, staleness and angular wraparound.

The native Xbox tests use mocked backends. The certificate tests create temporary CAs and do not change Windows or Android trust stores.

## Browser CI

`tests/browser_smoke.py` exercises actual Chromium with an Android-emulated viewport: touch racing, simulated orientation events through Enable tilt/Calibrate, steering plus Gas, sensor-loss release, permission denial, touch fallback, profiles, dual sticks and controller diagnostics. It checks portrait/landscape overflow and saves screenshots for review.

These are generated sensor events, not readings from real Android hardware. Loopback is a browser secure context; physical phones browsing a laptop LAN IP use the documented trusted HTTPS setup. TLS certificate validation is tested independently over real HTTPS/WSS sockets. See Actions for the actual browser run result; test code alone is not proof of a pass.

## Remaining physical checks

Follow docs/MOTION_TEST.md to finish the release, screen-lock, disconnect/reconnect, rotation and touch-fallback checks. Record any remaining details about calibration, steering direction and neutral response, along with the exact phone/browser and laptop specifications. Then complete docs/ROBLOX_TEST.md in a real experience; begin with ordinary movement/jump controls before testing motion in a vehicle.

The user requested refinement, validation, review, security checks and packaging after motion and Roblox succeed. Those gates are captured in docs/V1_PLAN.md. This iteration is not a completed security audit or a v1 APK/Windows bundle. The later phone-as-DualSense PS5 bridge is not implemented here.
