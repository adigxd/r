import os
import sys

from effects import REGISTRY, CATEGORIES, CATEGORY_DOCS, BLEND_MODES

# python -m effects: writes SHADERS.md (the guide to the shaders, with every effect and every setting), made from what the code says so it can't be out of date
# (run it from the folder of r.py again whenever an effect or a command changes)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import fx
import fxcommands

INTRO = """# Shaders

A **shader** is what the whole picture goes through before it reaches the screen: a stack of **effects**, applied one after the other. You build one in the game (from a menu of about {count} effects, no code), keep it, and it works on every map.

- **Backslash** (`\\`) shows the next shader, **Shift + Backslash** the previous one, round and round. The game starts on the first one (`default`, which is the picture as it is).
- **`]`** opens a menu on the right of the window to do all of it with the mouse. **T** opens the chat, where the `.fx` and `.shader` commands do the same. Use either or both, they change the same thing.
- The built-in shaders can't be changed or deleted. Yours are saved in `shaders/custom` (one `.json` file each, change `SHADER_DIR` in `.env` to move them), come after the built-in ones in alphabetical order, and are not tied to a map.

## The stack

Effects are layers: the first one is applied to the picture of the game, the next one to the result, and so on. The one on top (the highest number) is applied last. Any effect can be in the stack any number of times, in any order, and the order matters: a vignette before a dither is dithered, a vignette after it is smooth.

```
.fx add vignette amount=0.6        puts it on top of the stack
.fx add dither bayer8 4 2          the same effect can come again, and again
.fx stack                          what is on the screen (the top one first)
.fx up 1                           move effect 1 up (so it is applied after more of the others)
.fx swap 1 3                       swap two effects
.fx off 2                          switch one off without taking it out
.fx mix 3 0.4                      use only 40% of effect 3
.fx clear                          nothing on the screen: the picture as it is
.shader save my-look               keep what is on the screen as a shader of your own
```

## Settings

Every effect has settings (`.fx info <effect>` lists them). Write them as `name=value`, in any order, or only the values in the order `.fx info` lists them; both mean the same:

```
.fx add dither type=bayer8 levels=4 size=2
.fx add dither bayer8 4 2
.fx add dither levels=4 cluster         (a mix: the values without a name fill the settings you did not name)
.fx set 2 levels=8 type=noise           (change an effect that is in the stack: its number is in .fx stack)
.fx set 2 levels 8                      (also: name, then value)
.fx reset 2 levels                      (back to what it starts as)
```

| Kind | How to write it |
| --- | --- |
| number | `0.5`, `12` (a number outside what a setting takes is moved into it, and the game says so) |
| yes or no | `yes`, `no` (also `on`, `off`, `true`, `false`, `1`, `0`) |
| one of a list | its name (`bayer8`), its number in `.fx info` (`3`), or the start of its name when that is clear (`bay` is not, `clu` is `cluster`) |
| color | `#ff8000`, `#f80`, `1,0.5,0` (0 to 1) or `255,128,0` (0 to 255), or a name: black, white, gray, silver, red, green, blue, yellow, cyan, magenta, orange, pink, purple, brown, teal, navy, lime, gold, sky |
| point | `0.5,0.5` (x,y over the screen from 0 to 1, `0,0` is the bottom left) |

Every effect also has **`mix`** (0 to 1: how much of the effect is used, 0 is none, 1 is all of it); the ones that move in time have **`speed`** (how fast, 0 stops it, negative runs it backwards) and the ones that use random numbers have **`seed`** (another number, another pattern). These three can only be written by name (`.fx set 2 mix=0.5`). `.fx speed <x>` changes the speed of every animation at once.

Sizes in pixels (the size of a dither pixel, the width of an outline, the radius of a blur, ...) are measured on a screen 1080 pixels high and grow and shrink with the window, so an effect looks the same at every resolution.

## The menu (`]`)

A black panel on the right (`GUI_WIDTH`, `GUI_ALPHA` and `GUI_FONT_SIZE` in `.env.pre`); the mouse becomes a pointer while it is open and the view does not turn (you can still walk, unless you are typing in one of its lines). The panel has three tabs:

- **stack**: the effects on the screen, the top of the list is the top of the stack. Click an effect to open its settings. Buttons on every effect: switch on / off, up, down, copy, remove. A setting is a line to drag (click the number to type one, **right click** puts it back, **Shift + wheel** changes it a little), a yes / no to click, a list to click through (right click goes back), a color (click the swatch for red, green and blue lines, click the number to type a color) or a point (two lines). Also: expand / collapse all, clear, undo, redo and the speed of the animations.
- **add**: every effect with what it does; type in the search line or pick a category; click one to put it on top of the stack.
- **library**: every shader (the one on the screen has a bar next to it, a `*` means it was changed since it was saved). Click one to show it. Type a name and press Enter (or click save) to keep what is on the screen; yours can be renamed, copied and deleted (delete asks you to click twice); any shader, built in or yours, can be copied.

The mouse wheel scrolls a tab. The line at the bottom says what the pointer is over, and what the last action did.

## Commands

"""

