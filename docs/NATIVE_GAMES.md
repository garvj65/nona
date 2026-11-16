# From verified web racing to native games

The project owner confirmed **NONA Sprint and Jake Gordon's JavaScript Racer work on their Windows laptop with Android**. The next checks below establish native-game compatibility separately.

## First candidate: SuperTuxKart

Official download: https://supertuxkart.net/Download
Official requirements and input notes: https://supertuxkart.net/FAQ

SuperTuxKart is free, provides Windows builds, and supports keyboard/gamepad input. Start with low graphics settings and its benchmark; performance depends on the laptop. The official FAQ describes a fallback renderer for older hardware. This is a candidate, not a tested NONA result or a promise of performance.

### Start with the working keyboard path

1. Install and launch the game yourself from the official source.
2. In its input settings, configure steering, accelerate, brake, drift/handbrake and nitro to keys you want to use.
3. Choose NONA **Racing · Arrows** or **Racing · WASD**. Change NONA's bindings to match the game, including any extra actions.
4. Enable output, select the game window within four seconds, and drive a short offline race. Check simultaneous steering/gas, braking and key release.
5. Save the result as a named game profile and record the game version/settings. Loading that profile recalls its layout and bindings; output still starts disabled.

### Then try analog Xbox input

Complete GAMEPAD_SETUP.md and verify real controller detection first. Choose **Racing · Xbox analog** and connect the virtual device before starting the game. In the game's input settings, bind the left stick, triggers and action buttons to the corresponding actions. Some games expect acceleration on a button rather than RT; edit NONA's Xbox bindings or configure the game accordingly. Do not infer support from the gamepad tester alone.

## Second candidate: SuperTux

Official download: https://www.supertux.org/download

The official project provides Windows builds and controller support. Use **Platformer · Keyboard** and match the game's actual move/jump/action keys first. For controller input, choose **Universal · Xbox dual sticks** and configure its game bindings. This exercises a different game genre, without assuming that every racing profile fits a platformer.

## Record each result

For each tested game note: title/version, laptop CPU/GPU/RAM, Windows version, keyboard vs Xbox mode, saved NONA profile, game-side bindings, graphics settings, simultaneous controls, release/disconnect behavior, and whether a full round was playable.

Profile export contains the mappings and tuning, not the game or driver. It executes no commands and installs nothing. Prefer offline/free-play testing while establishing compatibility. Online hosting, online multiplayer and cross-play remain properties of the game.

Mouse-only games, games rejecting generated input, unsupported console/mobile-only titles, anti-cheat restrictions, and hardware requirements are outside what an input profile can solve. NONA does not bypass those boundaries.
