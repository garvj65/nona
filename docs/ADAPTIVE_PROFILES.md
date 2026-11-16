# How NONA adapts

A game profile contains five explicit choices: name, phone layout, output mode, bindings, and stick tuning. The phone sends normalized controls; the selected output adapter translates them into Windows keyboard state or an Xbox report.

| Game expects | Choose | Adaptation |
|---|---|---|
| Keyboard controls | Gamepad / Racing / Platformer keyboard preset | Map actions to the game's actual keys |
| Analog gamepad controls | Optional Xbox racing or dual-stick preset | Proportional sticks/triggers plus Xbox buttons |
| Different action buttons | Edit the active backend's bindings | Save the result under the game's name |
| Different stick feel | Adjust gamepad dead zone / sensitivity / right-stick Y | Save tuning with the profile |

NONA does not automatically discover or rewrite arbitrary game controls. A saved profile is how the app remembers the choices after you match them once. There is no process auto-switching, game launcher automation or keyboard/mouse emulation of right-stick aiming in 0.3.

## Save and reuse

Choose a preset, match the game's bindings, set output/tuning, enter a name and click **Save profile**. A built-in preset is copied into a new saved profile. Saving while a saved profile is selected updates it; **Save copy** duplicates it. Profile choices synchronize to the phone.

The normal launcher stores profiles at `%LOCALAPPDATA%\NONA\profiles.json` on Windows, outside the checkout so code updates do not erase them. An alternate file can be chosen with `--profiles-file PATH`. No profile file is written by imported test app instances unless a path is provided. At startup the active selection defaults to Gamepad · Arrows and output is disabled.

Export creates a versioned JSON file for the current bindings. Import validates its layout, output mode, allowed actions/targets, tuning and name, then creates a saved profile. Imported profiles cannot run commands. Templates are never overwritten. Writes replace the profile file atomically; an unreadable file remains untouched and saving is blocked until it is fixed or backed up. Up to 100 saved profiles are supported. There is no delete UI yet.

Changing a profile, bindings, tuning or backend clears current input and disables both output backends. A new enable action is required. This prevents a held pedal from carrying into a different game profile.
