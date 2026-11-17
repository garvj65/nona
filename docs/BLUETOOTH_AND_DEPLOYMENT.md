# Bluetooth feasibility and deployment proposal

Researched: 2026-11-17. Status: design exploration, not implemented or device-verified. NONA 0.5 remains the existing browser/Windows prototype. The owner accepted the companion QR/trust direction in APP_PAIRING.md and asked whether Bluetooth could remove both shared-Wi-Fi setup and a PC download.

## The decision Bluetooth alone does not answer

There are two different architectures:

1. **Direct Bluetooth HID:** the native Android app presents standard keyboard/mouse or generic gamepad reports. Windows handles the input device through its HID stack. This is the candidate that could remove the NONA PC download.
2. **Bluetooth data to a companion:** the app sends NONA control packets over a custom Bluetooth service, and a Windows receiver translates them into keyboard/mouse or virtual-controller output. It removes the same-Wi-Fi requirement, but the PC companion remains necessary. This transport is not implemented.

Android exposes BluetoothHidDevice from API 28, including keyboard/mouse combo and gamepad subclasses. Windows supplies Bluetooth HID transport drivers. Together these support the feasibility of the direct-HID architecture; they are not a successful test of the owner's Vivo Bluetooth stack, laptop radio or Roblox experience.

| Route | NONA PC app | Expected input path | Remaining condition |
|---|---|---|---|
| Direct Bluetooth keyboard/mouse | Not needed if the prototype succeeds | Floating WASD movement, buttons, relative swipe/gyro mouse | Confirm HID registration, Windows enumeration and actual gameplay |
| Direct Bluetooth generic gamepad | Not needed for a game accepting the device | Analog axes/triggers/buttons described by a HID report descriptor | Recognition and mapping are game-specific; this is not automatically XInput |
| Companion over Wi-Fi | Required | Existing keyboard/mouse or optional virtual Xbox backend | Native app-scoped TLS trust and packaged host are still to be built |
| Companion over Bluetooth data | Required | Companion performs the translation | Future transport; must test Windows/Android Bluetooth services and reconnect |

A generic HID controller is not automatically an Xbox controller. Microsoft's XInput documentation states that XInput does not recognize legacy DirectInput devices. Keep the companion option for titles requiring a compatible virtual Xbox path and for host-side features. Do not advertise universal game support from a Bluetooth pairing success.

## Recommendation

Keep one native Android app with a shared touch/sensor/profile engine and separate output adapters. Investigate direct Bluetooth keyboard/mouse first, since it corresponds to the current working WASD/swipe-camera controls. Then test generic analog gamepad HID separately. Retain the approved companion route as a fallback and an option for Windows-side translation, diagnostics and game-window focus handling.

Run the Bluetooth proof of concept before committing the store-facing product to a no-PC-app promise. If it passes on supported devices, make direct mode the simple entry path. If it does not, ship a clear companion flow instead of blocking the product indefinitely. Do not implement three transports in parallel before validating one.

Bluetooth is not inherently a latency improvement. Measure feel and gesture-to-display response under comparable game/frame-rate conditions. The owner's 10–40 ms Wi-Fi acknowledgement RTT is not directly comparable with Bluetooth sendReport returning success. Bluetooth changes controller connectivity; an online game still needs its own internet connection.

## Native Android requirement and capability gate

Use a native Android API path for HID Device mode. Chrome's Web Bluetooth exposes the BLE central/GATT-client role; switching the current web controller to Web Bluetooth does not make the phone advertise itself as a Bluetooth HID peripheral.

On the Vivo, verify the actual model/Android version and runtime availability of HID_DEVICE. Obtain the required Nearby devices permissions, obtain the HID profile proxy, register the app, and use onAppStatusChanged to establish registration. A successful registerApp return only indicates that the registration command was sent. Use the connection callback to establish the HID connection; an ordinary Bluetooth bond alone is not enough.

Android documents that only one HID app can be registered and that it is automatically unregistered when it is not foreground. Keep the controller app open while playing, and explicitly handle pause, screen lock, unregister and reconnect. Do not assume a background service makes this platform limitation disappear.

## Proposed install and play flows

### Direct Bluetooth

