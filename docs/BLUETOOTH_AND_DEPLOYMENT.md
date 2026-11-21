# Decision record 001: Bluetooth transport and distribution

| | |
|---|---|
| **Status** | Accepted. Direct Bluetooth HID shipped in 0.6 (keyboard + mouse). |
| **Date** | 2026-11-17 (decided) · updated 2026-11-21 for 0.6.1 |
| **Question** | Can Bluetooth remove both the shared-Wi-Fi requirement and the PC download? |

## Context

The Wi-Fi path works, but it asks a lot of a new user: same network, firewall approval, a Python install, and for tilt a manually trusted local CA. Bluetooth could remove some or all of that, depending on which of two architectures we pick.

## Options

| | **A. Direct Bluetooth HID** | **B. Bluetooth data to the companion** |
|---|---|---|
| How | The phone presents itself as a standard HID device (keyboard, mouse, gamepad). Windows' own HID stack handles it. | The phone sends NONA packets over a custom Bluetooth service; a Windows receiver translates them. |
| PC install | **None** | Companion required |
| Shared Wi-Fi | Not needed | Not needed |
| Output | What the HID descriptor declares: keyboard + mouse now, a generic gamepad possibly later | Anything the companion supports, including a virtual Xbox pad |
| Window guard | No: acts like a physical keyboard | Yes |
| Platform API | `BluetoothHidDevice`, Android 9+ | Android RFCOMM/GATT plus a Windows receiver |

Web Bluetooth in Chrome is **not** an option: it gives a page the BLE central (client) role, so the phone can't present itself as a HID device from a web page.

## Decision

**Build A first, for keyboard + mouse.** It matches the controls that already work (WASD movement, mouse camera), needs zero PC install, and uses only the standard Bluetooth pairing in Android and Windows. Keep the Wi-Fi companion as the full-featured path: window guard, virtual Xbox pad, tilt, custom bindings. **Defer B** until the companion is packaged; on its own it saves the Wi-Fi step but not the install.

## Consequences

- **The phone's Bluetooth stack has to cooperate.** The API has existed since Android 9, but each phone maker's Bluetooth stack has to support the HID device role. That's the first device gate ([ANDROID_BLUETOOTH.md](ANDROID_BLUETOOTH.md#acceptance-test)).
- **Android limits who can register, and when.** Only one app can be registered as a HID device at a time, and Android's HID service unregisters an app whose process is no longer foreground-important. 0.6 also unregistered itself in `onStop`, so a screen lock dropped the PC. **0.6.1 runs a `connectedDevice` foreground service while connected.** That keeps the process important enough to stay registered through locks and pairing screens while input pauses, with a 10-minute off-screen cutoff.
- **No window guard.** Input goes to whatever has focus. The app makes **Play** an explicit step and releases on every lifecycle event; users are told to tap Stop before switching windows.
- **Cleanup after abrupt loss depends on Windows.** NONA sends empty reports on every path it controls. If the phone dies mid-press, release is up to Windows' HID disconnect handling.
- **A generic HID gamepad isn't XInput.** Games built on XInput ignore it. Analog gamepad over Bluetooth is a separate feature with its own compatibility gate ([roadmap](ROADMAP.md#after-v1)).
- **Bluetooth isn't automatically lower-latency.** The Wi-Fi 10–40 ms figure is an acknowledgement round trip, which can't be compared with HID `sendReport` returning. Measure what the player feels under the same conditions.

## Distribution plan

1. **Now:** debug-signed test APKs from CI ([Android preview](https://github.com/garvj65/nona/actions/workflows/android.yml)).
2. **After the device and game gates:** a signed test track, then a Google Play release with managed signing. No signing keys in the repository.
3. **Windows companion:** a self-contained installer with no Python install, scripts or pip. It needs a firewall permission scoped to the app on private networks, and keeps the virtual Xbox driver as an explicit, separate choice.
4. A companion download becomes **optional** only for the paths where direct Bluetooth passed device testing.

iOS can't act as a Bluetooth HID device through public APIs. An iPhone version would need its own design.

## Sources

[Android BluetoothHidDevice](https://developer.android.com/reference/android/bluetooth/BluetoothHidDevice) · [HID SDP settings](https://developer.android.com/reference/android/bluetooth/BluetoothHidDeviceAppSdpSettings) · [Android Bluetooth permissions](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions) · [Windows HID transports](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-transports) · [XInput vs DirectInput](https://learn.microsoft.com/en-us/windows/win32/xinput/xinput-and-directinput) · [Chrome Web Bluetooth](https://developer.chrome.com/docs/capabilities/bluetooth)
