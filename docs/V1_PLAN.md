# Accepted direction and release gates

## Product goal

NONA v1: a PC-friendly Android controller. Android supplies touch and motion input; the Windows companion delivers compatible keyboard/controller output. The current 0.4 branch is a browser-based motion prototype, not the packaged v1 release.

## Ordered gates

1. **Motion prototype:** implement calibration, orientation-aware tilt, touch fallback, neutral-on-loss and an HTTPS path. Pass automated tests, then physically test on the owner's Android/Windows setup using NONA Sprint and the already-working JavaScript Racer.
2. **Roblox compatibility:** confirm Roblox runs on the laptop, test a simple experience through the keyboard profile, then the Xbox route for movement/camera where supported. Record the exact experience and results.
3. **Refine and validate:** use measured latency, drift, usability and failure results to adjust the input path; review the implementation and dependencies. Do not infer broad compatibility from one game.
4. **Security checks:** perform the requested code/security review before release, including pairing/origin boundaries, key/axis release, profile import, transport/certificate handling, optional native dependencies, update/install behavior and mobile lifecycle. Track actual findings and verify fixes. No completed security-audit claim is made by this plan.
5. **Package v1:** build the Windows companion and Android application, then test actual installation, pairing, upgrades and uninstall. The Android app should use app-scoped certificate trust/pinning and avoid requiring a device-wide prototype CA. Validate the final bundles on real devices before naming them v1.

Physical steps cannot be substituted by simulated sensor or controller tests. No v1 APK or Windows release bundle is published from this motion-prototype iteration.

## Separate later product: phone instead of DualSense

After the PC version, explore a separate Remote Play controller bridge using a real owned PS5, a legitimate account and a supported game. The phone replaces the input controller; the actual PS5 runs the game. Test on the friend's console with permission. This is not PS5 emulation or replacing the console's hardware. Keep its transport, game support, latency and controller requirements independently verified.
