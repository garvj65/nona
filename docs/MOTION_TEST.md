# Tilt steering (Wi-Fi)

Steer by turning the phone like a wheel. Tilt works with **NONA Sprint**, with keyboard racers through the bridge, and with the virtual Xbox pad. Gas and Brake stay on the touch screen.

| | |
|---|---|
| **Profiles** | Any **Racing** profile |
| **Needs** | Trusted local HTTPS (one-time setup below) |
| **Status** | **Device-tested.** Tilt racing passed in NONA Sprint and JavaScript Racer on a vivo phone with a Windows laptop ([validation](../VALIDATION.md)) |

## Why HTTPS

Browsers only expose motion sensors on a **secure connection**, and a phone opening a laptop's plain `http://192.168…` address isn't one. NONA never asks you to turn off browser protections or click through certificate warnings. Instead it makes a small local certificate authority (CA) that you choose to trust on your own devices.

> [!WARNING]
> Trusting a root CA changes what your device trusts. Compare fingerprints before you install it, keep its private key on the laptop, and remove it when you're done ([below](#remove-the-test-ca)). The native app won't need this: per-device pairing is designed in [APP_PAIRING.md](APP_PAIRING.md).

## One-time setup

| Step | Where | Do |
|---|---|---|
| 1 | PC | If this is a new folder, run `START_WINDOWS.bat` once, then close it |
| 2 | PC | Run **`PREPARE_MOTION_HTTPS.bat`**. It creates certificates in `%LOCALAPPDATA%\NONA\tls` and prints the CA's **SHA-256 fingerprint**. Keep that window open. |
| 3 | PC | Open `NONA-local-CA.crt` in that folder → **Install Certificate → Current User → Trusted Root Certification Authorities**. Don't pick a machine-wide store. |
| 4 | PC + phone | Start `START_WINDOWS.bat`, pair the phone, choose a Racing profile, open **HTTPS setup** on the phone and tap **Download public motion CA**. This is the public `.crt`, never a `.pem` key. |
| 5 | Phone | **Settings** → search *Install a certificate* → **CA certificate** → pick `NONA-local-CA.crt`. **Check that the fingerprint matches step 2** before you confirm. Menu paths vary by phone maker. |
| 6 | PC | Close NONA and start **`START_MOTION_WINDOWS.bat`**. The dashboard opens at `https://localhost:8765`, and the QR code now uses HTTPS. |
| 7 | Phone | Scan the new QR code. Both pages should load with **no certificate warning**. If you get one, stop and fix the trust setup; don't bypass it. |

The CA is valid for a year. Server certificates last 90 days or less; rerun step 2 to renew them, or whenever the laptop's LAN IP changes. You don't need to reinstall the CA for that. If you already have a trusted certificate covering the laptop's LAN address, run `run.py --certfile PATH --keyfile PATH` instead.

## First tilt test

1. Open **NONA Sprint** and leave desktop output **off**, because the demo reads the phone directly.
2. Choose **Racing · Arrows**, turn the phone sideways and go fullscreen **before** calibrating.
3. Hold the phone upright, screen facing you; a flat phone can't give a stable angle. Tap **Enable tilt**, allow sensors, hold your neutral position and tap **Calibrate**.
4. Hold Gas and turn the phone. The wheel should follow. Use **Invert** if it turns the wrong way. **Full turn** (20°, 30° or 45°) sets how far you tilt for full lock.
5. Try Brake, slow turns both ways, then a full lap.
6. Check that **Use touch**, **Stop**, rotating the phone, locking the screen and a Wi-Fi drop all release input.
7. Then move to **JavaScript Racer**: calibrate, click **Enable output** on the laptop, and click the game within 4 seconds.

Tilt releases and disarms output if readings stop for about 750 ms or the phone's orientation becomes unusable. Rotation, profile changes and reconnecting all need **Enable tilt** and **Calibrate** again. Calibration, invert and range are runtime settings, not saved in profiles.

## Remove the test CA

When you're done, remove **NONA local motion test CA** from Android's user credentials and from Windows' Current User trusted roots. Remove only that certificate. If the CA's private key is ever exposed, remove the trust everywhere and generate a new CA.

References: [MDN: device orientation](https://developer.mozilla.org/en-US/docs/Web/API/Device_orientation_events/Detecting_device_orientation) · [Chrome root store FAQ](https://chromium.googlesource.com/chromium/src/+/HEAD/net/data/ssl/chrome_root_store/faq.md)
