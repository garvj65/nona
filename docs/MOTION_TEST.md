# Phone tilt steering — prototype 0.4

This is the next test build, not the packaged v1 application. Tilt is implemented for the Racing layout. Gas and Brake remain touch controls. The sensor output uses the existing steering path for NONA Sprint, keyboard racing and optional Xbox output.

## Why HTTPS is part of setup

A phone opening the laptop's plain LAN HTTP address is not a secure browser context. Device orientation requires a secure context, so the browser prototype needs trusted HTTPS. NONA does not ask you to disable browser protections or click through certificate errors.

The supplied local-CA setup is an optional developer/test path for your own laptop and phone. Installing a root CA changes device trust: protect its private key, compare the public certificate's fingerprint against the laptop, and remove that CA when you no longer need this test setup. No trust settings are changed by the preparation script. A v1 native Android client should use app-scoped trust/pairing rather than require a device-wide test CA.

## One-time local HTTPS preparation

1. Update the repository and close NONA's old terminal.
2. If this is a new folder, run START_WINDOWS.bat once to create its Python environment, then close NONA.
3. Run **PREPARE_MOTION_HTTPS.bat**. It installs the optional HTTPS dependency and generates local certificates under `%LOCALAPPDATA%\NONA\tls`. It prints the public CA's SHA-256 certificate fingerprint. Keep that terminal available for comparison.
4. On Windows, open `%LOCALAPPDATA%\NONA\tls\NONA-local-CA.crt`, review it and use **Install Certificate → Current User → Place all certificates in the following store → Trusted Root Certification Authorities** if you choose to trust this locally generated CA. Do not select a system-wide store unnecessarily. Organization-managed devices may block user trust installation; use touch mode in that case.
5. Start **START_WINDOWS.bat** temporarily. The dashboard now shows the public CA fingerprint. Pair the phone using its HTTP QR code, choose a Racing profile, expand **HTTPS setup for your phone**, and download the **public motion CA**. This is the public `.crt`, never either private `.pem` key.
6. On Android, search Settings for **Install a certificate**, then choose **CA certificate** and select `NONA-local-CA.crt`. Typical Pixel path: Security & privacy → More security settings → Encryption & credentials. OEM paths vary. Verify the certificate SHA-256 fingerprint against the one printed on your laptop before trusting it. Do not install a different/unverified certificate. A screen-lock confirmation may be required.
7. Close HTTP NONA and start **START_MOTION_WINDOWS.bat**. The dashboard now opens at `https://localhost:8765` and its QR code uses HTTPS. Reopen Chrome if it cached the old trust state. Scan the new QR code on Android.
8. Confirm both pages load without certificate warnings. If they do not, stop and fix the trust/hostname issue or return to touch mode; do not bypass the warning.

Private keys `ca-key.pem` and `server-key.pem` remain on the laptop and must not be shared, committed or copied to the phone. Only the public CA route is served. The CA lasts one year; leaf server certificates last at most 90 days. Rerunning preparation renews the server certificate using the same CA. If your laptop's LAN IP changes, rerun preparation with NONA closed; the installed CA can stay the same. An expired/invalid CA requires deliberate replacement and removal of old device trust.

If you already have a suitable trusted certificate with the laptop's local address in its Subject Alternative Names, `run.py --certfile PATH --keyfile PATH` is an alternative.

## First physical motion test

1. Use NONA Sprint first. Leave native output off for this direct-input demo.
2. On the phone select **Racing · Arrows**, turn it sideways, and use fullscreen if desired **before calibration**.
3. Hold the screen reasonably upright and facing you. A nearly flat screen cannot provide a stable steering angle from this gravity projection.
4. Tap **Enable tilt**, grant sensor access if the browser asks, then hold your comfortable neutral position and tap **Calibrate**.
5. Start the race, hold Gas with a thumb, and rotate the phone left/right. The steering indicator should follow you. If its direction feels reversed, use **Invert**. Choose 20°, 30° or 45° for the angle needed to reach full steering.
6. Return to neutral and release Gas. Test Brake, turn slowly in both directions, then try a short lap.
7. Test **Use touch**, **Release / stop**, phone rotation, screen lock, and Wi-Fi interruption. Output should release. Screen rotation, profile changes and reconnect require enabling/calibrating motion again.
8. Once the local test feels good, open the already-working JavaScript Racer. After calibrating tilt, enable laptop keyboard output and select the game window within four seconds. Calibration/stop disables native output, so enable it after calibrating.

Tilt stops and disarms output if readings stop for about 750 ms or the orientation becomes unusable. Enabling waits up to four seconds for a usable sample. Motion is exclusive with the touch wheel, while pedals remain available. Motion calibration, inversion and full-turn range are runtime settings in this prototype, not saved game-profile fields.

## Report the result

Record Android model/version, browser, HTTPS setup result, neutral drift, steering direction, portrait/landscape behavior, responsiveness, and whether you can finish a lap. Automated sensor events do not establish physical sensor behavior or enjoyment.

After this passes on your phone, follow ROBLOX_TEST.md. The v1 review/security/packaging gate remains after both physical tests.

## Remove test trust later

Remove **NONA local motion test CA** from Android's user trusted credentials and Windows Current User's Trusted Root Certification Authorities when finished with the test setup. Remove that specific certificate, not all credentials. Keep or delete its local key material according to whether you intend to reuse it; if the private CA key is exposed, remove its trust and generate a new CA rather than reuse it.

References: https://developer.mozilla.org/en-US/docs/Web/API/Device_orientation_events/Detecting_device_orientation · https://support.google.com/pixelphone/answer/2844832 · https://chromium.googlesource.com/chromium/src/+/HEAD/net/data/ssl/chrome_root_store/faq.md
