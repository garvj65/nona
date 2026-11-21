# Native app pairing (Wi-Fi companion)

| | |
|---|---|
| **Status** | Designed, not built. The target for v1's Wi-Fi mode ([roadmap](ROADMAP.md)). |
| **Replaces** | The browser path's per-launch shared token and the manually trusted local CA |
| **Not used by** | Direct Bluetooth, which relies on the operating systems' own Bluetooth pairing |

## Goal

Pairing a phone with a PC should feel like pairing headphones: **scan, approve, play.** That has to happen without installing a root certificate on the phone, accepting arbitrary certificates, or any terminal work.

## User flow

1. Open the Windows companion and the NONA app.
2. Scan the companion's QR code in NONA.
3. Approve the phone on the PC.
4. Choose a profile and play. Later sessions reconnect without the QR code.

The only operating-system prompts should be the camera and an application-scoped firewall rule on private networks. No PowerShell, no turning off the firewall, no router changes.

## Trust model

**The laptop screen is where trust starts.** Physically seeing the QR code is the authorization.

| Step | Mechanism |
|---|---|
| QR contents | Versioned and expiring: endpoint, the **host's public-key fingerprint**, and a high-entropy, single-use pairing secret |
| Host verification | The app opens TLS and **pins** the host key from the QR code before sending anything secret |
| Device enrolment | After the PC approves, the companion issues a **per-device credential**, stored with Android Keystore protection |
| Later sessions | Mutual: the app pins the host key, and the host authenticates the device credential |
| Key change | Re-pairing must be explicit. Discovery can never silently swap a paired host's identity. |

Trust is scoped to NONA's own connection, using a narrowly scoped trust policy inside the app built from the pinned key. A static network-security XML file can't express keys learned at runtime. **Never** install a device-wide root, trust all certificates, skip hostname checks or click through WebView SSL errors. Use established TLS and the platform's random-number generation and key storage; no custom cryptography.

## Session rules

- Pairing secrets expire, are rate-limited and work only once. A device name alone never grants control.
- The companion keeps a **paired-device list with revoke**. Revoking closes any live session and releases output.
- Every controller connection is authorized. Secrets never appear in logs, screenshots or discovery broadcasts.
- One active controller owns output. A reconnect authenticates and starts **neutral and disarmed**, and queued input is never replayed.
- Arming output stays a host action for a selected game window. Stop, focus, timeout and phone-lifecycle release behave as they do today.

## Acceptance evidence required

These must be rejected:
- a wrong host, a changed key or an expired certificate;
- a replayed pairing secret;
- a revoked device;
- a second controller;
- malformed and rate-exceeding packets;
- hostile profile imports.

These must be verified on a real Windows PC and vivo phone:
- cleanup on focus loss, lock and network loss;
- key storage;
- dependency provenance;
- installer firewall scope;
- upgrade and uninstall.

Reference: [Android network security configuration](https://developer.android.com/privacy-and-security/security-config)
