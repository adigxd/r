### VER-2.4-20261025233333
- Fix: a long line in the chat was squeezed thin to fit the box while typing; now it goes on in more rows (the box grows upwards, breaking after a space when it can), the text keeps its size, and the caret is in the right row

### VER-2.3-20261024222808
- `python r.py` with no map now starts `heaven` (it was `parkour`; `python r.py parkour` still gives that)

### VER-2.2-20261024222706
- New map `heaven` (`python r.py heaven`): bright, abstract, no music; flat and hilly ground, big flat quartz fields, stepped platforms, a long roof on pillars, spires, two huge arches crossing over the middle, beams between the spires, floating islands, clouds and a ring in the sky, 57 pastel lights; exactly mirrored in x and in z (checked block by block: 970,000 blocks, none without its mirror image; the lights too)

### VER-2.1-20261024204549
- `COMMANDS.md`: a guide to every rend command (what it does, every form it takes, examples, and what its answers and mistakes mean); all 122 example commands in it were run to check that they work as written

### VER-2.0-20261021172542
- rend, the editing of the world in the game, and the chat it is typed into:
  - T opens the chat (JetBrains Mono, `chat.py`), Enter sends, Escape closes, Tab finishes a command name, Up / Down bring back what was sent, Page Up / Page Down scroll; the player stands still and the view doesn't turn while it is open, the physics goes on; a message stays `CHAT_FADE_TIME` seconds when the chat is closed; Right Shift is a letter while typing, not "exit"
  - a line that starts with `.` is a command (`rend.py`: `.pos1 .pos2 .sel .desel .set .replace .walls .hollow .sphere .cyl .copy .cut .paste .move .stack .undo .redo .save .tp .spawn .coords .clear .help`), anything else is a chat message shown as `<You> text` until there is multiplayer; unknown commands and mistakes are reported in red (with suggestions for a block name that is nearly right)
  - the selection is drawn in the world as a box (`selection.py`: cyan, orange and blue corners; faint through blocks)
  - undo / redo of any number of edits (kept compactly, 11 bytes a block, `REND_UNDO_BLOCKS`), limits for one command (`REND_MAX_BLOCKS`)
  - `.save` puts the edits into the map file as `"edits"`: what every command did, with the numbers worked out (corners, seeds of the random picks), played again after the shapes of the map when it is built, so the saved world is exactly the edited one (tested on 60 random command sequences); the rest of the file is left as it is, the old file is kept as `.bak`, and a file that would lose anything is never written
- `World.edit(changes)` changes blocks and remakes only the chunks that changed and their neighbours (the vertices of all other chunks are copied inside the graphics card), the mesh is exactly the one a fresh build gives (tested for solid and translucent blocks, also at the borders of chunks); `World.raycast` finds the block you look at
- A block with several textures (grass, dirt, sand) picks one from its position instead of from the random numbers of the build, so it looks the same whenever its chunk is made again (the look of the textures on the maps changes a little)
- Settings: `REND_MAX_BLOCKS`, `REND_UNDO_BLOCKS`, `CHAT_FONT`, `CHAT_FONT_SIZE`, `CHAT_LINES`, `CHAT_HISTORY`, `CHAT_FADE_TIME`, `CHAT_WIDTH`, and the shaders `UI_*` and `LINE_*`

### VER-1.16-20261018215714
- `COLLISION_STEP` is now 0.375 blocks (was 0.4); all collision and parkour route tests pass with it

### VER-1.15-20261018213440
- Escape (as well as Backspace) puts the player back at the spawn of the map
- Fix: collision at high speed. The old way of getting out of a block was to push the player out of it along the nearest side, so a player that went further into a block in one tick than half a block (50+ blocks per second, or a hard fall) was pushed out of the far side: phasing through walls and pillars, and being put on top of a pillar; falling fast onto a floor one block thick put the eye below the middle of the block and pushed the player down through it (from 500 blocks up)
- Now the player is moved one axis at a time in steps of at most `COLLISION_STEP` (0.4) blocks, and when a step ends inside a block the player is put back flat against the face it came from; nothing can be jumped over at any speed (tested against walls, a pillar from 16 angles, floors one block thick from 2000 blocks up, ceilings, sliding along a wall for 10 s, and 116 random worlds at up to 400 blocks per second: before 9 of 18 checks failed, now none); a player that ends up inside blocks anyway (teleported into a wall) is moved up out of them (`Camera.unstick`)
- Every route of the parkour map still passes

