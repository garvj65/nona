# Game compatibility

NONA supplies inputs. The laptop and game still determine performance and platform support.

| Target | Current integration | Evidence / next check |
|---|---|---|
| Original Neon Run | Direct WebSocket state | User reported working Windows + Android gameplay in the 0.1 starter; protocol kept compatible |
| NONA Sprint | Direct button state plus proportional steering | Racing physics and protocol tests; use the included device acceptance checks |
| Jake Gordon's JavaScript Racer | Racing · Arrows keyboard bridge | Official live page and published source specify arrow controls; requires a physical Windows gameplay check |
| Other keyboard-controlled websites | Racing/Gamepad presets plus editable bindings | Per-game focus, bindings and input acceptance must be checked |
| Windows-native games accepting keyboard input | Same Windows keyboard bridge | Candidate path, not blanket verified support; some input systems reject injection |
| Gamepad-only titles | Future virtual gamepad adapter | Not implemented |
| Console/mobile-only games | No port or emulator is supplied | A supported Windows/browser version is needed; NONA does not run console games |

## First external racing target

- Play: https://jakesgordon.com/games/racer/
- Author's simpler straight-track version: https://jakesgordon.com/games/racer/v1-straight/
- Source: https://github.com/jakesgordon/javascript-racer

Start at low rendering resolution and draw distance if needed. Choose Racing · Arrows in NONA. Its Gas pedal sends Up, Brake sends Down, and the wheel sends Left/Right. The game source also includes WASD aliases. Third-party code/assets are not bundled into this repository.

Source-level compatibility is not a successful device test: record your result after actually driving with the phone. If the game ignores input, verify Notepad first, then focus its canvas. Use the built-in NONA Sprint as the network/controller check.

## Analog vs keyboard steering

The phone sends a normalized steering value in [-1, 1]. NONA Sprint reads that value directly. For keyboard games, the server engages a direction at 0.22 and releases it below 0.12; opposite steering switches direction. This prevents jitter around the threshold. A keyboard event cannot express a proportional stick position. Future analog support requires a virtual-device backend or cooperation from the game.

## Online and cross-platform multiplayer

A game being hosted online does not mean it supports multiplayer. A multiplayer game being available on several platforms does not mean it supports cross-play. NONA's current role is to replace keyboard input on a Windows machine already able to run the game. It adds no game server, account entitlement, matchmaking, anti-cheat bypass or console compatibility layer.

The companion currently injects keys only on Windows. The built-in demos can run on other desktop OSes, but their native input adapters are not implemented. An Android APK is not required for the existing browser controller.

## Record a real compatibility result

For each game note: game/version or URL, laptop CPU/GPU/RAM, Windows/browser version, chosen preset and overrides, whether press/hold/release works, whether steering plus gas works, performance settings, and connection/focus behavior. Mark it verified only after playing it. This is the evidence to collect before promising broad support.
