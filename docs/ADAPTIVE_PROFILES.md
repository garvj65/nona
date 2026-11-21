# Game profiles

A **profile** tells NONA how to talk to a particular game. It has five parts:

| Part | Options |
|---|---|
| Name | Anything, such as *Roblox: Jailbreak* |
| Phone layout | Gamepad · Racing · Dual stick (Move & look uses the dual-stick layout as touch surfaces) |
| Output | Windows keyboard / mouse · Xbox 360 / XInput (optional) |
| Bindings | Phone action → keyboard key, or → Xbox button / axis |
| Tuning | Stick dead zone, sensitivity, invert Y · camera speed and right-button hold |

NONA doesn't read a game's control settings. You match them once and save the result.

## Built-in templates

| Template | Layout | Output |
|---|---|---|
| Gamepad · Arrows / WASD | Gamepad | Keyboard |
| Racing · Arrows / WASD | Racing | Keyboard |
| Platformer · Keyboard | Gamepad | Keyboard |
| Celeste Classic · Keyboard | Gamepad | Keyboard (arrows, X, C) |
| Roblox · Keyboard starter | Gamepad | Keyboard (WASD, Space) |
| Roblox · Mobile movement + look | Move & look | Keyboard + mouse |
| Mouse look · First person | Move & look | Keyboard + mouse, no right-button hold |
| Racing · Xbox analog | Racing | Xbox |
| Universal · Xbox dual sticks | Dual stick | Xbox |
| Roblox · Xbox candidate | Dual stick | Xbox |

Built-in templates are never overwritten. Editing one and saving creates your own copy.

## Make one for your game

1. Pick the closest template on the dashboard.
2. **Edit keys for your game** → match the game's keys → **Apply key mapping**. For Xbox output, use **Xbox device, bindings and tuning**. Leave a binding empty to turn that action off.
3. Adjust **Swipe camera settings** or stick tuning if needed.
4. **Save, export or import a game profile** → enter a name → **Save profile**. Use **Save copy** to fork one of your saved profiles.

The selected profile syncs to the phone automatically.

## Storage and sharing

- Saved to `%LOCALAPPDATA%\NONA\profiles.json`, outside the repository folder, so updates don't erase it. Choose another file with `run.py --profiles-file PATH`.
- Writes are atomic. If the file is unreadable, NONA leaves it untouched and blocks saving until you fix it or back it up.
- **Export JSON** produces a versioned file you can share. Importing checks the name, layout, output, every action and key, and the tuning ranges. A profile is pure data and can't run anything.
- Up to 100 saved profiles. There's no delete button yet.

## Safety

Switching profile, bindings, tuning or output **releases all input and disarms output**. You enable it again deliberately, so a held pedal can never carry over into a different game's controls.