### VER-1.14-20261018212104
- More settings moved into `.env.pre` / `.env` (each explained there, checked when the game starts, and all wrong ones are reported at once): `LIGHT_FADE_TIME` (0.25 s, 0 = no fading), `LIGHT_FADE_SHARE` (0.125 of `MAX_LIGHTS` kept free for lights that fade out), `LIGHT_STICKINESS` (1.3), `LIGHT_CELL_SIZE` (64), `MAX_FRAME_TIME` (0.25 s, the longest freeze the physics catches up on), `CHUNK_SIZE` (16, a power of 2: renders pixel for pixel the same at 8, 16 and 32), `GLASS_SORT_DISTANCE` (0.5 blocks), `LOADING_BAR_FPS` (30) and `LOADING_BAR_WIDTH` (0.3 of the window)
- `LightSet`, `World` (`glass_sort_distance`), `LoadingBar` and `chunks.set_chunk_size` take these as arguments (with the same defaults), the module constants `CELL_SIZE` / `FADE_TIME` are gone
- Still in the code on purpose: the window size limits (1280x720 to 3840x2160), the look of the loading bar (colors, height), the 6 faces' shading (that is per map, `lighting.face_shade`)

### VER-1.13-20261018210530
- Fix: lights flickered when the map has more lights than `MAX_LIGHTS` (the parkour map has 300, 32 fit at a time): every frame the best 32 are picked, and as the camera moved the ranking changed and lights popped on and off; now a light that wins or loses a place fades in or out over 0.25 s (`LightSet.select` takes the time of the frame and gives every light a weight, `uniforms.set_scene` multiplies the intensity with it), a light that is already in has to be 30% worse than a newcomer to lose its place, and at most an eighth of the places (4 of 32) hold lights that are fading out, so at most that many lights change at a time (the others wait a few frames); lights that only start to touch the view and everything when all the lights fit are not changed (maps with few lights render pixel for pixel as before); on the parkour map flying along 4 routes: 738 pops of a light by half or more before, none now
- Why not just a bigger `MAX_LIGHTS`: every light the shader loops over costs about 0.12 ms at 1920x1080 on a 3070 (32 lights: 2.8 ms a frame, 64: 6 ms, 128: 15 ms)

### VER-1.12-20261018200920
- `python r.py` with no map now starts `parkour` (it was `1`; `python r.py 1` still gives the bright world)

