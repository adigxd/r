# r

### What?

The best voxel engine ever

### CLI:

```
pip install -r requirements.txt
python r.py [map]
```

`map` is a file in `maps` (with or without `.json`); default is `heaven` (see below); `parkour` is the bunny hop playground and `1` is a bright daytime world to explore (meadow, temple, village, forests, desert, mountain, lighthouse and a floating island you can walk up to by the staircase). While a map builds, a loading bar fills in the window.

`python r.py heaven` is a bright abstract world with no music: flat and hilly ground, large quartz fields, spires, two huge arches and a ring in the sky, mirrored in x and in z (every quarter is a reflection of the others).

`python r.py parkour` is a giant bunny hop playground: hold W + Space to hop (a jump rises 2.4 blocks), hold the right mouse button to sprint (needed to cross the highway gaps fast, they can be walked as well), Backspace puts you back at the spawn. Climb the Needle in the middle (a spiral of stepping stones, 125 hops up), or take a highway to one of eight districts; falling just puts you on the arena floor.

### Keybinds:

| Key | Use |
| --- | --- |
| W / A / S / D | Move forward / left / backward / right |
| Mouse move | Look around |
| Right mouse button | Hold to increase movement speed |
| Space | Fly up in debug mode; jump in normal mode |
| Left Shift | Fly down in debug mode |
| Backspace | Back to the spawn of the map (not while typing in the chat or in the menu, where it deletes a letter) |
| T | Open the chat (Enter sends, Escape closes, Tab finishes a command name, Up / Down bring back what you sent, Page Up / Page Down scroll) |
| F11 | Toggle fullscreen |
| Backslash (`\`) | Next shader (Shift + Backslash: the previous one), round and round: the built-in ones, then yours |
| `]` | Open / close the menu of effects (the mouse becomes a pointer while it is open) |
| Backquote (`` ` ``) | Save screenshot |
| Right Ctrl | Toggle wireframe debug mode |
| Right Shift | Exit (not while the chat is open: it is a letter there) |

Alt-tabbing away doesn't close the game: it keeps running, lets go of the mouse, and takes it back when you come back.

### Settings:

There are two places, depending on whether a setting belongs to *you* or to *a map*:

- **`.env.pre`** has everything that is the same for every map (window size, fullscreen, fps cap, physics catch-up limit, view distance, how many lights at once and how they fade, chunk size, loading bar, mouse sensitivity, mipmaps, texture atlas, shader files, audio, ...) with a comment on each line. It is always read, so the game runs with nothing else. To change something for yourself, make a file called `.env` (not tracked by git) with just the lines you want different, for example `WIDTH=1600` and `MUSIC_VOLUME=0.1`; any line in `.env` replaces the same line in `.env.pre`, and everything you leave out stays as in `.env.pre`. You never have to copy `.env.pre`.
- **The map file** (`maps/<map>.json`) has everything that belongs to that map: `config` (seed, spawn, background, physics, speed, optional `music`), `lights`, `lighting` and `world` (the blocks). `config.py` lists every key and what it does.

If a setting is missing or has a typo, the game says which one and exits.

**Window and fullscreen:** `WIDTH` and `HEIGHT` are the size of the window when it isn't fullscreen (kept between 1280x720 and 3840x2160, and never bigger than your screen). Fullscreen ignores them: it is a borderless window as big as your screen, at your screen's own resolution, so the monitor never switches video mode (no black flicker). F11 switches at any time. Any resolution and aspect ratio works (the field of view is vertical, so a wider screen just shows more to the sides), and on Windows the game tells the system to use real pixels, so it isn't stretched blurry on a screen with display scaling above 100%.

**Physics and frames:** the physics (movement, gravity, jumping, collisions) runs at `TICK_RATE` updates per second (64) no matter how many frames per second are drawn, so the game plays the same on a slow and a fast computer; the frames in between are drawn smoothly blended between two physics steps, and turning with the mouse happens every frame.

**Chunks and view distance:** the blocks are drawn in chunks of 16x16x16. Every frame only the chunks inside the camera's view, and no further away than `FAR_CLIP` (a sphere around the camera, 4096 by default so you only notice it if you lower it), are sent to the graphics card.

### Maps:

```json
{
    "name": "my map",
    "description": "...",
    "config": { "seed": 1, "start_pos": [0, 2, 0], "background_color": [0, 0, 0], "fly": false, "gravity": 24, "jump_speed": 6, "speed": 8, "sprint_multiplier": 4, "player_width": 0.5, "player_height": 1.5, "music": "1.mp3" },
    "lights": [ ... ],
    "lighting": { ... },
    "world": { ... }
}
```

- `music` is optional, it is a file in the `MUSIC_DIR` folder from `.env.pre`; a map without it is silent.
- **`lights`** is a list of as many lights as you like (none, a few, thousands), each with its own settings (only `radius` is needed, and `pos` unless it follows the player):

