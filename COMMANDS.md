# rend commands

rend is the world editing of the game. You type commands into the chat.

- Press **T** to open the chat, type, press **Enter** to run it, **Escape** to close it without sending.
- A line that starts with a **`.`** is a command. A line that does not is a chat message (it shows as `<You> text` until there is multiplayer).
- Command names are not case sensitive (`.SET` is `.set`). Block names are not case sensitive either.
- Answers come back in the chat: **green** = it worked, **grey** = information, **red** = a mistake (nothing was changed).

Typing helpers: **Tab** finishes a command name (or lists the ones that match), **Up / Down** bring back what you sent before, **Left / Right / Home / End** move in the line (hold **Ctrl** to jump a word, also with Backspace and Delete), **Ctrl+V** pastes, **Page Up / Page Down** (or the mouse wheel) scroll the chat. While the chat is open you stand still and the view does not turn (gravity still works).

Contents: [the basics](#the-basics) · [selecting](#selecting) · [changing blocks](#changing-blocks) · [shapes](#shapes) · [copying and moving](#copying-and-moving) · [undo, redo and saving](#undo-redo-and-saving) · [moving yourself](#moving-yourself) · [other](#other) · [recipes](#recipes) · [messages and what they mean](#messages-and-what-they-mean)

---

## The basics

### Coordinates

The world is a grid of blocks. `x` goes east (right when you start), `y` goes up, `z` goes south (towards you when you start; the way you face at the start is **north**, `-z`).

A command that takes `x y z` takes whole numbers. Instead of a number you can write:

| You write | Means |
| --- | --- |
| `~` | the same as the block you are standing in |
| `~5` | 5 more than the block you are standing in |
| `~-3` | 3 less than the block you are standing in |

The block you stand in is the block your feet are in: if you stand on a floor whose top is at height 2, you are in the block `y = 2` (the empty block above the floor). `.coords` tells you.

### Blocks

Wherever a command wants `<blocks>`, you can write:

| You write | Means |
| --- | --- |
| `STONE` | that block |
| `STONE,DIRT` | a mix: each block is either one of them, with equal chances |
| `GRASS:60,STONE_LIGHT:1` | a mix with weights: 60 parts grass to 1 part light stone |
| `AIR` | nothing: it takes blocks away |

Names are the block names of the game (`STONE`, `STONE_BRICK_DARK`, `GRASS`, `DIRT`, `SAND`, `LOG_PINE`, `LEAF_MAPLE`, ...; `.help` and `world.py` have them all). If you mistype one, you get suggestions.

A mix is random but not reckless: the random choices are remembered (as a seed), so when your edits are saved and played again next time you get exactly the same blocks.

### The selection

Most commands work on a **selection**: a box between two corners you set with `.pos1` and `.pos2`. Both corners are inside the box (corners `0 0 0` and `3 2 1` select `4 x 3 x 2 = 24` blocks). The box is drawn in the world: cyan for the whole selection, an orange outline on corner 1 and a blue one on corner 2; you can see it through walls too, faintly. The two corners can be in any order.

### Limits

- A command that would work on more than **`REND_MAX_BLOCKS`** blocks (4,000,000 by default, in `.env.pre`) says so and does nothing.
- A command that would change nothing (the blocks were like that already) says so, and does not count as a step for undo.
- Undo remembers as many changed blocks as **`REND_UNDO_BLOCKS`** allows (8,000,000 by default); the oldest steps are forgotten first.

---

## Selecting

### `.pos1` and `.pos2`

```
.pos1 [x y z | look]
.pos2 [x y z | look]
```

Sets the first / second corner of the selection.

- **With nothing after it:** the block you are standing in.
- **`look`:** the block you are looking at (the solid block your crosshair would hit, within 100 blocks). It is the block itself, not the empty space in front of it.
- **`x y z`:** exactly that block. `~` works.

Once both corners are set, the answer also says how many blocks are selected.

```rend
.pos1
.pos2 ~9 ~4 ~9
```
Select a box that starts where you stand and reaches 9 blocks east, 4 up and 9 south.

```rend
.pos1 look
.pos2 10 4 10
```
One corner is the block you are looking at, the other is a block you name.

```rend
.pos1 0 0 0
.pos2 3 2 1
```
Answers: `position 1 is 0 0 0` and `position 2 is 3 2 1 (24 blocks selected)`.

```text
.pos1 look     (looking at the sky, nothing within 100 blocks)
→ you are not looking at a block (it has to be within 100 blocks)
.pos1 1 2
→ .pos1 needs x y z, or look, or nothing
```

### `.sel`

```
.sel
```

Says what is selected: the two far corners, the size on each axis, and the number of blocks.

```text
.sel
→ 0 0 0 to 3 2 1: 4 x 3 x 2 = 24 blocks
```

With one corner set it tells you the other is missing; with none, that nothing is selected.

### `.desel`

```
.desel
```

Forgets both corners (the box disappears).

---

## Changing blocks

All of these work on the selection and tell you how many blocks really changed (blocks that already were what you asked for don't count).

### `.set`

```
.set <blocks>
```

Fills the whole selection with the blocks. What was there is replaced. `AIR` empties it.

```rend
.pos1 0 2 0
.pos2 9 2 9
.set stone_brick
```
A floor of stone brick, 10 x 10.

```rend
.pos1 0 2 0
.pos2 9 2 9
.set grass:60,dirt:10,stone_light:1
```
A patchy meadow: mostly grass, some dirt, a few light stone "flowers".

```rend
.pos1 0 2 0
.pos2 9 6 9
.set air
```
Clears a box (digs it out).

Answer: `set 100 blocks`.

### `.replace`

```
.replace <from> <to>
```

Inside the selection, every block that is one of `<from>` becomes `<to>`. Everything else stays.

- `<from>` is a list of names (`stone` or `stone,sand,dirt`; weights are ignored there). It can be **`*`**, which means every block that exists (not air), or **`AIR`**, which means the empty places.
- `<to>` is a block, a mix, or `AIR`.

```rend
.pos1 0 2 0
.pos2 9 6 9
.set stone
.replace stone grass
```
Everything that was stone turns to grass.

```rend
.pos1 -5 0 -5
.pos2 5 8 5
.replace stone,sand,dirt air
```
Takes stone, sand and dirt out of a box and leaves other things (trees, logs, ...).

```rend
.pos1 0 2 0
.pos2 9 8 9
.set grass
.replace * stone_brick
```
`*` is every block: all of it becomes stone brick.

```text
.replace stone glass
→ unknown block "glass"        (nothing changes; a name that is nearly right also gets suggestions)
```

```rend
.pos1 0 2 0
.pos2 5 5 5
.replace air dirt
```
Fills every empty place of a box with dirt, and leaves the blocks that are there.

Answer, for example: `replaced 12 blocks`.

### `.walls`

```
.walls <blocks>
```

Builds the four sides of the selection over its whole height (not the floor and not the ceiling).

```rend
.pos1 0 2 0
.pos2 8 6 8
.walls stone_brick_light
```
The walls of a house, 9 wide and 5 high, open at the top and bottom.

Answer: `built walls of 160 blocks` (the 9 x 9 ring is 32 blocks around, times 5 high).

### `.hollow`

```
.hollow
```

Keeps the outer layer of the selection (all six sides) and takes away everything inside it.

```rend
.pos1 0 2 0
.pos2 8 7 8
.set stone_brick
.hollow
```
A closed room: a solid block, then emptied inside, with 1 thick walls, floor and ceiling.

```rend
.pos1 0 3 0
.pos2 0 4 0
.set air
```
...and a door: select the two blocks of the doorway in the wall (here the wall at `x = 0`) and empty them.

Answer: `took away 196 blocks inside` (the 7 x 4 x 7 inside of a 9 x 6 x 9 box).

---

## Shapes

Shapes are not made inside the selection. They are put around a point: the block you stand in, or the one you name with `at x y z` (`~` works).

### `.sphere`

```
.sphere <blocks> <radius> [hollow] [at x y z]
```

A ball. The block it is centered on counts as its middle; every block whose middle is at most `radius` away is part of it (radius can have decimals, like `3.5`). With `hollow` it is only a shell, about one block thick.

```rend
.sphere stone 5
```
A solid ball of radius 5 around where you stand. (You are inside solid blocks now: the game lifts you out through the top. Use `hollow` or `at` to avoid that.)

```rend
.sphere stone_brick_light 8 hollow at ~ ~ ~
```
A hollow dome-ball with you standing inside it, 8 blocks of radius.

```rend
.sphere grass:5,dirt:1 12 at 0 -4 0
```
A lump of ground, centered 4 blocks under the origin.

```rend
.sphere air 6 at 30 10 30
```
Digs a round hole of radius 6 at that place.

Answer: `made a ball of 515 blocks` for radius 5 in open space (only blocks that really changed are counted, so a ball in the ground says less). A radius that is zero, negative, above 500 or too big for `REND_MAX_BLOCKS` gives a red message.

### `.cyl`

```
.cyl <blocks> <radius> <height> [hollow] [at x y z]
```

A vertical tower. The block it is centered on is its **lowest layer**, and it goes up `height` blocks. With `hollow` only the ring is made: a pipe, open at both ends.

```rend
.cyl log_pine 2 12
```
A trunk-like column of radius 2, 12 high, standing on the block you stand in (you will be lifted out of it).

```rend
.cyl stone_brick_light 6 20 hollow at 20 2 20
```
A round tower wall, radius 6, 20 high, at those coordinates.

```rend
.cyl stone 5 1 at ~ ~-1 ~
```
A round platform: height 1, one block under your feet.

```rend
.cyl air 3 30 at 40 0 40
```
Digs a vertical shaft.

Answer: `made a tower of 156 blocks` (13 blocks in every layer, 12 layers).

---

## Copying and moving

### `.copy`

```
.copy
```

Remembers the blocks of the selection (the empty places too) in the clipboard, together with **where the box is relative to the block you stand in**. There is one clipboard: a new `.copy` or `.cut` replaces it.

Stand next to the thing you copy, so that pasting next to something else is easy.

### `.cut`

```
.cut
```

Like `.copy`, and then takes the blocks away (sets them to air). You can `.undo` it to put them back.

### `.paste`

```
.paste [noair]
```

Puts the clipboard down so that it has the same place relative to you as when you copied it: copy it standing south of a house, then walk somewhere else and paste, and the copy stands in the same way relative to you.

- Normally the empty places of the copied box erase what is in the target (the whole box is replaced).
- With **`noair`** the empty places are skipped, so only the blocks are put down. Use it to paste a tree into a landscape without cutting a square hole around it.

```rend
.pos1 0 2 0
.pos2 4 8 4
.copy
.paste
```
(Pasted onto itself: nothing changes and it says so. Walk somewhere, then `.paste`.)

```rend
.pos1 2 3 2
.pos2 8 14 8
.copy
.tp 30 2 2
.paste noair
```
Copies a tree and puts it down 28 blocks east without a hole around it.

Answer, for example: `pasted, 340 blocks changed`. Before any `.copy`: `nothing copied yet (.copy first)`.

### `.move`

```
.move <distance> <direction>
.move <dx> <dy> <dz>
```

Moves everything in the selection. The place it was in becomes empty. The selection itself stays where it is (so you can move again from the same box, or `.undo`).

Directions: **`up`, `down`, `north`** (`-z`, the way you face at the start), **`south`** (`+z`), **`east`** (`+x`), **`west`** (`-x`).

The whole box moves, empty places in it included: whatever is in the place it moves to is replaced by the box.

```rend
.pos1 0 2 0
.pos2 4 6 4
.set stone
.move 5 up
```
Lifts the block 5 up.

```rend
.pos1 0 2 0
.pos2 4 6 4
.set stone
.move 12 east
```
Moves it 12 blocks east.

```rend
.pos1 0 2 0
.pos2 4 6 4
.set stone
.move 3 0 -2
```
Moves it 3 east and 2 north (numbers: east, up, south).

Answer: `moved, 250 blocks changed`. Zero distance says `that does not move anything`.

### `.stack`

```
.stack <count> [direction]
.stack <count> <distance> <direction>
.stack <count> <dx> <dy> <dz>
```

Repeats what is in the selection `count` times (the original stays, so you end with `count + 1` of them).

- With **only a direction** (or nothing, which means `up`) each copy goes one box-length further, so the copies touch: stacking a floor upwards makes floors on top of each other.
- With a **distance and a direction** each copy goes that far from the one before. Use this for gaps (a fence with posts every 4 blocks).
- With **three numbers** it is the step from one copy to the next, in any direction.

The empty places of the box are copied too, so copies overwrite what is in their way.

```rend
.pos1 0 2 0
.pos2 0 2 0
.set stone_brick
.stack 9 up
```
One brick block becomes a column of 10.

```rend
.pos1 0 2 0
.pos2 8 2 0
.set stone_brick
.stack 5 south
```
A row of 9 bricks becomes 6 rows: a floor 9 x 6.

```rend
.pos1 0 2 0
.pos2 0 6 0
.set log_pine
.stack 8 4 east
```
A post 5 high and 8 more posts, every 4 blocks to the east.

```rend
.pos1 0 2 0
.pos2 3 2 3
.set stone
.stack 6 1 1 0
```
A staircase going 1 east and 1 up for every step.

Answer: `stacked 9 times, 9 blocks changed`.

---

## Undo, redo and saving

### `.undo`

```
.undo [n]
```

Takes back the last `n` edits (1 if you leave it out). Every command that changes blocks is one edit: `.set`, `.replace`, `.walls`, `.hollow`, `.sphere`, `.cyl`, `.cut`, `.paste`, `.move`, `.stack`. `.copy` is not (it changes nothing).

```text
.undo
→ undid 1 edit (100 blocks)
.undo 5
→ undid 3 edits (812 blocks)       (only 3 were left)
.undo
→ nothing to undo
```

What cannot be undone: edits that were already in the map file when the game started (they are part of the map), and steps that were forgotten because of the undo memory limit.

### `.redo`

```
.redo [n]
```

Does again what was undone. As soon as you make a new edit, the steps that could be redone are gone.

```rend
.pos1 0 2 0
.pos2 4 4 4
.set stone
.set dirt
.undo
.undo
.redo
```
Ends with the stone back (the dirt was undone, then the stone was undone, then the stone was redone).

### `.save`

```
.save
```

Puts everything you changed into the map file, so that the map has it the next time.

How it works: the map file gets an `"edits"` list. It holds one short entry for every command you ran (with the numbers worked out: the corners, the seed of the random choices), not all the blocks. When the game builds the map it first builds the shapes of the map and then plays the edits, in order, so you get the world you left. Undone edits are not saved.

- The rest of the map file is left exactly as it was. The old file is kept next to it as `<map>.json.bak` (one copy: the next save replaces it).
- A save that would change anything but the edits is refused and writes nothing.
- Nothing is saved by itself. If you leave with edits that were not saved, the console says so.
- To go back to the map without your edits: delete the `"edits"` list in the map file (or copy the `.bak` back).
- The edits use fixed coordinates and are played on top of the map's shapes: if you later change the shapes in the map file, the edits still land where they were.

```text
.save
→ saved 7 edits into parkour.json (the old file is parkour.json.bak)
```

---

## Moving yourself

### `.tp`

```
.tp <x y z>
```

Takes you to a block: you stand in the middle of it, at its bottom. `~` works. If you end up inside blocks you are lifted out.

```rend
.tp 0 20 0
.tp ~ ~30 ~
.tp ~10 ~ ~-10
```
Goes to a place, then 30 up from where you are, then 10 east and 10 north of where you are.

Answer: `went to 0 20 0`.

### `.spawn`

```
.spawn
```

Back to the spawn of the map (the same as pressing Escape when the chat is closed).

### `.coords`

```
.coords
```

Tells you the block you are standing in: handy for choosing `x y z`.

```text
.coords
→ you are in the block 12 2 -7
```

---

## Other

### `.help`

```
.help
.help <command>
```

Lists the commands, or explains one (with or without the dot: `.help set`, `.help .set`).

### `.clear`

```
.clear
```

Empties the chat window (nothing in the world changes).

---

## Recipes

**A house.**

```rend
.pos1 ~ ~ ~
.pos2 ~10 ~5 ~8
.set stone_brick_light
.hollow
.pos1 ~4 ~ ~
.pos2 ~5 ~2 ~
.set air
```
A room 11 x 6 x 9 with a 2 wide door in the front wall (the door is a block `~4`, `~5` east of where you stood at the start; use `.pos1` / `.pos2` with `look` to choose the doorway by looking at it).

**A pond.**

```rend
.sphere air 6 at ~ ~ ~
```
Digs a round hole where you stand. (Fill the bottom half with `.pos1` / `.pos2` and `.replace air water` once the game has a water block.)

**A row of lamp posts.**

```rend
.pos1 0 2 0
.pos2 0 6 0
.set log_redwood_naked
.pos1 0 7 0
.pos2 0 7 0
.set stone_light
.pos1 0 2 0
.pos2 0 7 0
.stack 9 6 east
```
One post with a light block on top, then 9 more, 6 blocks apart.

**A tree for each of three places.**

```rend
.pos1 5 3 5
.pos2 11 16 11
.copy
.tp 40 2 5
.paste noair
.tp 80 2 5
.paste noair
```
Copy one tree, then paste it where you are (twice). `noair` keeps the ground around the paste.

**Taking a mistake back.**

```rend
.pos1 0 2 0
.pos2 5 5 5
.set sand
.undo
```

**Working on a part of the map across sessions.** Edit, `.save`, quit. Next time the map has your edits. If you are unhappy with a day of work: `.undo` (this session only), or put the `.bak` back, or delete the `"edits"` list.

---

## Messages and what they mean

| Message | What is wrong |
| --- | --- |
| `unknown command .sett (maybe .set?)` | no such command; the hint lists commands that start the same |
| `select two corners first (.pos1 and .pos2)` | the command needs a selection |
| `unknown block "stoen" (did you mean STONE, ...?)` | a block name does not exist |
| `the weight of STONE has to be above 0` / `"x" is not a number (the weight of STONE)` | a mistake in `NAME:weight` |
| `you are not looking at a block (it has to be within 100 blocks)` | `look` found nothing |
| `.pos1 needs x y z, or look, or nothing` | the wrong number of numbers |
| `a coordinate has to be a whole number, not "abc"` | a coordinate is not a whole number or `~` form |
| `that is 5,000,000 blocks, the limit is 4,000,000 (REND_MAX_BLOCKS in .env.pre)` | the selection (or result) is too big; a smaller box, or change the limit |
| `nothing changed (it was like that already)` | it was fine as it was; there is nothing to undo either |
| `nothing copied yet (.copy first)` | `.paste` before `.copy` |
| `give a direction (up down north south east west), a distance and a direction, or 3 numbers` | wrong form after `.move` or `.stack` |
| `that does not move anything` | `.move 0 0 0` |
| `nothing to undo` / `nothing to redo` | the lists are empty |
| `could not save: ...` | the map file can't be written (the reason follows), or saving would have changed more than the edits |
| `something went wrong in .xxx: ...` | a bug; the game goes on and the console has the details, please report it |
