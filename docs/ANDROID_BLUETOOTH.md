# Android Bluetooth app

The NONA app turns your phone into a **Bluetooth keyboard + mouse**. Windows pairs with it like any wireless keyboard: there's no PC software, no shared Wi-Fi and no certificate to install.

| | |
|---|---|
| **Version** | 0.6.1-preview (debug-signed test build) |
| **Phone** | Android 9+ with a Bluetooth stack that supports the HID device role |
| **PC** | Windows 10/11 with Bluetooth |
| **Status** | CI-tested; first device test pending ([validation](../VALIDATION.md)) |

> [!IMPORTANT]
> Android has offered this feature to apps since Android 9, but some phone makers' Bluetooth stacks don't support it. Step 3 of [Pair](#2-pair-with-your-pc) is the moment you find out.

## 1. Install

1. Open the latest green [Android preview run](https://github.com/garvj65/nona/actions/workflows/android.yml). Under **Artifacts**, download `nona-android-preview` and unzip it.
2. Copy the `.apk` to your phone (USB, Drive or a message to yourself), tap it, and allow **Install unknown apps** for that source.
3. **Uninstall any older NONA first.** Each CI build is signed with a fresh key, so an update over an older build fails.
4. **Let it run in the background.** Some phone makers stop background apps aggressively. On Vivo: **Settings → Battery → background power management → NONA → allow**, and turn on **Auto-start** if it's listed. Menu names vary by OS version.
5. Close any other "phone as keyboard/mouse" apps. Android lets only one app at a time act as a keyboard.

Check: **Connection details** in the app shows `0.6.1-preview` and your Android version.

## 2. Pair with your PC

| Step | Do | You should see |
|---|---|---|
| 1 | If the phone and PC were paired before, remove the pairing on **both** sides | |
| 2 | Open NONA → **Set up Bluetooth** → allow **Nearby devices** | One permission prompt |
| 3 | Wait up to 12 seconds | Amber dot: *Choose a paired computer, or pair a new one.* An error here means this phone can't act as a keyboard. Copy **Connection details**. |
| 4 | Tap **Pair a new computer** → allow visibility | |
| 5 | On the PC: **Settings → Bluetooth & devices → Add device → Bluetooth** → pick your phone → confirm the PIN on both screens | *Your device is ready to go* |
| 6 | Wait about 15 seconds without touching NONA | The PC's row turns **Connected** (green). NONA accepts the computer that just paired. |

If step 6 doesn't happen, tap the PC's row in **Paired devices**.

## 3. Play

1. Tap **Open controller** and choose **Move & look** or **Racing**.
2. Click your game window on the PC.
3. Tap **Play**. Input starts neutral and stays paused until you do.

**Stop** releases everything. Tap it before switching windows on the PC: the PC treats the phone as a physical keyboard, so input goes to whatever has focus.

## Controls

| Profile | Left side | Right side | Buttons |
|---|---|---|---|
| **Move & look** | Floating stick. Touch anywhere, drag: 8-way WASD with equal 45° sectors | Swipe to look (relative mouse) | Jump = Space · Run = Shift · Use = E · Action = Q |
| **Racing** | Stick left/right steers (arrow keys) | — | Gas = ↑ · Brake = ↓ · Slide = Space · Boost = Shift |

The **Controls** button in the controller toolbar opens these settings:
- **Camera speed** for swipe look.
- **Third-person camera (hold right mouse):** holds the right mouse button while you swipe. Turn it off for first-person games that capture the mouse.
- **Gyro assist while touching the look area:** turning the phone adds to the camera while your thumb is on the look area. Needs a gyroscope.
- **Racing: proportional steering:** pulses the arrow key over a 120 ms cycle. Key-down time grows with stick distance; full lock holds the key. Turn it off for games that act once per key press, like lane switchers and menus.

## Connection lifecycle

| Event | What happens |
|---|---|
| **Stop**, leaving the controller, profile change, cancelled touch | Empty reports are sent and input pauses. Resuming needs **Play**. |
| Screen lock or switching apps | Input pauses immediately, but **the connection stays up**. A *NONA is connected* service keeps Android's keyboard registration alive. Come back and tap **Play**. |
| Ten minutes away from NONA | NONA releases the PC completely |
| Next launch | Reconnects to the last PC you chose, unless you tapped **Disconnect** |
| Bluetooth off or out of range | The link drops; Windows releases the keyboard |

Nothing pressed before an interruption is replayed after it.

## Acceptance test

Run this on real hardware, then record the results in [VALIDATION.md](../VALIDATION.md). Use a keyboard-tester web page for anything involving held keys: Notepad auto-repeats only the last key pressed.

| # | Do | Pass |
|---|---|---|
| 1 | Move & look, Notepad: hold the stick up, tap Jump | `wwww…` then a space |
| 2 | Keyboard tester: push up, drift your thumb about 20° right | Only **W** stays lit. At 45° you get **W + D**. |
| 3 | Swipe the right side; turn **Third-person camera (hold right mouse)** on | The pointer follows. The right button is held only while touching. |
| 4 | Hold the stick and Jump, then tap **Stop** | Everything clears at once |
| 5 | Play while holding the stick, lock the phone for 10 s, unlock | Nothing held while locked; still connected; **Play** works without reselecting the PC |
| 6 | Same, but switch to another app for 30 s | Same as 5 |
| 7 | Hold the stick, turn the phone's Bluetooth off | Keys clear on the PC within about 2 s |
| 8 | Swipe NONA out of recents, reopen it | Reconnects by itself |
| 9 | Tap **Disconnect**, swipe NONA away, reopen it | Does **not** reconnect by itself |
| 10 | A Roblox experience: 1 minute on the laptop's own keyboard and mouse, then NONA | Straight walking stays straight; look and jump-while-moving work |
| 11 | JavaScript Racer, Racing: a long curve at half stick, then full | Half: a steady, gentle curve. Full: a hard turn. Compare with proportional steering off. |

> [!CAUTION]
> If any key or button stays held, stop testing and record the step number and how you cleared it. A stuck key is the most important kind of bug to report.

## Troubleshooting

| Symptom | Try |
|---|---|
| Error at registration (Pair step 3) | Close other keyboard/mouse apps, toggle Bluetooth, tap **Retry Bluetooth setup**. If it still fails, the phone's Bluetooth stack probably doesn't support the keyboard role; use the [Wi-Fi controller](../README.md#quick-start-wi-fi) instead. |
| The PC paired, but no keyboard appears in Device Manager | Remove the pairing on both sides. Open NONA to the *Choose a paired computer* screen **before** clicking **Add device** on the PC, so Windows sees the keyboard service during pairing. |
| Connected, but nothing types | Make sure you tapped **Play** (the surface shouldn't say *Paused*) and the target window has focus |
| The link drops when the screen locks | Allow NONA to run in the background (Install, step 4) |
| A key keeps repeating | Tap **Stop**. If it persists, turn the phone's Bluetooth off; Windows releases everything from a disconnected keyboard. |

## Build from source

```powershell
cd android
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug
```

Needs JDK 17 and Android SDK 35. More in [DEVELOPMENT.md](DEVELOPMENT.md).

## Limits of this preview

- Keyboard + mouse only. A Bluetooth gamepad (analog sticks over HID) is on the [roadmap](ROADMAP.md).
- Racing has no tilt steering yet; use the Wi-Fi controller for tilt.
- It's a debug-signed test APK, not a Play Store release.
- If the phone fails abruptly mid-press, key release depends on Windows.
