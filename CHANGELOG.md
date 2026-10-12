### VER-1.3-20261011203308
- Everything renamed to plain snake_case words (`blc_arr` -> `blocks`, `_CAM_SET` -> `update`, `__MAP__` -> `World`, ...); no behavior change (screenshots of 3 maps x all post-processing effects x wireframe are pixel-identical before / after)
- Files: `cam.py` -> `camera.py`, `cfg.py` -> `config.py`, `dbg.py` -> `log.py`, `map_.py` -> `world.py`, `buf.py` -> `buffers.py`, `mat.py` -> `matrices.py`, `sha.py` -> `glsl.py`, `uni.py` -> `uniforms.py`, `req.txt` -> `requirements.txt`, `DIR-Changelog/README.md` -> `CHANGELOG.md`
- Folders: `DIR-Maps` -> `maps`, `DIR-Shaders` -> `shaders`, `DIR-Resources` -> `resources`, `DIR-Music` -> `music`, `DIR-Screenshots` -> `screenshots`
- Assets: `IMG-Texture.png` -> `atlas.png`, `IMG-WIN.png` -> `icon.png`; shaders are now `block.vert` / `block.frag` / `post.vert` / `post_default.frag` / `post_edge.frag` / `post_dither.frag`, and their uniforms / varyings follow `u_` / `a_` / `v_` prefixes
- Map files: lowercase keys (`name`, `description`, `config`, `world`); settings renamed (`RES_X` -> `width`, `SEN` -> `mouse_sensitivity`, `ACC_D` -> `gravity`, `TIC` -> `max_fps`, ...) and `DBG_KIN` is now `fly` (true / false); shapes use `radius`, `height`, `blocks`; `axs` is `"axis": "y" | "x" | "z"`, `flp` is `"flip": true | false`, `shp` is `"shape": "circle" | "square"`
- `log.error('title', key=value)` replaces `_DBG(tag, [keys], [values])`
- Fix: `Camera` no longer shares one default `rot` list between instances

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