```json
{"pos": [10, 4, 0], "radius": 14, "intensity": 1.5, "color": [1.0, 0.2, 0.2], "falloff": "inverse_square", "falloff_scale": 0.3, "snap": true, "diffuse": 1.0}
{"follow_player": true, "pos": [0, 1, 0], "radius": 16, "color": [0.5, 0.875, 1.0]}
```

  `follow_player` makes `pos` an offset from the player, `snap` puts the light in the middle of its block, `diffuse` is how much the angle of a surface matters (0 to 1), `falloff` is `"linear"` or `"inverse_square"`. There are no shadows (light goes through walls), and a light inside a block doesn't light that block's own sides. `python r.py lights` is a map with five different lights to look at and fly around.

  A map can have any number of lights, but the graphics card can only light with a few at a time (`MAX_LIGHTS` in `.env.pre`, 32 by default, and fewer on a card that can't take that many). So every frame the game picks the lights that can light something you can see (a light behind you still counts if it reaches things in front of you, and lights further away than `FAR_CLIP` don't); if more than `MAX_LIGHTS` of them matter, the brightest, biggest and closest win, and the game tells you once that lights are being left out. Lights that win or lose a place that way fade in or out over a quarter of a second (`LIGHT_FADE_TIME`; and a light that already has a place has to be `LIGHT_STICKINESS` = 1.3 times worse than a newcomer to lose it), so lights don't flicker as you move; an eighth of the places (`LIGHT_FADE_SHARE`) are kept free for lights that are fading out. Lights that follow the player are always used. A light that can't be seen costs the graphics card nothing; the only cost is a little time per frame to look through all the lights (about 0.4 ms for 10,000 lights, 4 ms for 100,000), so a map with thousands of lights runs about as fast as one with a few.
- **`lighting`** is everything that isn't one light, all optional: `ambient`, `ambient_color`, `brightness`, `per_block` (light whole blocks or single pixels) and `face_shade` (how bright each side of a block is: `top`, `bottom`, `front`, `back`, `left`, `right`).
- **`world`** has `voxels`, `cubes`, `spheres`, `cylinders`, `cones`, `trees` and `forests`; block names are in `world.py`.
  - A cube is either its edges (`x_min` ... `z_max`) or its middle and size (`x`, `y`, `z`, `size`; `size` can be one number or `[x, y, z]`).
  - Spheres, cylinders and cones can have a `scale` to stretch them along x / y / z: `"scale": [2, 1, 1]` is twice as wide in x (a sphere becomes an ellipsoid, a cylinder an elliptical one).

### Customization:

- Create your own map in `maps` ... run it with `python r.py <map>`
- Edit the textures in `resources/atlas.png`
- A new block needs a spot in `world.py` (`BLOCK_TYPES`) that points at its tile(s) in the atlas
- **Transparent blocks** need nothing but the picture: draw the tile in `atlas.png` with an alpha channel and the block is see-through, per block, automatically (`atlas.py` looks at every tile):
  - a tile whose pixels are either fully solid or fully gone (leaves, fences, ...) is a *cutout*: drawn like any other block with the gone pixels cut out
  - a tile with partly see-through pixels (glass, water, ...) is *translucent*: blended with what is behind it; a face between two blocks of the same translucent type is not drawn, and a solid block next to glass keeps its face
  - the tile row 0 is the bottom row of the png (the atlas is uploaded upside down)

### Files:

| File | What |
| --- | --- |
| `r.py` | Entry point: window, main loop, post-processing, fullscreen |
| `config.py` | Loads `.env.pre` / `.env` and a map file, and checks all of it |
| `world.py` | Blocks, shapes / trees, and the block mesh (solid and translucent) |
| `atlas.py` | Works out which tiles of the texture atlas are see-through |
| `camera.py` | Mouse look, physics ticks, collisions |
| `ticks.py` | Runs the physics at a fixed rate whatever the frame rate is |
| `chunks.py` | The 16x16x16 chunks and which of them can be seen |
| `matrices.py` | Model / view / projection matrices, and the 6 planes of the camera's view |
| `buffers.py` | OpenGL vertex buffers and the frame buffer |
| `glsl.py` | Shader loading and compiling |
| `lights.py` | Picks the lights that matter every frame (a map can have any number) |
| `loading.py` | The loading bar shown while the map builds |
| `rend.py` | The editing commands (`.set`, `.undo`, ...), what they do to the blocks, undo / redo and saving the edits into the map file |
| `chat.py` | The chat: typing, messages and drawing them (in JetBrains Mono) |
| `uidraw.py` | Draws rectangles and text over the picture (the chat and the menu of effects share it) |
| `effects/` | The menu of full-screen effects: every effect is a piece of GLSL with its settings (`color.py`, `retro.py`, `blur.py`, `edges.py`, `distort.py`, `overlay.py`); `python -m effects` writes `SHADERS.md` |
| `fx.py` | The effects on the screen (the stack, with undo), how typed values are understood, and the library of shaders (built in and yours) |
| `fxcommands.py` | The chat commands `.fx` and `.shader` |
| `fxrender.py` | Draws the stack: one full-screen pass after another |
| `gui.py` | The menu of effects (`]`) |
| `selection.py` | Draws the box of the rend selection |
| `uniforms.py` | Shader uniform values (matrices, lights, ...) |
| `log.py` | Console logging |
| `.env.pre` | Default settings for every map |
| `maps/` | Map files (their settings, lights and blocks) |
| `shaders/` | `block.*` (the world), `post.vert` (the full-screen quad of the effects), `ui.*` and `line.*` (chat, menu, selection), `defaults.json` (the built-in shaders) and `custom/` (yours, made in the game) |
| `resources/` | Texture atlas, window icon, music, the chat font |
| `COMMANDS.md` | Guide to every rend command, with examples |
| `SHADERS.md` | Guide to the shaders: every command, every effect and every setting |
| `CHANGELOG.md` | Version history |

