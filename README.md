# NONA

**A game controller, already in your pocket.**

NONA turns an Android phone into a Wi-Fi controller for a Windows laptop. Open the controller in your phone browser, pair with a QR code, and play. The laptop runs the game; the phone supplies the controls.

Version **0.6 preview** adds a native Android **Bluetooth keyboard/mouse** app, with a simpler pairing screen and a dedicated play surface. The Windows controller desk and browser controls have a quieter, task-focused design. The existing Wi-Fi, racing, saved-profile and optional Xbox paths remain available.

**[Install and test the Android preview](docs/ANDROID_BLUETOOTH.md)** · [Android build artifacts](https://github.com/garvj65/nona/actions/workflows/android.yml) · [Wi-Fi mobile controls](docs/MOBILE_CONTROLS.md)

Direct Bluetooth uses Android/Windows Bluetooth pairing and does not require the PC NONA server, shared Wi-Fi or a CA certificate. This is a test APK, not a Play Store release. Physical Vivo/Windows compatibility remains a device acceptance test; generic/Xbox HID gamepad and native Wi-Fi QR pairing are not implemented by this Android preview.

## Current device results and next test

The owner confirmed physical tilt works in NONA Sprint and JavaScript Racer, with around 10–40 ms controller RTT, and that Release / stop works. Screen lock and deliberate Wi-Fi interruption remain untested. An unnamed Roblox obby accepted keyboard controls but felt restricted without camera input. Test the new **Roblox · Mobile movement + look** profile using [MOBILE_CONTROLS.md](docs/MOBILE_CONTROLS.md). SuperTuxKart and SuperTux do not run on this laptop. Read [MOTION_TEST.md](docs/MOTION_TEST.md), run PREPARE_MOTION_HTTPS.bat, complete its manual certificate-trust steps, then use START_MOTION_WINDOWS.bat. Choose Racing, Enable tilt, hold neutral and Calibrate. Gas/Brake remain touch controls.

[Alternative games](docs/NATIVE_GAMES.md) · [Roblox test gate](docs/ROBLOX_TEST.md) · [PC/Android v1 and later PS5 direction](docs/V1_PLAN.md)

This is a pre-v1 controls and Bluetooth prototype. Complete the movement/camera and lifecycle device checks before native-app acceptance, release security review and packaging. [Native app pairing](docs/APP_PAIRING.md) is planned to keep trust inside NONA rather than require a device-wide test CA. The PS5 controller bridge remains a separate later version.

## Start on Windows

1. Download this repository with **Code → Download ZIP**, then extract the entire folder. If you already run the earlier starter, close its terminal first so port 8765 is free.
2. Install [Python 3.10+](https://www.python.org/downloads/windows/) if needed, with **Add python.exe to PATH** selected.
3. Double-click **START_WINDOWS.bat**. First setup installs the Python dependencies; later launches reuse them.
4. The laptop dashboard opens at **http://localhost:8765**. Keep the terminal running.
5. Connect the phone and laptop to the same trusted Wi-Fi. If Windows Firewall asks, allow Python on your private network.
6. Scan the dashboard QR code and open the phone controller in Chrome. Choose **Racing · Arrows** on the phone.
7. On the laptop, click **Launch NONA Sprint**. Press **Start** on the phone, then hold **Gas** and drag the wheel with your other thumb.

The included games use direct network input: leave **desktop keyboard off** for these first tests. Turn the phone sideways for the wider controller layout.

| Phone control | NONA Sprint |
|---|---|
| Touch wheel | Proportional left/right steering; springs to centre on release |
| Gas / A | Accelerate |
| Brake / B | Brake; overrides acceleration |
| Handbrake | Stronger braking and tighter turning |
| Nitro | Temporary boost with a replenishing reserve |
| Start | Start / pause / resume |
| Select | Reset the run |

Follow the arrows counterclockwise, through the right, top, and left checkpoints before crossing the finish line. Grass slows you down. Best lap stays in the laptop browser. The violet car is a pacer with no collisions, not another connected player.

**Neon Run** is still available from the dashboard. Choose a Gamepad preset for its D-pad layout.

## Play an existing online browser game

NONA's companion can translate controller input into Windows keyboard events for the selected game window. This requires no modification to the game website.

A first external target is [Jake Gordon's JavaScript Racer](https://jakesgordon.com/games/racer/). Its published controls use the arrow keys; lower the in-game resolution and draw distance if needed. The project owner confirmed successful phone-controlled gameplay with the 0.2 release on their Windows + Android setup.

1. Open the external game on the laptop and read its controls.
2. Choose **Racing · Arrows** in NONA (or Racing · WASD for a game using WASD).
3. Use **Edit keys for your game** on the dashboard if the controls differ. Saving a mapping disables desktop keyboard until you enable it again.
4. Click **Enable keyboard**, then select the game window within **4 seconds**. Click its canvas if needed.
5. Hold Gas and steer using the phone. Use **Stop / release keys** before switching browser tabs or ending play.

Default racing mappings:

| Controller action | Racing · Arrows | Racing · WASD |
|---|---|---|
| Steering left/right | Left / Right | A / D |
| Gas | Up | W |
| Brake | Down | S |
| Handbrake | Space | Space |
| Nitro | Left Shift | Left Shift |
| Start | Enter | Enter |
| Select | R | R |

Handbrake, nitro, pause and reset only do something if the game uses those keys. Disable or change unused actions in the mapping editor. Match the game's key bindings before enabling input.

The touch wheel is proportional in our own racing demo. The keyboard bridge converts it to **digital left/right** using a dead zone and hysteresis; it is not analog Xbox-controller emulation.

To verify the bridge independently, select Racing · WASD, open Notepad, enable keyboard and select Notepad during the countdown. Tap Gas: it should type `w`. Stop keyboard mode afterward. Holding an injected key does not promise text auto-repeat.

An online-hosted game is different from online multiplayer. NONA changes your input device; the game controls multiplayer, cross-play, account access, hardware requirements, and whether it accepts generated input. See [the compatibility guide](docs/COMPATIBILITY.md).

## Adaptive controller

Choose a layout and output mode that match the game, customize its bindings, then save a named profile. Profiles persist across restarts and can be imported/exported as JSON. The app synchronizes the selected profile to the phone. It does not automatically read arbitrary games’ control settings.

For a native game accepting keyboard input, reuse the existing keyboard backend. For controller input, complete the optional Xbox setup and verify the device in the new Controller test page before playing. The optional backend uses retired ViGEmBus; see its setup guide for the dependency status and manual driver step. Normal setup installs no driver.

Dual-stick mode provides both analog sticks, A/B/X/Y, shoulder buttons and spring-return trigger sliders. Xbox bindings and stick tuning are editable. Switching profiles or outputs disarms both backends, and the phone now has a Release / stop action.

## What works today

- One paired phone with multi-touch gamepad and racing layouts; QR pairing and connection RTT.
- Proportional touch steering, gas, brake, handbrake and nitro.
- A lightweight Canvas racing time trial and the original Neon Run game.
- Windows keyboard/mouse injection, named presets, per-action key remapping, floating WASD movement and relative swipe camera.
- Optional gyro camera assistance while the right look surface is held, with bounded sensor deltas and a coalesced 50 Hz continuous-input loop.
- Shared protocol for future Android clients; old button-only starter packets remain accepted.
- Key release on normal disconnect, timeout, focus change, mapping changes and normal shutdown.

An Android Bluetooth keyboard/mouse test APK is built by the Android preview workflow. Native Bluetooth gamepad/XInput, game streaming, internet relay and multiple-controller multiplayer are not implemented. The new browser mouse/gyro path and native Bluetooth controls need physical Roblox acceptance. Xbox output is optional and requires its separate adapter/driver setup. These are separate milestones in [the roadmap](docs/ROADMAP.md).

## Project map

| File | Responsibility |
|---|---|
| `server.py` | Pairing, controller state, WebSockets, mapping and safety timeout |
| `windows_input.py` | Windows SendInput adapter and injected-key ownership |
| `virtual_gamepad.py` | Optional Xbox backend, normalized reports and neutralization |
| `controller_profiles.py` | Validated templates, saved profiles and atomic persistence |
| `web/controller.js` | Touch/motion UI, reconnect and profile synchronization |
| `web/motion.js` | Racing orientation mapping, calibration, dead zone and smoothing |
| `web/mobile-input.js` | Floating-stick math and bounded angular-velocity camera assistance |
| `local_tls.py` | Optional local HTTPS certificates, without installing trust |
| `web/dashboard.js` | Pairing, presets, mapping editor and keyboard arming |
| `web/race-physics.js` | Pure racing simulation, checkpoints, laps and boost |
| `web/race.js` | Canvas rendering and direct controller integration |
| `web/game.js` | Original Neon Run demo |
| `tests/` | Protocol, input lifecycle, physics and rendered browser smoke checks |

Plain HTML/CSS/JavaScript keeps the first setup small: no Node build, game engine, database or cloud account is required to play. Node is needed only for the optional JavaScript unit tests.

## Development and checks

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

For another port: `python run.py --port 8766`. Protocol and input lifecycle checks:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

With Node 22+ available: `node --test tests/race.test.cjs tests/motion.test.cjs tests/mobile.test.cjs`.

Optional rendered Android-emulation browser check:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tests/browser_smoke.py
```

GitHub Actions runs protocol/physics checks on Ubuntu and Windows and browser checks on Ubuntu. See [VALIDATION.md](VALIDATION.md) for what was actually checked and what still needs physical devices. CI browser tests emulate an Android viewport; they do not run Android hardware.

## Troubleshooting

- **Phone cannot connect:** same Wi-Fi, non-guest network, private-network firewall permission, and VPN off for initial testing. Use the QR address, not localhost, on the phone. Try another displayed LAN IP if needed.
- **Pairing unavailable:** close duplicate controller tabs and scan the current QR after a restart. The pairing token changes each server launch.
- **Another game ignores controls:** verify the bridge with Notepad, then check mapping and game focus. A game may reject injected input or require a real/virtual gamepad.
- **Keyboard turns off:** connection timeout, a changed application window, or an input error disables it. Re-enable after selecting the right game.
- **Wrong browser tab receives controls:** the bridge locks a window, not a tab. Stop input before switching tabs in that window.
- **Phone locks or switches apps:** reopen/reconnect and re-enable desktop keyboard if needed. Wake lock and fullscreen are best-effort browser features.
- **Port busy:** stop the earlier starter or choose another port. Close the terminal with Ctrl+C after releasing controls.

Keep the helper on a trusted private network. Local HTTP/WS is unencrypted; do not expose the port to the internet. Abrupt process termination or Windows rejecting a release cannot guarantee key cleanup, so release controls before killing the process.

The project owner has confirmed NONA Sprint and the external JavaScript Racer on Windows + Android. Native-game and optional Xbox-driver tests remain separate acceptance checks; successful web racing does not establish those automatically.