OUTRO = """
## A shader file

The `.json` files in `shaders/custom` (made by `.shader save`, you can also write one by hand; the name of the file is the name of the shader) look like this, with one effect on every line, in the order they are applied:

```json
{
  "name": "cozy",
  "description": "warm and dark at the edges",
  "speed": 1.0,
  "effects": [
    {"effect": "temperature", "params": {"warmth": 0.4}},
    {"effect": "vignette", "params": {"amount": 0.7, "color": [0.1, 0.05, 0.0]}},
    {"effect": "grain", "params": {"amount": 0.05}, "enabled": false}
  ]
}
```

Only settings that differ from what they start as have to be written. A file with a wrong effect or setting still loads: what is wrong is left out and the console says what it was. The built-in shaders are the same kind of file, in `shaders/defaults.json` (`SHADER_DEFAULTS`).

## Notes

- Effects that draw something that moves are animated with the time of the game; `strobe` and `flash` can go at any rate you ask for, and fast flashing can bother people who are sensitive to it.
- An effect is compiled the first time it is used (a few milliseconds; `bloom` and the other effects of several passes take a little longer). Every effect is one or more full-screen passes, and `.fx cost` says how many the stack needs; the menu and the commands never limit how many effects there are, only your graphics card does.
- Not there yet: effects that need the depth of the scene (fog, depth of field, outlines of depth, ambient occlusion, a tint or a scan by depth) and effects that need the previous frame (trails, motion blur, ghosts, feedback), and shaders that belong to single blocks.
"""


def table_cell(text):
    return str(text).replace('|', '\\|')


def settings_table(effect):
    lines = ['| Setting | Kind | Starts as | What |', '| --- | --- | --- | --- |']

    for p in effect.params:
        kind = fx.kind_text(p)
        default = fx.format_value(p, p.default)
        what = p.doc + ('' if p in effect.own else ' (every effect has it)' if p.name == 'mix' else '')
        lines.append(f'| `{p.name}` | {table_cell(kind)} | `{table_cell(default)}` | {table_cell(what)} |')

    return '\n'.join(lines)


def shader_chain(shader):
    if not shader['effects']:
        return 'no effects'

    return ', '.join(entry['effect'] for entry in shader['effects'])


def build():
    out = [INTRO.format(count=len(REGISTRY))]

    for group, rows in fxcommands.HELP.items():
        out.append(f'### `.{group}`\n')
        out.append('| Command | What it does |')
        out.append('| --- | --- |')

        for usage, what in rows:
            out.append(f'| `{table_cell(usage)}` | {table_cell(what)} |')

        out.append('')

    out.append('`.help fx` and `.help shader` say the same in the game. Tab finishes command words, effect names, settings (`type=`), the choices of a setting and shader names.\n')

    library = fx.Library(os.path.join(ROOT, 'shaders', 'defaults.json'), os.path.join(ROOT, 'shaders', 'no-custom-shaders-here'))
    out.append('## Built-in shaders\n')
    out.append('In the order Backslash goes through them (yours come after, in alphabetical order). Copy any of them (`.shader copy <name> <new>`) to start from it.\n')
    out.append('| # | Shader | What | Effects, in the order they are applied |')
    out.append('| --- | --- | --- | --- |')

    for i, shader in enumerate(library.defaults, 1):
        out.append(f'| {i} | `{shader["name"]}` | {table_cell(shader["description"])} | {table_cell(shader_chain(shader))} |')

    out.append('')
    out.append(f'## The effects ({len(REGISTRY)})\n')
    out.append('Blend modes (in `blend` and `gradient`): ' + ', '.join(f'`{m}`' for m in BLEND_MODES) + '. The settings that say what to show where the picture is moved off the screen (`edge`): `clamp`, `mirror`, `repeat`, `black`.\n')

    for category in CATEGORIES:
        effects = [e for e in REGISTRY.values() if e.category == category]
        out.append(f'### {category}: {CATEGORY_DOCS[category]}\n')
        out.append('| Effect | What it does |')
        out.append('| --- | --- |')

        for e in effects:
            out.append(f'| [`{e.name}`](#{e.name}) | {table_cell(e.doc)} |')

        out.append('')

        for e in effects:
            passes = f' ({len(e.passes)} passes)' if len(e.passes) > 1 else ''
            out.append(f'#### {e.name}\n')
            out.append(f'{e.doc[0].upper() + e.doc[1:]}{passes}.\n')
            out.append(settings_table(e))
            out.append('')

    out.append(OUTRO)

    return '\n'.join(out)


if __name__ == '__main__':
    path = os.path.join(ROOT, 'SHADERS.md')

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(build())

    print('wrote', path)
