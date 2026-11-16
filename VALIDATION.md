# Validation — NONA motion prototype 0.4

Recorded: 2026-11-16.

## Device evidence

The owner confirmed NONA Sprint and JavaScript Racer work with Windows + Android. SuperTuxKart and SuperTux do not run on this laptop, so they are blocked targets. Physical tilt, Roblox gameplay, optional Xbox-driver gameplay and the eventual packaged v1 remain separate acceptance gates.

## Passed locally

- **41 Python tests:** existing protocol/profile/output lifecycle coverage plus local certificate reuse and SANs, public-cert-only serving, preservation of incomplete trust material, and real HTTPS/WSS pairing using certificate verification. An untrusted client is rejected; a client trusting the generated CA connects.
- **17 Node tests:** 9 racing simulation tests plus 8 motion tests for portrait/landscape coordinate mapping, flat/invalid readings, explicit calibration, neutral dead zone, angle limits, time-based smoothing, inversion, screen rotation, staleness and angular wraparound.

The native Xbox tests use mocked backends. The certificate tests create temporary CAs and do not change Windows or Android trust stores.

## Browser CI

`tests/browser_smoke.py` exercises actual Chromium with an Android-emulated viewport: touch racing, simulated orientation events through Enable tilt/Calibrate, steering plus Gas, sensor-loss release, permission denial, touch fallback, profiles, dual sticks and controller diagnostics. It checks portrait/landscape overflow and saves screenshots for review.

These are generated sensor events, not readings from real Android hardware. Loopback is a browser secure context; physical phones browsing a laptop LAN IP use the documented trusted HTTPS setup. TLS certificate validation is tested independently over real HTTPS/WSS sockets. See Actions for the actual browser run result; test code alone is not proof of a pass.

## Required physical test now

Follow docs/MOTION_TEST.md. Confirm sensor access, stable calibration, correct direction (or Invert), neutral response, a playable lap, touch fallback, rotation, screen lock and disconnect behavior. Record phone/browser and laptop details. Then complete docs/ROBLOX_TEST.md in a real experience.

The user requested refinement, validation, review, security checks and packaging after motion and Roblox succeed. Those gates are captured in docs/V1_PLAN.md. This iteration is not a completed security audit or a v1 APK/Windows bundle. The later phone-as-DualSense PS5 bridge is not implemented here.