### Shaders (the look of the picture):

The whole picture goes through a **shader**: a stack of effects (about 100: colors, dithering, blur, edges, bending, vignette, weather, ...) that you build in the game, with no code. **Backslash** goes through every shader (46 are built in, from `default`, the picture as it is, to `crt`, `vhs`, `noir`, `halftone`, `underwater` ...; yours come after them), **`]`** opens a menu to build one with the mouse, and the chat commands do the same:

```
.fx add vignette amount=0.6      an effect on top of the stack
.fx add dither bayer8 4 2        the same, with only the values (in the order .fx info dither lists them)
.fx up 1                         the order matters: move it up (applied after more of the others)
.shader save my-look             keep it: it joins the list Backslash goes through, on every map
.fx clear                        nothing on the screen
```

**[SHADERS.md](SHADERS.md) has the guide: every command, every effect with all its settings, the built-in shaders, and the file format of your own.** The shaders are not tied to a map.

### Rend (editing the world in the game):

Press T and type a command that starts with a `.` (anything else you send is a chat message, shown as `<You> ...` until there is multiplayer). `.help` lists the commands, `.help <command>` explains one. **[COMMANDS.md](COMMANDS.md) has a guide with examples for every command.**

- **Selecting:** `.pos1` and `.pos2` set the two corners, with nothing after them to the block you stand in, with `look` to the block you look at, or with `x y z` (`~` is relative to you, `~5` is 5 away). The box shows in the world (cyan; orange and blue corners). `.sel` says what is selected, `.desel` forgets it.
- **Blocks:** `STONE`, `STONE,DIRT` (equal chances) or `GRASS:60,STONE_LIGHT:1` (weights); `AIR` takes blocks away. Names are not case sensitive, a wrong one gets suggestions.
- **Changing:** `.set <blocks>`, `.replace <from> <to>` (`*` is every block), `.walls <blocks>`, `.hollow`, `.sphere <blocks> <radius> [hollow] [at x y z]`, `.cyl <blocks> <radius> <height> [hollow] [at x y z]`.
- **Copying:** `.copy`, `.cut`, `.paste [noair]` (put down relative to where you stand), `.move <distance> <direction>` or `.move dx dy dz`, `.stack <count> [direction]` (directions: up, down, north, south, east, west; north is the way you face at the start).
- **Undo:** `.undo [n]` and `.redo [n]` go through everything you changed; a new edit throws the redo steps away. Undo remembers as many blocks as `REND_UNDO_BLOCKS` allows, the oldest steps are forgotten first.
- **Other:** `.tp x y z`, `.spawn`, `.coords`, `.clear`.
- **Keeping edits:** `.save` puts everything you did into the map file as `"edits"` (a short list of what each command did, not all the blocks), so `python r.py <map>` builds the same world next time; the file keeps everything else as it was, and the old one is kept next to it as `<map>.json.bak`. Edits that are loaded from the map are part of the map (you can't `.undo` them); edits that are not saved are lost when you quit (the console says so).
- A command that would change more than `REND_MAX_BLOCKS` blocks does nothing and says so. Editing only remakes the chunks that changed, so it stays quick on big maps (13,000 blocks: a fifth of a second; 1,500,000: about 2 seconds).

### Atlas:

![](resources/atlas.png)

### To-Do:
- Advanced tree functions (including the `WINDSWEPT` tree, which is a placeholder in `world.py`)
- Place and destroy blocks (first on a hotkey at a position, eventually at the end of a directed ray); `World.edit` (remakes only the changed chunks) and `World.raycast` (the block you look at) are there for it, and it should become a rend op so it can be undone and saved
- Effects that need the depth of the scene (fog, depth of field, outlines of depth, ambient occlusion, a tint or a scan by depth): the depth buffer has to be readable as a texture
- Effects that need the previous frame (trails, motion blur, ghosts, feedback): a copy of the last picture has to be kept
- Interactable blocks, and shaders that belong to single blocks (every block would carry a material for it)
