# Mobile movement and camera — prototype 0.5

The owner reported that the Roblox keyboard starter could move/jump in an unnamed obby, but movement and looking felt restricted. That starter had digital directions and no camera output. This iteration adds a floating movement surface, swipe mouse look and optional motion-assisted camera input. It does not establish that a particular Roblox experience accepts the new mouse output until physically tested.

## Update the working installation

Close NONA, then update the source in the existing working folder (`git pull` for a Git checkout, or copy the new ZIP's contents over the working source folder). Keep the existing `.venv`; do not copy an environment from another computer. Certificates remain in `%LOCALAPPDATA%\NONA\tls`, outside the repository. This change adds no Python package or driver requirement for keyboard/mouse output, and does not require recreating the existing CA.

Use START_MOTION_WINDOWS.bat for gyro. Scan the current dashboard QR after restarting; the old pairing link expires. For swipe-only controls, START_WINDOWS.bat also works. Motion sensors still need trusted HTTPS in the browser prototype. Device-wide certificate installation is a prototype limitation, not the intended native-app onboarding; see APP_PAIRING.md.

## Roblox: start with touch controls

1. Confirm that the same experience is playable with the laptop's keyboard and mouse. If it is choppy with those too, reduce Roblox graphics or choose a lighter experience; controller changes do not fix a low game frame rate.
2. Pair the phone, use landscape/fullscreen, and select **Roblox · Mobile movement + look**. Select the profile before arming laptop output.
3. On the laptop choose **Windows keyboard / mouse**, click **Enable output**, and focus the Roblox window within four seconds.
4. Touch anywhere in the left surface and drag from that starting point to move. The floating stick is neutral on touch-down. Releasing centres it. WASD remains digital, including diagonal combinations; it cannot represent analog walking speed.
5. Swipe the right surface to move the camera. Lift and swipe again for a longer turn. This profile holds the right mouse button only during the look gesture, for a typical third-person camera. Experience controls can differ.
6. A jumps; B maps Shift; X maps E; Y maps Q. These are starter bindings. Test movement + look + jump together, then adjust optional actions to the experience.
7. Change the phone's Look setting for a runtime speed adjustment. On the laptop, **Swipe camera settings** offers a saved base speed and a right-mouse drag switch. Apply, save a named profile if desired, then re-enable output. For first-person games that already capture the mouse, use **Mouse look · First person** or disable the right-mouse switch.

If mouse look is rejected, record the experience and result rather than forcing compatibility. The optional **Roblox · Xbox candidate** already supplies real analog axes and two-stick camera input where a gamepad is supported. Complete GAMEPAD_SETUP.md separately; the mouse route does not require that driver.

## Add optional gyro assist

First establish usable swipe look. Tap **Enable gyro assist** on the phone and allow sensor permission if asked. The action releases/disarms output; enable laptop output again afterward and focus Roblox. There is no neutral-angle calibration for this angular-velocity mode.

Hold the right look surface and rotate the phone gently to assist camera aiming. Swiping and motion add together. Lifting the look thumb stops gyro camera output, so moving the phone while navigating menus does not aim. Use **Invert gyro Y** if needed. This is camera assistance, separate from the racing tilt-steering mode. Gyro response is bounded and filtered, but physical axis direction and feel must still be checked on the owner's Vivo phone.

Touch-only mode remains available when sensors are absent, denied or unusable. A missing/stale gyro stream releases input and disarms output; re-enable the desired mode and laptop output afterward. Screen rotation, hiding the page, profile changes, Stop and reconnect clear motion state. Browser lifecycle behavior still needs physical screen-lock/Wi-Fi-loss tests.

## Input path and limits

- Continuous changes are coalesced into a 50 Hz send loop; button down/up send immediately so short taps are retained. This is a send budget, not an end-to-end latency guarantee.
- Relative camera deltas are bounded per packet, consumed once, and never replayed by the host watchdog. Excessive browser socket buffering closes the controller connection instead of intentionally building an unbounded input queue.
- Windows output must be explicitly armed and stays attached to the selected foreground window. Changing focus, disconnecting, timing out or stopping releases owned keys and right mouse. A rejected mouse release is retried; failed cleanup prevents rearming.
- The protocol accepts old button/axis packets. Old saved profiles default to camera disabled. Camera settings are validated and changed by the laptop admin; profile changes disarm output.
- Browser/CI tests do not prove actual Windows game input acceptance, phone sensor quality or improved gameplay FPS.

## Acceptance report

Record the experience URL, whether laptop keyboard/mouse runs smoothly, the chosen NONA profile, simultaneous move/look/jump, camera speed/direction, gyro feel and typical controller RTT. Explicitly try Stop, screen lock, Wi-Fi loss/reconnect, orientation change and switching laptop windows. The owner has confirmed Stop for 0.4; screen lock and deliberate Wi-Fi interruption remain untested. The new mouse/right-button path needs those checks too.

References: https://create.roblox.com/docs/input/gamepad · https://create.roblox.com/docs/input/mouse-and-keyboard · https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput · https://w3c.github.io/deviceorientation/#devicemotion · https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/modules/device_orientation/device_motion_event_pump.cc
