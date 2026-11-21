# Validation record

This file is the record of what has been **proven**, how, and on what. It's kept separate from the feature list on purpose: a passing test suite is not a passing phone.

**Evidence levels**

| Level | Meaning |
|---|---|
| **Device** | Run by a person on real hardware, with the device and build recorded |
| **CI** | Automated in GitHub Actions; the run is linked |
| **Not run** | Implemented, with no evidence yet |

**Test hardware**

| | |
|---|---|
| Phone | vivo Y33T (model V2146), Android 13, Chrome |
| PC | Windows laptop; exact specs not recorded yet |

---

## Current build: 0.6.1-preview (`f481311`)

| Check | Result | Evidence |
|---|---|---|
| Python suite (protocol, output lifecycle, profiles, TLS) | 55 passed | [NONA checks 44142182027](https://github.com/garvj65/nona/actions/runs/44142182027), Ubuntu + Windows |
| Node suite (racing physics, tilt, mobile input) | 23 passed | same run |
| Rendered browser smoke (Android viewport) | 18 checks passed, no page errors | same run |
| Android unit (HID reports, input session, 8-way, pulsed steering, gyro) | 13 passed | [Android preview 44142182103](https://github.com/garvj65/nona/actions/runs/44142182103) |
| Android lint, debug and release builds | Passed | same run |
| Android emulator UI and lifecycle test | Passed | same run, `native-ui` job |
| Physical Bluetooth acceptance | **Not run** | See the checklist below |

## Physical acceptance

### Wi-Fi browser controller

| Check | Status | Date | Notes |
|---|---|---|---|
| NONA Sprint, touch racing | **Device: pass** | 2026-11-16 | |
| NONA Sprint, tilt steering | **Device: pass** | 2026-11-16 | |
| JavaScript Racer, tilt through the keyboard bridge | **Device: pass** | 2026-11-16 | Digital left/right with hysteresis |
| Controller round trip | **Device: 10–40 ms** | 2026-11-16 | Acknowledgement time between the phone and the companion, not the full delay from motion to what's on screen |
| Stop / release all | **Device: pass** | 2026-11-16 | Keyboard path, on 0.4 |
| Roblox, keyboard starter profile | **Device: partial** | 2026-11-16 | Moved and jumped in an unnamed obby; camera felt restricted, which led to 0.5 Move & look |
| Roblox, Move & look (swipe camera, gyro aim) | Not run | | Includes releasing the right mouse button |
| 8-way movement sectors | Not run | | Added in 0.6.1 |
| Screen lock, Wi-Fi loss, reconnect, rotation | Not run | | |
| Virtual Xbox output in a real game | Not run | | Needs ViGEmBus |

### Android Bluetooth app

| Check | Status | Notes |
|---|---|---|
| HID registration on the vivo Y33T | Not run | The first gate: if this fails, the phone's Bluetooth stack doesn't support the keyboard role |
| Windows pairing, and NONA connecting by itself after pairing | Not run | |
| Typing in Notepad, Stop releases everything | Not run | |
| 8-way movement, mouse look, right-button release | Not run | |
| Screen lock and app switch keep the link (foreground service) | Not run | Check Vivo's background-battery setting first |
| Phone Bluetooth off releases keys on the PC | Not run | |
| Relaunch reconnects; Disconnect stops auto-reconnect | Not run | |
| Roblox Move & look, compared with laptop keyboard and mouse | Not run | |
| JavaScript Racer, pulsed steering on vs off | Not run | |

The step-by-step procedure is in [docs/ANDROID_BLUETOOTH.md](docs/ANDROID_BLUETOOTH.md#acceptance-test).

## What automation can't prove

- **Radio compatibility.** The emulator test uses a debug-only, in-process link that sends no Bluetooth or OS input. Whether a particular phone's Bluetooth stack works as a keyboard can only be found on that phone.
- **Sensors.** The browser suite injects simulated orientation and motion events. Drift, axis direction and feel need a real phone.
- **Game acceptance.** CI never runs a third-party game. A game may reject injected input, need a gamepad, or map controls differently in each experience.
- **Windows drivers.** The Xbox path is tested with mocked backends, not an installed ViGEmBus.

## Previous builds

| Build | CI evidence | Device evidence |
|---|---|---|
| 0.6.0 | [Android 44051171819](https://github.com/garvj65/nona/actions/runs/44051171819) (11 unit tests, lint, builds, emulator UI); [checks 44051171867](https://github.com/garvj65/nona/actions/runs/44051171867) | None |
| 0.5.0 | Python, Node and browser suites | Not run for Move & look |
| 0.4.0 | Python, Node and browser suites, including real HTTPS/WSS certificate checks | Tilt racing pass, Stop pass |
| 0.2.0 | Python and browser suites | JavaScript Racer on a phone through the keyboard bridge |

## Recording a result

Add a row to the right table with the date, build or commit, and status. For anything that fails, also note:

```
Device / OS / browser or app version:
PC (CPU · GPU · RAM · Windows version):
Game + URL or version, graphics settings:
Profile and any binding changes:
What happened (steps → expected → actual):
Anything left held? How was it cleared?
Connection details (Bluetooth app → Connection details → Copy):
```
