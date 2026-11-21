# Virtual Xbox controller (optional)

Some games only take real controller input. With this optional backend, the companion creates a **virtual Xbox 360 controller** on Windows, with analog sticks, analog triggers and every button. Keyboard output and the built-in demos don't need it.

| | |
|---|---|
| **Profiles** | **Racing · Xbox analog** · **Universal · Xbox dual sticks** · **Roblox · Xbox candidate** |
| **Needs** | Windows, the `vgamepad` Python adapter and the ViGEmBus driver |
| **Status** | CI-tested with a mocked driver; not yet tested in a real game ([validation](../VALIDATION.md)) |

> [!WARNING]
> **ViGEmBus is retired.** Version 1.22.0 is its final upstream release. Its author archived the project in 2023, so there are no updates and future Windows compatibility isn't guaranteed. NONA keeps the backend isolated so it can be swapped for a maintained one later. NONA never installs, updates or removes the driver; you decide whether to install it.
> [Final release](https://github.com/nefarius/ViGEmBus/releases/tag/v1.22.0) · [End-of-life notice](https://docs.nefarius.at/projects/ViGEm/End-of-Life/) · [Install / remove](https://docs.nefarius.at/projects/ViGEm/How-to-Install/)

## Set up

1. Run `START_WINDOWS.bat` once so the Python environment exists, then close it.
2. Run **`SETUP_XBOX_OUTPUT.bat`**. It installs `vgamepad==0.2.0` with `VGAMEPAD_SKIP_VIGEMBUS_INSTALL=true`, which stops the package's old bundled driver installer from running. Don't `pip install -r requirements-gamepad.txt` without that variable set.
3. If you choose to, download the official ViGEmBus 1.22.0 installer from the link above, review it and run it yourself. Restart if asked. Skip this if a working copy is already installed.
4. Start NONA, pair the phone and choose an Xbox profile.
5. Dashboard → **Xbox device, bindings and tuning** → **Connect Xbox device**. *Connected* means a virtual device was created, not just that the package is installed.
6. Open **Controller diagnostics**, click **Enable output** and click that window within 4 seconds. Press A or move a stick on the phone. The *browser-detected gamepad* panel should show live input. `Win+R → joy.cpl` works too.
7. For a real game, **connect the virtual device before launching the game** so the game sees it. Then enable output and focus the game.

## Layouts

| Profile | Mapping |
|---|---|
| **Racing · Xbox analog** | Wheel or tilt → left stick X · Gas → RT · Brake → LT · Handbrake → X · Nitro → A |
| **Universal · Xbox dual sticks** | Two analog sticks · A/B/X/Y · LB/RB · LT/RT sliders that spring back · Start · Select = Back |

Under **Xbox device, bindings and tuning** you can rebind buttons and tune the sticks (dead zone, sensitivity, invert right-stick Y), then save the result as a [profile](ADAPTIVE_PROFILES.md). Racing pedals press their trigger fully. Steering stays analog.

## Failure handling

Changing a profile, binding, output mode or tuning, or tapping **Stop**, disconnecting, timing out, losing focus or shutting down, returns the pad to neutral and disarms output. If the driver rejects a neutral report, NONA keeps retrying while it runs. If the Xbox device won't connect, the dashboard says why; pick a keyboard profile to carry on without it.

The diagnostics page shows two panels: what the companion **received** from the phone (left) and what the browser **detected** as a gamepad (right). NONA never fakes `navigator.getGamepads()`.
