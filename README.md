# r

### What?

The best voxel engine ever

### CLI:

```
pip install -r requirements.txt
python r.py [map]
```

`map` is a file in `maps` (with or without `.json`); default is `1`.

### Keybinds:

| Key | Use |
| --- | --- |
| W / A / S / D | Move forward / left / backward / right |
| Mouse move | Look around |
| Right mouse button | Hold to increase movement speed |
| Space | Fly up in debug mode; jump in normal mode |
| Left Shift | Fly down in debug mode |
| Backspace | Reset position |
| F11 | Toggle fullscreen |
| Backslash (`\`) | Cycle post-processing shader |
| Backquote (`` ` ``) | Save screenshot |
| Right Ctrl | Toggle wireframe debug mode |
| Right Shift | Exit |

### Settings:

There are two places, depending on whether a setting belongs to *you* or to *a map*:

- **`.env.pre`** has everything that is the same for every map (window size, fullscreen, fps cap, view distance, mouse sensitivity, mipmaps, texture atlas, shader files, audio, ...) with a comment on each line. To change something for yourself, add just that line to a file called `.env` (not tracked by git); it overrides `.env.pre`.
- **The map file** (`maps/<map>.json`) has everything that belongs to that map: `config` (seed, spawn, background, physics, speed, optional `music`), `lights`, `lighting` and `world` (the blocks). `config.py` lists every key and what it does.

If a setting is missing or has a typo, the game says which one and exits.

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
- **`lights`** is a list of 0 to 16 lights, each with its own settings (only `radius` is needed, and `pos` unless it follows the player):

```json
{"pos": [10, 4, 0], "radius": 14, "intensity": 1.5, "color": [1.0, 0.2, 0.2], "falloff": "inverse_square", "falloff_scale": 0.3, "snap": true, "diffuse": 1.0}
{"follow_player": true, "pos": [0, 1, 0], "radius": 16, "color": [0.5, 0.875, 1.0]}
```

  `follow_player` makes `pos` an offset from the player, `snap` puts the light in the middle of its block, `diffuse` is how much the angle of a surface matters (0 to 1), `falloff` is `"linear"` or `"inverse_square"`.
- **`lighting`** is everything that isn't one light, all optional: `ambient`, `ambient_color`, `brightness`, `per_block` (light whole blocks or single pixels) and `face_shade` (how bright each side of a block is: `top`, `bottom`, `front`, `back`, `left`, `right`).
- **`world`** has `voxels`, `cubes`, `spheres`, `cylinders`, `cones`, `trees` and `forests`; block names are in `world.py`.
  - A cube is either its edges (`x_min` ... `z_max`) or its middle and size (`x`, `y`, `z`, `size`; `size` can be one number or `[x, y, z]`).
  - Spheres, cylinders and cones can have a `scale` to stretch them along x / y / z: `"scale": [2, 1, 1]` is twice as wide in x (a sphere becomes an ellipsoid, a cylinder an elliptical one).

### Customization:

- Create your own map in `maps` ... run it with `python r.py <map>`
- Edit the textures in `resources/atlas.png`
- A new block needs a spot in `world.py` (`BLOCK_TYPES`) that points at its tile(s) in the atlas

### Files:

| File | What |
| --- | --- |
| `r.py` | Entry point: window, main loop, post-processing, fullscreen |
| `config.py` | Loads `.env.pre` / `.env` and a map file, and checks all of it |
| `world.py` | Blocks, shapes / trees, and the block mesh |
| `camera.py` | Movement, mouse look, collisions |
| `matrices.py` | Model / view / projection matrices |
| `buffers.py` | OpenGL vertex buffers and the frame buffer |
| `glsl.py` | Shader loading and compiling |
| `uniforms.py` | Shader uniform values (matrices, lights, ...) |
| `log.py` | Console logging |
| `.env.pre` | Default settings for every map |
| `maps/` | Map files (their settings, lights and blocks) |
| `shaders/` | GLSL shaders (`block.*` for the world, `post_*.frag` for post-processing) |
| `resources/` | Texture atlas, window icon, music |
| `CHANGELOG.md` | Version history |

### Atlas:

![](resources/atlas.png)

### To-Do:
- Advanced tree functions (including the `WINDSWEPT` tree, which is a placeholder in `world.py`)
- Rend (the in-game worldedit): a chat in JetBrains Mono, opened with T, closed with Esc, sent with Enter; it only takes commands and says so when a command doesn't exist
- Place and destroy blocks (first on a hotkey at a position, eventually at the end of a directed ray)
