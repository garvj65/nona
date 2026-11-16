# NONA

**A game controller, already in your pocket.**

NONA turns an Android phone into a Wi-Fi controller for a Windows laptop. Open the controller in your phone browser, pair with a QR code, and play. The laptop runs the game; the phone supplies the controls.

Version **0.2** adds a touchscreen steering wheel, racing pedals, a local time-trial game, and editable keyboard mappings for games hosted on other websites. The original PocketPad / Neon Run starter is preserved.

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

A first external target is [Jake Gordon's JavaScript Racer](https://jakesgordon.com/games/racer/). Its published controls use the arrow keys; lower the in-game resolution and draw distance if needed. This is a source-matched compatibility target, not a claim of physical-device verification for this release.

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

## What works today

- One paired phone with multi-touch gamepad and racing layouts; QR pairing and connection RTT.
- Proportional touch steering, gas, brake, handbrake and nitro.
- A lightweight Canvas racing time trial and the original Neon Run game.
- Windows keyboard injection, four presets, and per-action key remapping.
- Shared protocol for future Android clients; old button-only starter packets remain accepted.
- Key release on normal disconnect, timeout, focus change, mapping changes and normal shutdown.

There is no motion-sensor steering, Android APK, Bluetooth HID, virtual Xbox controller, game streaming, internet relay, or multiple-controller multiplayer in this version. These are separate milestones in [the roadmap](docs/ROADMAP.md).

## Project map

| File | Responsibility |
|---|---|
| `server.py` | Pairing, controller state, WebSockets, mapping and safety timeout |
| `windows_input.py` | Windows SendInput adapter and injected-key ownership |
| `web/controller.js` | Multi-touch buttons, wheel, reconnect and profile synchronization |
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

With Node 22+ available: `node --test tests/race.test.cjs`.

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

NONA grew from a working Windows + Android prototype. The original user's successful connection/gameplay report is the starting point; racing and third-party games need their own device tests.
