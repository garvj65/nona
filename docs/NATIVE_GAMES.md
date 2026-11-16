# Alternative compatibility targets

SuperTuxKart and SuperTux did not run on the project owner's laptop. They are blocked targets for that machine, not verified NONA integrations, and are no longer the default next step. Do not keep reinstalling them to validate the controller.

| Target | Purpose | Status |
|---|---|---|
| NONA Sprint | Local touch/tilt racing | Touch confirmed by owner; physical tilt is the next gate |
| JavaScript Racer | Existing online-hosted racing | Keyboard/phone play confirmed by owner; reuse for tilt |
| Celeste Classic | Browser platformer | Alternative candidate; published controls are arrows, X and C |
| TrackMania Nations Forever | Native racing | Alternative candidate, untested on this laptop |
| Roblox | Native client with many experiences | Next explicit test gate after physical motion succeeds |

## Celeste Classic

Creator page: https://maddymakesgamesinc.itch.io/celesteclassic . Choose NONA **Celeste Classic · Keyboard**: D-pad sends arrows, A sends X, B sends C. Focus the game iframe before enabling/using input. This avoids needing another native platformer installation, but responsiveness and gameplay still need a device test.

## TrackMania Nations Forever

Official publisher store: https://store.steampowered.com/app/11020/TrackMania_Nations_Forever/ . This is the free 2008 racer, not the newer Trackmania game. Its published minimum graphics requirement is DirectX 9.0c and memory requirement 256 MB; the present Steam client has its own modern OS requirements. Those old minimums are a reason to consider it, not a guarantee of launch compatibility with a current laptop.

Try offline solo play using the laptop keyboard first. If it runs, choose Racing · Arrows in NONA and match any bindings in the game's input settings. Test a short track, held gas+steering, braking, release and disconnect; then save the result. Add tilt only after ordinary controls work.

## Roblox

See ROBLOX_TEST.md. Current system requirements and experience-specific controller support must both be satisfied. Begin with a simple experience at low graphics, not an expensive or demanding game. Record the actual tested experience.

For every native test, note CPU/GPU/RAM, Windows version, game/client version, output mode, mappings, graphics settings, successful tasks, and failures. This iteration offers alternatives; it does not claim either native candidate runs on the owner's hardware.