1. Install NONA on Android. Early testers receive a signed test APK or test-track build; production Google Play publication follows device validation and release review. This is an Android-first release, not an existing store listing. An iPhone/App Store version needs separate capability and platform work.
2. Open NONA, select direct Bluetooth, and grant the necessary OS Bluetooth permissions. Register the intended HID descriptor before the pairing/discovery step.
3. In Windows Bluetooth settings, add/select the phone and complete the OS pairing confirmation. The app shows the actual phone/PC names; do not depend on silently renaming the user's phone globally.
4. Once HID registration and the host connection are confirmed, choose the game profile. Begin with neutral reports and controls paused.
5. Open/focus the game on Windows and tap Play in NONA. Use movement, look, buttons and optional sensor assistance.
6. Stop sends neutral key/button/axis reports before pausing. Background/lock/Bluetooth loss disables controls; reconnect clears stale state and requires Play again rather than replaying held input.
7. Later sessions can select the remembered paired PC and reconnect through OS bonding. Support explicit disconnect and unpair.

This route has no NONA TCP port, IP address, HTTP certificate or companion QR requirement. It uses standard Bluetooth pairing/security. The app still needs to limit connections to the selected bonded host and handle permission/revocation correctly.

Direct HID behaves like a physical keyboard/mouse: it targets the foreground Windows application. Without a PC component, NONA cannot enforce the companion's chosen-game-window guard or independently neutralize inputs on the host when the phone disappears. Release before switching apps; test Windows' actual disconnect behavior. Do not promise guaranteed cleanup after an abrupt phone failure.

### Companion mode

1. Install the Android app and a packaged NONA Windows companion. The Windows bundle includes its runtime; end users should not install Python, use pip or run development batch scripts.
2. Open the companion, allow its scoped OS network permission and scan its QR in NONA. The phone verifies the PC identity inside the app; approve the phone on the PC. Follow APP_PAIRING.md for the detailed trust contract.
3. Select the game window and controller profile, then start the session. Keep host-side output arming, game-window focus checks, neutralization and diagnostics.
4. Stop, background/lock, loss of connection or loss of the selected game focus pauses/disarms the session. Reconnect begins neutral and does not automatically resume output.

The first companion transport can reuse Wi-Fi. A later Bluetooth-data adapter could remove router dependence while retaining companion features. A switch of transport must release and end the old session first so the game never receives duplicate control streams.

## Proposed deployment order

1. Build a small native Android Bluetooth capability/HID keyboard+mouse probe before a complete store app. Pair to the owner's Windows laptop with the existing NONA server closed; confirm typing/mouse and right-button release without any NONA PC process.
2. Add the shared mobile controller UI/sensors and test the same Roblox experience, external racer and a sustained session. Record the exact experience, laptop baseline performance, camera feel and reconnect/lock/loss results.
3. Separately probe generic HID gamepad axes in Windows and in a real game. Detection in joy.cpl or a browser tester is not proof of game compatibility or XInput support.
4. Implement the native companion pairing fallback and a self-contained Windows bundle. Retain the optional virtual-controller dependency as an explicit compatibility/maintenance decision.
5. Review and security-test both modes, fix actual findings, and verify clean installs, updates, uninstall, rejected hosts, mode switches and input cleanup. Use managed release signing; do not commit private signing keys.
6. Distribute an Android test release and Windows test bundle; after acceptance, publish Android through Google Play and the companion through an official release/download page. Microsoft Store is a possible later channel. A companion download is optional only for the specific direct-HID paths that passed testing.

Keep the PS5 phone-controller product separate. A Windows Bluetooth HID success does not establish that a real PS5 will accept the phone as a DualSense replacement.

## Primary sources

- Android HID Device API, registration callbacks and foreground lifetime: https://developer.android.com/reference/android/bluetooth/BluetoothHidDevice
- Android SDP descriptor advertisement: https://developer.android.com/reference/android/bluetooth/BluetoothHidDeviceAppSdpSettings
- Android Bluetooth permissions: https://developer.android.com/develop/connectivity/bluetooth/bt-permissions
- Windows Bluetooth HID transport: https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-transports
- Windows XInput/DirectInput distinction: https://learn.microsoft.com/en-us/windows/win32/xinput/xinput-and-directinput
- Browser Bluetooth role: https://developer.chrome.com/docs/capabilities/bluetooth
