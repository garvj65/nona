# Validation — NONA 0.2

Recorded: 2026-11-16.

## Passed locally

- **23 Python unittest cases:** original pairing/origin/exclusivity/disconnect regressions, input lifecycle and mocked Windows ABI; racing pedal aliases; wheel hysteresis and centring; legacy button-only packets; controller-driven preset changes; editable mapping validation and preset restoration; malformed, non-finite and out-of-range axes; race routes/assets.
- **9 Node simulation tests:** stopped/paused behavior, acceleration and brake priority, finite nitro/recharge, proportional steering, grass slowdown, ordered checkpoints, finish-line rejection without checkpoints, bounded frame steps, reset state.

The Windows INPUT layout/scan-code tests use a mocked API. They are not physical Windows gameplay tests.

## Rendered browser checks

`tests/browser_smoke.py` starts a real local server and tests dashboard/QR rendering, Android-emulated profile synchronization, simultaneous wheel + gas touches, vehicle response, centring/release, short pause/resume taps, portrait/landscape overflow, mapping persistence within the running session, and disconnect pause. GitHub Actions runs it on Ubuntu Chromium. Check the repository's Actions tab for the actual run result; adding the test itself is not evidence it passed.

Local browser execution in the build environment is unavailable because its Chromium Unix socket setup is restricted. The JavaScript simulation tests do not replace a rendering check.

## User evidence and remaining device checks

The user reported successful pairing and gameplay for the earlier Windows + Android starter on 2026-11-16. This confirms that baseline path on those devices, not the new racing layout or the Windows keyboard bridge to third-party games.

Before marking the new racing feature physically verified:

1. Launch NONA 0.2 and pair the real Android phone.
2. Choose Racing and hold Gas while moving the wheel. Test both portrait and landscape.
3. Complete one NONA Sprint lap, test Brake / Handbrake / Nitro, and verify Start / Select.
4. Release the wheel and pedals; confirm neutral input. Lock/reconnect the phone and confirm pause plus keyboard disarm.
5. Verify the keyboard bridge in Notepad using Racing · WASD and Gas → w.
6. Play Jake Gordon's JavaScript Racer with Racing · Arrows, and record the result, laptop specifications and performance settings.
7. Test another keyboard-controlled title only after those pass. Do not infer gamepad-only, native-game or cross-play support from one successful browser game.

No physical motion sensors, virtual gamepad driver, Android APK, game streaming, multiple-player sessions or third-party multiplayer integration are implemented or claimed in 0.2.
