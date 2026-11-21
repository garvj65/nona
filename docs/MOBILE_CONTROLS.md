# Move & look controls (Wi-Fi)

Move & look gives third-person games like Roblox what a plain D-pad can't: free movement plus a camera. The left half of the phone is a floating movement stick. The right half is a swipe camera that drives the PC's mouse, with optional gyro aim.

| | |
|---|---|
| **Profiles** | **Roblox · Mobile movement + look** (third person) · **Mouse look · First person** |
| **Output** | Windows keyboard / mouse |
| **Needs** | The Wi-Fi companion running. Gyro aim also needs [trusted local HTTPS](MOTION_TEST.md). |
| **Status** | CI-tested; device test pending ([validation](../VALIDATION.md)) |

Using the Bluetooth app instead? It has the same Move & look profile. See [ANDROID_BLUETOOTH.md](ANDROID_BLUETOOTH.md).

## Set up

1. **Check the game first.** Play a minute with the laptop's own keyboard and mouse. If it stutters, lower the graphics settings; a controller can't fix a low frame rate.
2. Start NONA (`START_WINDOWS.bat`, or `START_MOTION_WINDOWS.bat` if you want gyro), scan the QR code and turn the phone sideways.
3. On the laptop, choose the profile and **Windows keyboard / mouse**. Choose the profile *before* enabling output, because changing profiles disarms output.
4. Click **Enable output**, then click the game window within 4 seconds.

## Use

| Control | How it works |
|---|---|
| **Move (left half)** | Touch anywhere; that point becomes the stick centre. Drag to move: 8-way WASD with equal 45° sectors and hysteresis, so an angled thumb still walks straight. Lift your thumb to stop. |
| **Look (right half)** | Swipe to turn the camera; lift and swipe again for a bigger turn. In the third-person profile the right mouse button is held only during the swipe. |
| **Buttons** | A jumps (Space) · B = Shift · X = E · Y = Q. These are starter bindings; experiences differ. |
| **Look speed** | Runtime: the phone's **Look** menu. Saved default: dashboard → **Swipe camera settings** → **Apply camera settings**. |

Movement is digital, so WASD can't walk slowly. For analog movement use the [virtual Xbox pad](GAMEPAD_SETUP.md) with **Roblox · Xbox candidate**.

## Gyro aim (optional)

Set up swipe look first. Then tap **Gyro assist** on the phone and allow sensor access.

- Gyro moves the camera **only while your thumb is on the look area**, so moving the phone in menus doesn't aim. Swipe and gyro add together.
- Use **Invert gyro Y** if up and down feel reversed. Use **Touch only** to turn gyro off.
- Turning gyro on disarms output. Re-enable it on the laptop and refocus the game.
- If sensor readings stop, input is released and output disarms. Re-enable gyro or carry on with touch.

## How it stays safe

- Continuous input is sent at up to 50 Hz, and button presses are sent immediately, so short taps still register.
- Camera movement per packet is bounded (96 or less) and applied **once**. The watchdog never replays it.
- Output follows the window you armed. Focus loss, disconnect, timeout, Stop and profile change release every key and the right mouse button. If a release fails, NONA retries it, and output can't be re-armed until the release succeeds.

## What to report

Experience name or URL, how it plays on the laptop alone, the profile used, whether moving, looking and jumping all work together, camera speed and direction, gyro feel, and the controller round-trip time shown on the phone. Also try Stop, locking the screen, a Wi-Fi drop, rotating the phone and switching windows. Record the results in [VALIDATION.md](../VALIDATION.md).

References: [Roblox mouse and keyboard input](https://create.roblox.com/docs/input/mouse-and-keyboard) · [Roblox gamepad input](https://create.roblox.com/docs/input/gamepad) · [Win32 SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
