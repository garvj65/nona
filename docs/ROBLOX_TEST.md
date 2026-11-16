# Roblox test gate, after physical tilt passes

Roblox is a native Windows client/platform containing many experiences. The fact one experience works does not prove every experience has the same controls. Roblox's official docs support keyboard/mouse and Xbox/PlayStation gamepad input; experience authors choose and may customize bindings.

## Check the laptop first

Roblox currently requires 64-bit Windows 10 or Windows 11 and DirectX 10 or higher feature-level graphics support. See the current official requirements: https://en.help.roblox.com/hc/en-us/articles/203312800-Computer-Hardware-Operating-System-Requirements . A failed SuperTuxKart launch does not tell us whether Roblox will run. If needed, check Windows `dxdiag` and the CPU/RAM information before installing more games.

Install Roblox from https://www.roblox.com/ if you choose to test it. Sign in yourself, choose a simple experience, lower graphics initially, and confirm it plays normally using the laptop's own keyboard/mouse first. Do not spend Robux or buy an experience for this compatibility test.

## Keyboard starter profile

The owner tried an unnamed obby on 2026-11-16: keyboard controls worked, but movement and camera felt restricted. No experience URL or independent laptop frame-rate result was supplied. The old starter does not supply mouse camera control. For the next test use **Roblox · Mobile movement + look**, described in MOBILE_CONTROLS.md; its new mouse/gyro route still requires physical Roblox verification.

Choose **Roblox · Keyboard starter**:

- D-pad: WASD movement.
- A: Space/jump.
- B: Shift; X: E; Y: Q. These are optional, experience-specific actions, not universal Roblox commands.
- Start: Esc/menu; Select: Tab.

Enable NONA output and select the Roblox client within four seconds. Check move, stop, move+jump, focus loss and disconnect. This keyboard starter does not emulate a mouse: camera operation still uses your laptop mouse. Match any experience-specific actions in the profile editor and save them.

## Xbox candidate profile

If the optional Xbox adapter/driver is installed and verified in NONA's controller tester, choose **Roblox · Xbox candidate**. Connect the device before launching the client. In an experience that supports gamepads, left stick commonly moves, right stick commonly controls the camera and A commonly jumps. Those are Roblox's common control schemas, not a guarantee for every experience.

Test both sticks, move+jump, camera, menus, triggers, release, focus changes and reconnect. Controller support is experience-dependent. Do not bypass restrictions or change the Roblox process to force compatibility. If input is rejected, record that outcome and use a supported input route.

## Motion inside Roblox

Test normal controls first. For a racing experience, choose a Racing profile and map the wheel/tilt output to the inputs that specific vehicle accepts. Global tilt steering does not automatically become meaningful character movement or camera control in every experience. Gyro aiming and automatic per-experience adaptation are separate future features.

## Pass criteria before v1

Record the experience URL/name, laptop specifications, client version, chosen profile, graphics settings, inputs tested, a sustained playable session and disconnect behavior. At minimum, complete a simple movement/jump task and verify camera operation for the full-controller route. Have a working physical motion result and a working Roblox result before moving to the v1 review/security/packaging gate in V1_PLAN.md.

The owner's report establishes partial keyboard compatibility in one unnamed experience. It does not establish a smooth full-controller experience, physical Xbox compatibility or a pass for the new mouse/gyro route. CI does not run Roblox gameplay.

Primary references: https://create.roblox.com/docs/input/gamepad · https://create.roblox.com/docs/input/mouse-and-keyboard
