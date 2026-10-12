### VER-1.2-20261011201924
- All settings moved from `.env` / `.env.pre` into the `CONFIG` block of each map file in `DIR-Maps`; `.env`, `.env.pre` and `python-dotenv` removed
- New `cfg.py` loads and validates a map file (missing / invalid settings are reported and the game exits instead of crashing later)
- Map is picked on the command line: `python r.py [map]` (default `1`); `DIR_MAP` is now a constant in `cfg.py`
- Hidden block faces are no longer generated (map `1`: 9.6M -> 3.3M vertices, startup 6.1s -> 2.7s, peak memory ~2GB -> ~0.5GB)
- Map vertex data is built in a compact float32 array instead of a Python list
- Fix: GPU buffers of the previous map mesh were never freed on rebuild
- Fix: wireframe toggle (Right Ctrl) drew the post-processing quad as lines and was a frame late; it now only affects the scene
- Fix: shader link failure crashed with `dbg.__DBG`; failed shader compiles are now detected, and a missing post-processing shader no longer breaks effect cycling
- Fix: music failing to load is now printed instead of silently ignored; `PTH_MSC` pointed at a folder instead of a file
- Fix: `__MAP__` ignored its `blc_siz` / `tex_siz` arguments and read module constants instead

### VER-1.1-20260427030155
- ...

### VER-1.0-20260411000000
- ...

### ALF-20260404000000
- Forked from [Voxelbulb](https://github.com/adigxd/Voxelbulb)