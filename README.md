# r

### What?

The best voxel engine ever

### CLI:

```
pip install -r req.txt
cp .env.pre .env
python r.py
```

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

- Create your own map in `DIR-Maps` ... set your map in `.env` (`_MAP`)
- Edit other variables in `.env`
- Edit the textures in `DIR-Resources/IMG-Texture.png`

### Atlas:

![](DIR-Resources/IMG-Texture.png)

### To-Do:
- Advanced tree functions
- Advanced shape functions for stretch
- Generally move `.env` vars to JSON map
- CLI:
    - W/E
    - Other (map sel, etc.)
- On hotkey, place at pos ... eventually make it place at end of directed ray