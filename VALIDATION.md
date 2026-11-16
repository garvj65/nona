# Validation — NONA 0.3

Recorded: 2026-11-16.

## Physical user reports

The project owner confirmed that NONA Sprint and the external JavaScript Racer both work with the Windows laptop and Android phone. This verifies those 0.2 paths on their devices. Native-game and optional Xbox-device gameplay are separate checks.

## Passed locally

- **38 Python tests:** existing input/pairing/racing regressions, saved-profile persistence and atomic write failure, invalid/corrupt import handling, Xbox report mapping, axis tuning/Y conversion, output switching, focus/disconnect/timeout neutralization, and phone emergency stop.
- **9 Node racing simulation tests:** acceleration, brake priority, nitro, proportional steering, grass slowdown, ordered lap checkpoints and bounded frame steps.

Gamepad mapping/lifecycle tests use fake backends and a mocked vgamepad module. They do not establish that a real Windows virtual controller is installed or accepted by a game.

## Browser and CI checks

The repository workflow runs Python/physics tests on Windows and Ubuntu. The Windows job also checks that the optional Python adapter can be installed with its bundled driver hook explicitly skipped. It does not install ViGEmBus or run a game.

`tests/browser_smoke.py` runs actual Chromium with an Android-emulated viewport and touch input. It exercises the existing race, two-touch steering/gas, saved-profile synchronization, dual analog sticks, mapping changes, diagnostics, portrait/landscape overflow and disconnect pause. See the latest Actions run for the actual result; test code being present is not proof of a passed run. Test screenshots are retained as CI artifacts for review.

This local execution environment cannot launch Chromium because of its Unix socket restriction, so rendered checks run through GitHub Actions. Android emulation does not replace physical Android testing.

## Remaining acceptance checks for 0.3

1. Update NONA, pair the real phone, and confirm existing keyboard/browser racing still works.
2. Save a custom profile, restart NONA, load it and confirm its layout, bindings, output and tuning persist.
3. Try a native game using keyboard mode; SuperTuxKart and SuperTux are documented candidates, not verified results.
4. If choosing the optional legacy Xbox backend, complete GAMEPAD_SETUP.md yourself. Verify the virtual controller in the tester's browser-detected gamepad section or joy.cpl.
5. Verify analog steering/sticks, each trigger/button, focus changes, emergency stop, disconnect and reconnect against a real game. Record title/version, laptop specifications and settings before marking that game verified.

Automatic game-control detection, mouse-only output, motion sensors, an Android APK, internet relay, game streaming and multiple-controller multiplayer are not implemented in 0.3.