### VER-1.11-20261018200351
- New map `parkour` (`python r.py parkour`): a giant bunny hop playground, 910,000 blocks and 300 lights, every block type in it; a 460 x 460 neon arena at night with a 260 block tall Needle in the middle (a spiral of 125 stepping stones up to the summit, a rest deck with a light every 40 blocks, floating rings around it), eight sprint / walk highways from the plaza up to eight districts (Redwood Canopy: giant trees with a spiral up the first trunk and canopy to canopy hops; Cathedral: a staircase of 2 high steps through a hall of pillars to floating rings; Floating Gardens: grass islands in a spiral; Aqueduct Skyline: walls of arches with gaps, a tower and a second wall; Pillar Desert: a spiral of sand pillars, dunes, palms, a pyramid and a floating sun; Cloud Archipelago: a ladder of pads into the sky, then clouds; Obsidian Ziggurat: a dark staircase of 2 high steps and a spire; Crystal Obelisks: a zigzag along the tops of white obelisks)
- The physics of the map are made for it: gravity 40, jump 14 (2.45 blocks high, 0.7 s in the air), speed 10 (a hop covers 7 blocks), sprint x2.5 (17.5 blocks); every route was played by a bot (a person's way of playing: W + Space held, aiming at the next pad, letting go of W to shorten a hop) on the real World and Camera: all 25 routes can be finished at walking speed (the highways also with sprinting)
- Starting the game with the map takes about 6 s (the loading bar shows it); Backspace puts you back at the start, a fall ends on the arena floor

### VER-1.10-20261017174401
- Alt-tabbing (or anything else taking the focus) no longer exits the game: it keeps running, nothing is paused, the mouse is let go and shown while another window has the focus, mouse movement over the game window doesn't turn the camera then, sprinting is switched off (a released right mouse button in another window never arrives), and the mouse is taken again when the focus is back; exit with Right Shift or the window's close button; the grace period that kept fullscreen switches from counting as lost focus is gone, it isn't needed any more

### VER-1.9-20261017152355
- Loading bar (`loading.py`): the window is shown right away, at its final size (a hidden window only goes fullscreen when it is shown, so nothing windowed flashes up), and a bar fills in the middle of a black screen while the map builds; `World.build` reports how far along it is (placing the shapes, then the faces of the mesh, counted in blocks), the bar is redrawn 30 times a second at most, costs about 0.2 s of a 2.8 s build, and needs no shader or texture (it clears small rectangles of the screen); closing the window, Right Shift or leaving the window works during loading too, and the mouse movement during loading doesn't turn the camera afterwards
- Map `1` is now a bright world of my own making (the old one is in git history): a meadow with flowers and hills, a white temple with pillars and a glowing altar, an aqueduct with carved arches, two log houses, pine / maple / redwood forests, a desert with dunes and palms, a snow-capped mountain, a striped lighthouse, a sand arch and a stepped pyramid, three glowing crystals, a floating island (reached by an 18 step staircase from the meadow; `jump_speed` is 9 so one block steps can be jumped), a block-built sun and puffy clouds, with 13 lights and no music

### VER-1.8-20261017141656
- Startup no longer flashes: the window is created hidden and is only shown once everything is loaded (map built, textures, shaders), directly at its final size and place; before, a windowed window with a title bar appeared for a moment before switching to fullscreen, and the fullscreen window then sat blank for as long as the map took to build (2.8 s on map 1); the first thing shown is a black frame, then the first real frame once the frame buffer has been fitted to the final size (while hidden, the window still reports its windowed size)
- A pygame without hidden windows just shows the window right away like before

### VER-1.7-20261017140232
- A map can have any number of lights (the limit of 16 per map is gone): every frame `LightSet.select` (`lights.py`) picks the lights that can light something visible (sphere of the light against the 6 planes of the view and `FAR_CLIP`, lights are sorted into 64 block cubes so only the cubes in view are looked at), always the lights that follow the player first, and if more than `MAX_LIGHTS` matter the brightest, biggest and closest win; picking is lossless (a render with picked lights is pixel-identical to sending every light of the map when `MAX_LIGHTS` fits them all)
- `MAX_LIGHTS` (32) in `.env.pre` is how many lights can light the screen at once; the shader array is sized from it when the shader is compiled (`glsl.with_defines`), limited to what the graphics card supports (`uniforms.light_capacity`: 141 on an RTX 3070), so there are no longer two numbers that have to match and a weak card can't fail to link the shader
- A one-time notice tells the map author when more lights matter than fit
- Cost: 10,000 lights take 0.4 ms per frame to pick from, 100,000 take 4.4 ms

### VER-1.6-20261014215937
- Chunk-based rendering with frustum culling: the mesh is cut into 16x16x16 chunks (`chunks.py`); all solid chunks share one GPU buffer and every frame only the chunks inside the camera's view (`matrices.frustum_planes`), and no further from the camera than `FAR_CLIP` (a sphere), are drawn in a single `glMultiDrawArrays` call; translucent chunks get their own buffers and are drawn and sorted far to near, chunk by chunk; the image is pixel-identical to drawing everything (map 1: 970 -> 1182 fps, a 1024x1024 world: 601 -> 847 fps, at 1920x1080 with the GPU's work included)
- Physics is decoupled from rendering: it runs in fixed ticks of 1/`TICK_RATE` s (64) (`ticks.py`, `Camera.tick`), mouse look stays per frame (`Camera.look`), and the camera is drawn blended between the last two ticks (`Camera.render_pos`); the same inputs give the same positions at any frame rate, jumps are exactly the designed height (exact gravity maths), and falling through floors at low frame rates is gone
- Fullscreen / resolutions: the size of the window is checked every frame and the frame buffer and projection are rebuilt whenever it changes (works the same on every platform and for any resolution or aspect ratio); on Windows the game turns on DPI awareness (no blurry stretching on screens scaled above 100%); the windowed size is never bigger than the screen; the dither cell size scales with the screen height
- Removed `World.get_mesh` / `get_translucent_mesh` (replaced by `draw_opaque` / `draw_translucent`) and `Camera.update`

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