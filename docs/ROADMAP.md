# NONA roadmap

## 0.3: adaptive profiles and optional Xbox output

Implemented: persistent named profiles, import/export, dual sticks and trigger sliders, keyboard/Xbox output selection, optional vgamepad backend, tuning, OS-controller diagnostics and an emergency stop. Complete GAMEPAD_SETUP.md and the native-game acceptance checks before marking physical gamepad gameplay verified.

## 0.2: racing first

Included: a touch wheel, independent pedals, handbrake/nitro, presets, editable mappings, NONA Sprint, and a documented external web-racer target.

Acceptance: play a lap with two simultaneous touches; release the wheel and pedals; recover from disconnect; verify the Windows bridge in Notepad; drive the external racer and record the result.

## Next: motion steering

Serve the controller through trusted HTTPS with WSS, or add a native client. Add a user-triggered sensor-permission action, orientation detection, a neutral-position calibration, dead zone, smoothing and sensitivity. Handle device rotation and sensor loss. Never depend on disabling browser security. Sensor support varies by browser and device.

Acceptance: steering follows tilt on the real Android phone, recalibrates, centres safely on sensor loss, and still releases on disconnect.

## Continue: native games and backend maintenance

The 0.3 backend separates normalized controls from keyboard and optional Xbox output. The current Xbox route depends on retired ViGEmBus; evaluate maintained alternatives as they become practical. Add an actual compatibility matrix from games tested on the user's laptop. Investigate macOS/Linux backends separately.

Acceptance: one supported native game recognizes the virtual device, holds proportional inputs correctly, and releases/reconnects reliably. Do not label keyboard injection as gamepad emulation.

## Android app

Keep the existing host protocol and build a Kotlin or React Native client around it. Add QR pairing, trusted transport, native sensors, tactile feedback, saved layouts and background lifecycle handling. A simple WebView wrapper does not solve analog-device emulation on Windows.

Acceptance: install an APK on a real Android device and complete the same pairing, input, disconnect and racing checks without regressing the browser controller.

## Wider product

After one phone/one host is reliable: support multiple controllers with separate ownership, game-specific layouts, optional relay/WebRTC transport based on measured latency, accessibility settings, and a packaged Windows companion that does not require Python setup. Internet play, streaming and multiplayer are independent scopes.
