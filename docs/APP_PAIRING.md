# Native app pairing: companion-mode implementation contract

Status: planned, not implemented. The browser prototype still uses its documented manual CA setup for motion. The user requested a native Android app and Windows companion after the controller experience is usable. Installing a device-wide root CA must not become the app's normal onboarding.

The owner accepted this pairing direction on 2026-11-17. Keep it for the Wi-Fi companion route. [BLUETOOTH_AND_DEPLOYMENT.md](BLUETOOTH_AND_DEPLOYMENT.md) explores an additional direct Bluetooth HID mode that could work without NONA software on the PC, subject to device/game tests. Ordinary Bluetooth data transport would still need a PC receiver. These are separate connection routes; direct HID uses OS Bluetooth pairing rather than this TLS/QR flow.

## Intended user flow

1. Install/open the Windows companion and Android NONA app.
2. Scan the companion's pairing QR in NONA.
3. Approve the phone on the companion.
4. Choose a controller profile and play.

Normal OS camera/local-network/firewall permission prompts may still be necessary. The installer/companion should offer a private-network, application-scoped firewall permission rather than asking users to run PowerShell, disable a firewall, or open a router port.

## Transport and trust

Use TLS with trust restricted to the paired PC inside the Android app. Android supports app-specific network trust. For per-PC keys discovered at runtime, implement a narrowly scoped native trust policy using the QR's authenticated identity; a static global network-security XML file alone does not implement dynamic pairing.

The laptop display is the trust bootstrap. A versioned, expiring QR carries the endpoint, the host's public-key fingerprint and a high-entropy, short-lived pairing secret. The Android client verifies the presented host identity and certificate validity/address before sending the secret over TLS. The laptop explicitly approves the device and issues a per-device credential. The native client stores host trust and its credential privately; use Android Keystore-backed protection where applicable. Never put a CA private key into a QR or APK.

Scope this trust to NONA's paired host connection. Do not install a root into the phone's global trust store, accept all TLS certificates, ignore hostname errors, or make a WebView proceed past SSL errors. Endpoint discovery must not silently replace a paired host's identity. A key change requires a clear repair/re-pair flow.

Implement using established TLS, secure random tokens and platform key storage rather than inventing an encryption protocol. The current browser's launch-scoped shared token is a prototype mechanism, not the complete per-device native pairing design. Physical QR access/approval is an explicit trust assumption; a remote invitation/relay would require a separate design.

## Session lifecycle

- Pairing secrets expire, are rate limited and become unusable after successful pairing. A random nearby LAN client must not claim control using a device name alone.
- Keep a paired-device list and host-side revoke action. Revocation closes any active controller session and releases output.
- Authorize every controller connection; avoid reusable bearer secrets in logs, screenshots or discovery broadcasts.
- Preserve one active controller's ownership; reconnect authenticates the paired phone and begins neutral/disarmed, never replaying queued input.
- Require host action to arm native output for a selected game. Keep stop, focus, timeout and mobile background release behavior.
- On Android background/lock/network loss, close the input session and release locally held state. The host must independently neutralize on timeout.

## App implementation and packaging order

Use a native Android client (Kotlin is the proposed first target) with native touch and sensor APIs. Keep the existing normalized actions/axes and bounded pointer deltas as the initial host protocol. Make protocol capability/version negotiation explicit before expanding it. Reuse validated input math where feasible and verify sensor coordinates against Android's native device/display axes rather than copying browser property names.

After the mobile-control physical acceptance test: implement native QR pairing/trust and app lifecycle, review/security-test the resulting code, fix findings, then build and test signed Android and Windows distribution artifacts. A Windows Python-free bundle should retain the optional Xbox driver as an explicit dependency decision. Re-evaluate its retired upstream driver before calling the product broadly supported.

Required security/release evidence includes wrong-host/changed-key/expired-cert rejection, replayed pairing secrets, revoked-device rejection, conflicting controllers, malformed/rate-excess packets, profile imports, output ownership, focus/lock/loss cleanup, key storage, dependency provenance, installer firewall scope, upgrade/uninstall and actual installation on the owner's Windows/Vivo setup. This document is a contract, not a completed security assessment or a shipped app.

Primary reference: https://developer.android.com/privacy-and-security/security-config
