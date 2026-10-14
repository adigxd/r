### VER-1.5-20261014192903
- Transparent blocks, per block and automatic: `atlas.py` reads the alpha of every tile of `atlas.png`; cutout tiles (every pixel solid or gone, like leaves) have their gone pixels cut out, translucent tiles (partly see-through, like glass) are drawn in a second pass with blending, sorted far to near (re-sorted whenever the camera moves half a block); a face is only hidden by a fully solid neighbour or by the same translucent block, and the frame's alpha stays 255 so screenshots don't get see-through spots; none of the blocks that exist today are see-through, so every existing scene renders exactly as before
- Fullscreen is a borderless window as big as the screen (the screen's own resolution, no video-mode switch, no black flicker) at startup and on F11; `WIDTH` / `HEIGHT` in `.env.pre` are only the windowed size, kept between 1280x720 and 3840x2160 (default is now 1280x720)
- Maple trees have their leaves again (the commented-out cube + sphere of `LEAF_MAPLE`)
- `maps/lights.json`: an example map with five different lights
- Removed the note about indexed drawing (skipped)

### VER-1.4-20261011211155
- `.env.pre` (tracked defaults) and an optional `.env` (yours, overrides `.env.pre`, not tracked) are back, for settings that are the same for every map: window, fullscreen, fps cap, view distance (`NEAR_CLIP` / `FAR_CLIP`), mouse sensitivity, mipmaps, texture atlas, shader files (`POST_FRAGMENT_SHADERS` is the list of post-processing shaders, in cycling order), audio and paths; map files keep what belongs to a map; unknown or wrong settings in either are reported
- Fullscreen can be toggled with F11 at any time (the frame buffer and projection are rebuilt for the new window size; the exit-on-focus-loss no longer triggers on the focus change a toggle causes); `FULLSCREEN` in `.env.pre` is the start state
- Lights: a map has `lights`, a list of 0 to 16 lights with their own `pos` / `follow_player`, `radius`, `intensity`, `color`, `falloff` (`linear` / `inverse_square`), `falloff_scale`, `snap` and `diffuse`; `lighting` holds ambient, `ambient_color`, `brightness`, `per_block` and `face_shade` per side; a map with the old single player-following light renders exactly like before
- Music is optional per map (`config.music`, a file in `MUSIC_DIR`)
- Mipmaps (`MIPMAPS`): far textures stop shimmering, near ones stay sharp; kept free of bleeding between neighbouring tiles
- Shapes: spheres, cylinders and cones take a `scale` to stretch them; cubes can be given as `x`, `y`, `z`, `size` (the old unfinished centered cube works for every size now); `WINDSWEPT` trees are a placeholder
- New dither (ordered Bayer dither, `post_dither.frag`); the old random one is `post_noise.frag`
- Removed: unused imports / functions / variables, the `threads` setting, the `gluPerspective` setup, the `ramp_color` lighting function, `opencv-python`, the commented-out debug prints
- Safety: a light exactly at the middle of the block being lit no longer normalizes a zero vector in the shader (undefined, could give garbage pixels)

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