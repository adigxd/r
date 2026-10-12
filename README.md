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
| Backslash (`\`) | Cycle post-processing shader |
| Backquote (`` ` ``) | Save screenshot |
| Right Ctrl | Toggle wireframe debug mode |
| Right Shift | Exit |

### Customization:

- Create your own map in `maps` ... run it with `python r.py <map>`
- All settings (resolution, speed, light, paths, music, etc.) live in the `config` block of the map file, so every map can have its own; `config.py` lists every key and what it does
- The blocks live in the `world` block of the map file (`voxels`, `cubes`, `spheres`, `cylinders`, `cones`, `trees`, `forests`); block names are in `world.py`
- Edit the textures in `resources/atlas.png`

### Files:

| File | What |
| --- | --- |
| `r.py` | Entry point: window, main loop, post-processing |
| `config.py` | Loads a map file and its settings |
| `world.py` | Blocks, shapes / trees, and the block mesh |
| `camera.py` | Movement, mouse look, collisions |
| `matrices.py` | Model / view / projection matrices |
| `buffers.py` | OpenGL vertex buffers |
| `glsl.py` | Shader loading and compiling |
| `uniforms.py` | Shader uniform values |
| `log.py` | Console logging |
| `maps/` | Map files (settings + blocks) |
| `shaders/` | GLSL shaders (`block.*` for the world, `post*.frag` for post-processing) |
| `resources/` | Texture atlas, window icon, music |
| `CHANGELOG.md` | Version history |

### Atlas:

![](resources/atlas.png)

### To-Do:
- Advanced tree functions
- Advanced shape functions for stretch
- CLI:
    - W/E
    - Other (etc.)
- On hotkey, place at pos ... eventually make it place at end of directed ray