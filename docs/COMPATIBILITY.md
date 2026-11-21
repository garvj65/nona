# Game compatibility

NONA replaces your **input device**. The PC still has to run the game, and the game decides what input it accepts. A game *verified* here has been played with NONA on real hardware. Everything else is a candidate until someone plays it.

## Results

| Game | Path | Status |
|---|---|---|
| **NONA Sprint** (built-in) | Wi-Fi, direct touch and tilt | **Verified**: touch and tilt racing |
| **Neon Run** (built-in) | Wi-Fi, direct buttons | **Verified** |
| **[JavaScript Racer](https://jakesgordon.com/games/racer/)** | Wi-Fi → keyboard bridge (Racing · Arrows) | **Verified**: touch and tilt steering |
| **Roblox** | Wi-Fi keyboard starter | **Partial**: moved and jumped in an obby, but the camera felt restricted |
| **Roblox** | Wi-Fi or Bluetooth Move & look | Candidate: next device test |
| **Roblox** | Virtual Xbox (Roblox · Xbox candidate) | Candidate: needs ViGEmBus |
| **[Celeste Classic](https://maddymakesgamesinc.itch.io/celesteclassic)** | Wi-Fi keyboard (Celeste Classic · Keyboard) | Candidate |
| **[TrackMania Nations Forever](https://store.steampowered.com/app/11020/TrackMania_Nations_Forever/)** | Wi-Fi keyboard (Racing · Arrows) | Candidate |
| **SuperTuxKart, SuperTux** | — | Blocked: they won't launch on the test laptop (a laptop problem, not a NONA one) |
| Other keyboard browser games | Wi-Fi keyboard with custom bindings | Usually works; check focus and bindings |
| Native Windows games | Wi-Fi keyboard, or the virtual Xbox pad | Varies; some anti-cheat or input systems ignore injected input |
| Console-only or mobile-only games | — | Not supported. NONA doesn't run console games. |

## Roblox

Roblox is a platform of experiences, and each experience picks its own controls. One experience working doesn't mean they all will.

1. **Check the laptop.** Roblox needs 64-bit Windows 10/11 and DirectX 10+ ([requirements](https://en.help.roblox.com/hc/en-us/articles/203312800-Computer-Hardware-Operating-System-Requirements)). Pick a simple experience, set the graphics low and play a minute with the laptop's keyboard and mouse first. Don't spend Robux on a compatibility test.
2. **Choose a route:**

| Route | Profile | Movement | Camera |
|---|---|---|---|
| Move & look | **Roblox · Mobile movement + look** | 8-way WASD | Swipe, plus optional gyro aim ([guide](MOBILE_CONTROLS.md)) |
| Virtual Xbox | **Roblox · Xbox candidate** | Analog left stick | Right stick (in experiences that support gamepads) |
| Keyboard starter | **Roblox · Keyboard starter** | WASD | None; use the laptop mouse |

3. **To pass:** a sustained session where you move, look and jump together, plus Stop, focus change and reconnect. Record the experience name or URL, PC specs, client version, profile and graphics settings.

Never modify the Roblox client or get around its restrictions. If an experience rejects an input route, record that and try another route.

## Browser and native candidates

- **Celeste Classic** (browser platformer): choose **Celeste Classic · Keyboard**, where the D-pad sends the arrow keys, A sends X and B sends C. Click inside the game's frame before enabling output.
- **TrackMania Nations Forever** (free 2008 racer, native): play offline with the keyboard first. Then use **Racing · Arrows** and match the game's input settings. Add tilt only after the basic controls work.

## Keyboard steering vs analog

The phone sends steering as a number from -1 to 1. **NONA Sprint** uses it directly. For keyboard games the companion presses left or right once steering passes **0.22** and releases below **0.12**; that gap (hysteresis) stops the key flickering at the threshold. A key is either pressed or not, so keyboard steering can't be truly proportional. The **virtual Xbox pad** keeps it analog. The **Bluetooth app** gets close by [pulsing the key](ANDROID_BLUETOOTH.md#controls).

## Multiplayer and cross-play

A game being hosted online doesn't make it multiplayer, and being available on several platforms doesn't mean cross-play. NONA adds no game servers, accounts, matchmaking, anti-cheat bypass or console compatibility; it only replaces the controller on a PC that can already run the game.

## Report a result

Record the game and its version or URL, PC CPU, GPU, RAM and Windows version, the path and profile used with any binding changes, the graphics settings, and whether press, hold, release, combined inputs, Stop, focus change and reconnect behaved. Add it to [VALIDATION.md](../VALIDATION.md). Only mark a game *verified* after actually playing it.
