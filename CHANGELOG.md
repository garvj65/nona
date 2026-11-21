# Changelog

All notable changes to NONA. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions are pre-1.0 previews; a minor version may change behaviour.

Each release states what it **verified on a device** separately from what passed **CI**. See [VALIDATION.md](VALIDATION.md) for evidence.

## [0.6.1-preview] — 2026-11-17

### Added
- **Proportional racing steering (Bluetooth app).** The arrow key is pulsed over a 120 ms cycle, and its key-down time grows with stick distance. Full lock holds the key. You can turn it off in **Controls** for games that act once per key press.
- **The Bluetooth connection survives a screen lock and app switching.** A `connectedDevice` foreground service keeps Android's Bluetooth keyboard registration alive while NONA is off-screen. Input still pauses immediately. After ten idle minutes off-screen, NONA releases the computer.
- **Automatic reconnect.** NONA accepts the connection Windows opens right after pairing, and connections from the last chosen computer. On launch it reconnects to that computer unless you last tapped **Disconnect**.

### Changed
- **8-way movement**, in the Bluetooth app and on the Wi-Fi server. Equal 45° sectors with 7.5° hysteresis replace per-axis thresholds. Before, about 13° of thumb drift turned forward into forward + strafe.
- **One visual system** across the phone controller, laptop dashboard and Android app: graphite surfaces, with colour used only for state. Orange means pressed; green, amber and red show link and output state.
  - The phone's **Stop**, **Reconnect** and **Fullscreen** moved to a top bar away from the thumbs.
  - Face buttons use the standard diamond, and unmapped buttons are dimmed.
  - Racing pedals are bottom-aligned under the right thumb.
- The dashboard header shows live phone and output state. Its key chips light up while the phone presses them.
- The Android app uses a dark Material theme. Its pairing screen lists paired devices as rows that show their connection state.

### Fixed
- Racing in the Bluetooth app no longer draws a mislabelled "PEDALS" area.
- Hidden setup strips no longer shrink the phone's play area.
- `SensorManager` access is null-safe.

### Verified
- **CI:** 55 Python, 23 Node, 18 rendered-browser, 13 Android unit tests. Android lint, debug and release builds, and the emulator UI test pass ([run 44142182103](https://github.com/garvj65/nona/actions/runs/44142182103)).
- **On a device:** none yet. The first Bluetooth hardware test is pending.

## [0.6.0-preview] — 2026-11-17

### Added
- **Native Android Bluetooth keyboard + mouse app** (Kotlin, API 28+). It needs no PC software, shared Wi-Fi or certificate.
  - **Move & look** and **Racing** profiles.
  - Gyro aim assist.
  - An explicit **Play**/**Stop** session.
  - A debug-only preview link for emulator tests, with no radio or OS input.
- Android CI: unit tests, lint, debug and release APKs, and an emulator UI and lifecycle test. The Gradle wrapper is SHA-256 pinned.
- Design record comparing direct Bluetooth HID with a Wi-Fi companion ([BLUETOOTH_AND_DEPLOYMENT.md](docs/BLUETOOTH_AND_DEPLOYMENT.md)).

### Changed
- Redesigned the laptop dashboard as a task-focused desk.
- Revoked Bluetooth permission and screen-on during play are handled explicitly.

## [0.5.0] — 2026-11-16

### Added
- **Move & look controls**: a floating WASD stick, a relative swipe camera (holds the right mouse button for third-person cameras), and optional gyro aim that works only while touching the look area.
- **Roblox · Mobile movement + look** and **Mouse look · First person** profiles.
- Continuous input is coalesced into a 50 Hz loop, and button edges are sent immediately.
- Camera deltas are bounded and consumed once.

### Fixed
- **Stop** stays visible in short landscape layouts.

## [0.4.0] — 2026-11-16

### Added
- **Tilt steering** with neutral calibration, orientation awareness, 20/30/45° range, invert, and release on sensor loss.
- An optional **trusted local HTTPS** setup (`PREPARE_MOTION_HTTPS.bat`, `START_MOTION_WINDOWS.bat`). It never changes trust settings itself.
- Roblox starter profiles and alternative native-game candidates.

### Verified
- **On a device:** tilt racing in NONA Sprint and JavaScript Racer on a Vivo phone with a Windows laptop. Stop / release works.

## [0.3.0] — 2026-11-16

### Added
- **Saved game profiles** stored in `%LOCALAPPDATA%\NONA\profiles.json`, with atomic writes and JSON import/export.
- **Dual-stick layout** with trigger sliders.
- **Optional virtual Xbox 360 output** through `vgamepad` and ViGEmBus, with dead zone, sensitivity and Y-invert tuning.
- A controller diagnostics page and a phone emergency stop.

## [0.2.0] — 2026-11-16

### Added
- **Racing controls**: proportional touch wheel, independent Gas and Brake, handbrake and nitro.
- **NONA Sprint**, a lap-timed canvas racer.
- A Windows keyboard bridge with per-action remapping, focus locking and a 4-second arming countdown.

### Verified
- **On a device:** JavaScript Racer played from the phone through the keyboard bridge.

## [0.1.0] — 2026-11-16

### Added
- First release: QR pairing, a WebSocket controller, the Neon Run demo, and release on disconnect.

[0.6.1-preview]: https://github.com/garvj65/nona/compare/4008022...f481311
