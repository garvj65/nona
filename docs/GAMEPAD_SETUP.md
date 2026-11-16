# Optional Xbox / XInput output

NONA 0.3 can create an Xbox 360-style virtual controller through `vgamepad` on Windows. Keyboard mode and the included demos work without this option.

## Dependency status

The Windows backend uses **ViGEmBus 1.22.0**, the final upstream release. The author retired and archived ViGEmBus in 2023; it receives no upstream updates and future Windows compatibility is not guaranteed. NONA isolates this adapter so another backend can replace it later. This release does not use an unsigned experimental driver or require disabling Windows protections.

Official references:

- Final driver release: https://github.com/nefarius/ViGEmBus/releases/tag/v1.22.0
- End-of-life statement: https://docs.nefarius.at/projects/ViGEm/End-of-Life/
- Installation/removal: https://docs.nefarius.at/projects/ViGEm/How-to-Install/
- Python adapter: https://github.com/yannbouteiller/vgamepad

## Setup on your laptop

1. Run the normal NONA launcher once so its Python environment exists, then close NONA.
2. Run **SETUP_XBOX_OUTPUT.bat**. It installs the optional `vgamepad==0.2.0` Python adapter and sets `VGAMEPAD_SKIP_VIGEMBUS_INSTALL=true`, preventing the package's older bundled-driver installer hook from running. Do not install `requirements-gamepad.txt` directly without that environment variable.
3. If you choose to use the legacy driver, download its final installer from the official release linked above. Review and run it yourself, follow its Windows prompts, and restart if requested. NONA does not download, install, upgrade or remove the driver for you. If an existing installation works, do not install a second copy.
4. Start NONA again. Pair your phone and choose **Racing · Xbox analog** or **Universal · Xbox dual sticks**.
5. On the laptop, click **Connect Xbox device**. A connected device means the adapter successfully created a target, not just that the Python package exists.
6. Click **Test controller**. Click **Enable output** on the dashboard and select the tester window within four seconds. Press A or move a stick on the phone while the tester is selected. Its browser-detected gamepad section should list a controller and live axes/buttons. Windows can also test it with **Win+R → joy.cpl**.
7. Connect the virtual controller before launching a native game, so the game can enumerate it. Enable output and select the game window within four seconds. Configure the game's controller bindings if required.

The browser Gamepad API may initially hide a device until an input occurs with the page selected. Host-received phone data on the left of the tester is different from the gamepad detected by the browser on the right. NONA never injects a fake `navigator.getGamepads()` implementation.

## Profiles and layouts

- **Racing · Xbox analog:** wheel → left-stick X; Gas → right trigger; Brake → left trigger; Handbrake → X; Nitro → A. Bind these to the corresponding actions in the game.
- **Universal · Xbox dual sticks:** two proportional sticks, A/B/X/Y, LB/RB, LT/RT trigger sliders, Start and Select/Back.
- Edit Xbox button bindings and stick tuning on the dashboard. Bindings are explicit; NONA does not read arbitrary games' private settings or automatically infer their controls.
- Save the result under the game's name. It then appears on both laptop and phone, including after restarting NONA.

Trigger sliders spring back to zero on release; shoulder/face buttons are full digital presses. Racing pedals currently press their mapped trigger fully; wheel steering remains analog. Trigger/stick packets can carry intermediate values. Dead zone and sensitivity tune gamepad stick output; right-stick Y can be inverted. Keyboard mode uses digital direction thresholds instead.

## Failure handling

Changing profiles, bindings, output modes, or tuning disables output and returns both backends to neutral. Disconnect, timeout, focus change and normal shutdown do the same. The phone's **Release / stop** button disarms output; re-enable from the laptop to continue.

If Xbox output cannot connect, the dashboard reports the failure. Select a keyboard preset to continue without the optional backend. A driver disconnect or rejected neutral report may require reconnecting the device; NONA retries neutralization while running. Abrupt termination cannot promise cleanup. Focus is locked to a Windows window, not a browser tab.

Physical Windows controller recognition and gameplay are device acceptance checks. CI uses fake gamepad backends to verify report construction and lifecycle, not a real installed driver.
