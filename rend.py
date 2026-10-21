import difflib
import itertools
import json
import math
import os
import random
import traceback

import numpy as np

# rend: the world editing of the game, driven by commands that all start with a "." (typed in the chat)
# every command that changes blocks is an "op": a small dict that says what was done, with the numbers worked out (the corners of the selection, the seed of the random picks)
# the ops are what the "edits" of a map file hold: playing them again, in order, gives the same world, so a saved map stays small and readable
# nothing in here needs a window: it works on a world that has `blocks` (a dict) and `edit(changes)` (see World.edit)

AIR = 'AIR'
DIRECTIONS = {'up': (0, 1, 0), 'down': (0, -1, 0), 'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)} # north is where you look when the game starts

# what the user is told: (kind, text)
OK, INFO, ERROR = 'ok', 'info', 'error'


class RendError(Exception):
    # something wrong with a command: the text is shown to the user
    pass


# ------ blocks the user types

def parse_blocks(text, names):
    # "STONE", "stone,dirt" (equal chances), "GRASS:60,STONE_LIGHT:1" (weights); returns {NAME: weight}
    picks = {}

    for part in text.split(','):
        name, _, weight = part.strip().partition(':')
        name = name.upper()

        if name not in names:
            close = [n for n in sorted(names) if n.startswith(name)][:4] if name else []
            close = close or difflib.get_close_matches(name, sorted(names), n=4, cutoff=0.6)
            raise RendError(f'unknown block "{part.strip()}"' + (f' (did you mean {", ".join(close)}?)' if close else ''))

        try:
            weight = float(weight) if weight else 1.0
        except ValueError:
            raise RendError(f'"{weight}" is not a number (the weight of {name})')

        if weight <= 0:
            raise RendError(f'the weight of {name} has to be above 0')

        picks[name] = picks.get(name, 0.0) + weight

    if not picks:
        raise RendError('no block given')

    return picks


def picker(blocks, seed):
    # returns a function that gives the block types for n blocks of an op: {NAME: weight} with the random numbers of seed, the same every time
    names = list(blocks)

    if len(names) == 1:
        return lambda count: [names[0]] * count

    weights = list(blocks.values())
    rng = random.Random(seed)

    return lambda count: rng.choices(names, weights=weights, k=count)


# ------ the shape of a region

def corners(a, b):
    return tuple(min(a[i], b[i]) for i in range(3)), tuple(max(a[i], b[i]) for i in range(3))


def volume(a, b):
    low, high = corners(a, b)

    return (high[0] - low[0] + 1) * (high[1] - low[1] + 1) * (high[2] - low[2] + 1)


def region_positions(a, b):
    # every block position of the cuboid between two corners (both included), x slowest
    low, high = corners(a, b)

    return itertools.product(range(low[0], high[0] + 1), range(low[1], high[1] + 1), range(low[2], high[2] + 1))


def is_edge(pos, low, high):
    return any(pos[i] in (low[i], high[i]) for i in range(3))


def sphere_positions(center, radius, hollow):
    cx, cy, cz = center
    r = int(math.ceil(radius))
    out = []

    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            for dz in range(-r, r + 1):
                d = dx * dx + dy * dy + dz * dz

                if d <= radius * radius and (not hollow or d > (radius - 1) * (radius - 1)):
                    out.append((cx + dx, cy + dy, cz + dz))

    return out


def cylinder_positions(center, radius, height, hollow):
    # standing on the block at center (it is the lowest layer), going up height blocks
    cx, cy, cz = center
    r = int(math.ceil(radius))
    ring = []

    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = dx * dx + dz * dz

            if d <= radius * radius and (not hollow or d > (radius - 1) * (radius - 1)):
                ring.append((dx, dz))

    return [(cx + dx, cy + dy, cz + dz) for dy in range(height) for (dx, dz) in ring]


# ------ ops: what a command does to the blocks

class Clipboard:
    # a copied cuboid: the block of every position (AIR too), and where its corner is relative to the block the player stood on
    def __init__(self, low, high, origin, blocks):
        self.offset = tuple(low[i] - origin[i] for i in range(3))
        self.size = tuple(high[i] - low[i] + 1 for i in range(3))
        self.names = [AIR] + sorted({blocks[pos] for pos in region_positions(low, high) if pos in blocks})
        index = {name: i for i, name in enumerate(self.names)}
        self.grid = np.zeros(self.size, dtype=np.uint8)

        for pos in region_positions(low, high):
            if pos in blocks:
                self.grid[pos[0] - low[0], pos[1] - low[1], pos[2] - low[2]] = index[blocks[pos]]

    def placed_at(self, at, skip_air):
        # {position: block name} of the clipboard put down with its origin at `at`
        out = {}
        base = tuple(at[i] + self.offset[i] for i in range(3))

        for (i, j, k), value in np.ndenumerate(self.grid):
            name = self.names[value]

            if name != AIR or not skip_air:
                out[(base[0] + i, base[1] + j, base[2] + k)] = name

        return out


def changes_of(op, blocks, state):
    # {position: new block name} for an op, worked out from the blocks as they are now; state holds what lives from op to op (the clipboard)
    # nothing is changed here: the caller applies it (and only the positions that really change count)
    kind = op['op']

    if kind in ('set', 'walls', 'hollow', 'replace'):
        a, b = op['from'], op['to']
        low, high = corners(a, b)

        if kind == 'hollow': # keep the outside of the cuboid, take away everything inside it
            return {pos: AIR for pos in region_positions(a, b) if not is_edge(pos, low, high)}

        if kind == 'walls':
            area = [pos for pos in region_positions(a, b) if pos[0] in (low[0], high[0]) or pos[2] in (low[2], high[2])]
        elif kind == 'replace':
            match = set(op['match'])
            every = '*' in match
            area = [pos for pos in region_positions(a, b) if (pos in blocks if every else blocks.get(pos, AIR) in match)]
        else:
            area = list(region_positions(a, b))

        return dict(zip(area, picker(op['blocks'], op['seed'])(len(area))))

    if kind in ('sphere', 'cyl'):
        if kind == 'sphere':
            area = sphere_positions(op['center'], op['radius'], op['hollow'])
        else:
            area = cylinder_positions(op['center'], op['radius'], op['height'], op['hollow'])

        return dict(zip(area, picker(op['blocks'], op['seed'])(len(area))))

    if kind == 'copy':
        state['clipboard'] = Clipboard(*corners(op['from'], op['to']), op['origin'], blocks)

        return {}

    if kind == 'paste':
        if state.get('clipboard') is None:
            raise RendError('nothing copied yet (.copy first)')

        return state['clipboard'].placed_at(op['at'], op['skip_air'])

    if kind in ('move', 'stack'):
        source = list(region_positions(op['from'], op['to']))
        offset = op['offset']
        contents = {pos: blocks.get(pos, AIR) for pos in source}
        result = {pos: AIR for pos in source} if kind == 'move' else {}

        for n in range(1, (1 if kind == 'move' else op['count']) + 1):
            for pos in source:
                result[(pos[0] + offset[0] * n, pos[1] + offset[1] * n, pos[2] + offset[2] * n)] = contents[pos]

        return result

    raise RendError(f'unknown op "{kind}"')


# what every op has to have (to check an "edits" list of a map file)
OP_KEYS = {
    'set': {'from': 'pos', 'to': 'pos', 'blocks': 'blocks', 'seed': 'int'},
    'walls': {'from': 'pos', 'to': 'pos', 'blocks': 'blocks', 'seed': 'int'},
    'hollow': {'from': 'pos', 'to': 'pos'},
    'replace': {'from': 'pos', 'to': 'pos', 'match': 'names', 'blocks': 'blocks', 'seed': 'int'},
    'sphere': {'center': 'pos', 'radius': 'number', 'hollow': 'flag', 'blocks': 'blocks', 'seed': 'int'},
    'cyl': {'center': 'pos', 'radius': 'number', 'height': 'count', 'hollow': 'flag', 'blocks': 'blocks', 'seed': 'int'},
    'copy': {'from': 'pos', 'to': 'pos', 'origin': 'pos'},
    'paste': {'at': 'pos', 'skip_air': 'flag'},
    'move': {'from': 'pos', 'to': 'pos', 'offset': 'pos'},
    'stack': {'from': 'pos', 'to': 'pos', 'offset': 'pos', 'count': 'count'},
}


def check_value(kind, value, names):
    whole = lambda v: isinstance(v, int) and not isinstance(v, bool)

    if kind == 'pos':
        return isinstance(value, list) and len(value) == 3 and all(whole(v) for v in value)
    if kind == 'int':
        return whole(value)
    if kind == 'count':
        return whole(value) and value > 0
    if kind == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    if kind == 'flag':
        return isinstance(value, bool)
    if kind == 'names':
        return isinstance(value, list) and len(value) > 0 and all(v == '*' or v in names for v in value)
    if kind == 'blocks':
        return isinstance(value, dict) and len(value) > 0 and all(k in names and isinstance(w, (int, float)) and not isinstance(w, bool) and w > 0 for k, w in value.items())

    return False


def validate_edits(edits, names):
    # the problems with the "edits" of a map file, as text (an empty list if it is fine)
    if not isinstance(edits, list):
        return ['edits (needs a list)']

    problems = []

    for i, op in enumerate(edits):
        where = f'edits[{i}]'

        if not isinstance(op, dict) or op.get('op') not in OP_KEYS:
            problems.append(f'{where}.op (needs one of {", ".join(OP_KEYS)})')

            continue

        wanted = OP_KEYS[op['op']]

        for key, kind in wanted.items():
            if key not in op:
                problems.append(f'{where}.{key} (missing)')
            elif not check_value(kind, op[key], names):
                problems.append(f'{where}.{key} (wrong: needs {kind})')

        for key in op:
            if key != 'op' and key not in wanted:
                problems.append(f'{where}.{key} (unknown setting)')

    return problems


def replay(blocks, edits):
    # plays the edits of a map file on the blocks (a dict), no mesh involved: this is how a world with edits is built
    state = {}

    for op in edits:
        for pos, name in changes_of(op, blocks, state).items():
            if name == AIR:
                blocks.pop(pos, None)
            else:
                blocks[pos] = name


# ------ the map file

def write_edits(path, edits):
    # puts the "edits" list into the map file at `path` and leaves everything else in it as it is; the old file is kept next to it as .bak
    with open(path, encoding='utf-8', newline='') as f:
        text = f.read().replace('\r\n', '\n')

    before = json.loads(text)
    lines = ',\n'.join('        ' + json.dumps(op, separators=(', ', ': ')) for op in edits)
    block = '"edits":\n    [\n' + lines + ('\n' if edits else '') + '    ]'
    start = text.find('"edits"')

    if start >= 0: # replace the value that is there
        at = text.index(':', start) + 1

        while text[at] in ' \n\t\r':
            at += 1

        _, end = json.JSONDecoder().raw_decode(text, at)
        new = text[:start] + block + text[end:]
    else: # add it as the last key of the file
        closing = text.rstrip().rfind('}')
        new = text[:closing].rstrip() + ',\n    ' + block + '\n}\n'

    expected = dict(before)
    expected['edits'] = edits

    if json.loads(new) != expected: # never write a file that lost something
        raise RendError('could not save: the map file would have been changed in more than its edits, nothing was written')

    with open(path + '.bak', 'w', encoding='utf-8', newline='') as f:
        f.write(text)

    with open(path + '.tmp', 'w', encoding='utf-8', newline='') as f:
        f.write(new)

    os.replace(path + '.tmp', path)


# ------ undo

class Change:
    # what one command changed, kept compactly so a big edit can still be undone: the positions and the block before / after (as numbers, see Rend.names)
    def __init__(self, positions, before, after, ops):
        self.positions = positions # int32 array (n, 3)
        self.before = before # uint8 arrays
        self.after = after
        self.ops = ops # the ops this was, to keep the edits of the map in step with undo / redo

    def __len__(self):
        return len(self.before)


def without(items, item):
    # a list without one item (that very one, not one that is equal to it)
    return [other for other in items if other is not item]


# ------ the commands

HELP = {
    'help': ('.help [command]', 'what the commands do'),
    'pos1': ('.pos1 [x y z | look]', 'first corner of the selection: where you stand, the block you look at, or numbers (~ is relative to you)'),
    'pos2': ('.pos2 [x y z | look]', 'second corner of the selection'),
    'sel': ('.sel', 'what is selected'),
    'desel': ('.desel', 'forget the selection'),
    'set': ('.set <blocks>', 'fill the selection; blocks is NAME, NAME,NAME (equal chances) or NAME:weight,NAME:weight; AIR takes blocks away'),
    'replace': ('.replace <from> <to>', 'in the selection replace the blocks <from> (a list, or * for every block) with <to>'),
    'walls': ('.walls <blocks>', 'the 4 sides of the selection'),
    'hollow': ('.hollow', 'take away everything inside the selection but its outside layer'),
    'sphere': ('.sphere <blocks> <radius> [hollow] [at x y z]', 'a ball around you (or around x y z)'),
    'cyl': ('.cyl <blocks> <radius> <height> [hollow] [at x y z]', 'a tower standing on the block you stand on (or x y z), going up'),
    'copy': ('.copy', 'copy the selection (it stays in the clipboard with its place relative to you)'),
    'cut': ('.cut', 'copy the selection and take it away'),
    'paste': ('.paste [noair]', 'put the copied blocks down relative to where you are now (noair: air does not erase)'),
    'move': ('.move <distance> <direction> | .move <dx dy dz>', 'move what is in the selection (directions: up down north south east west)'),
    'stack': ('.stack <count> [direction | dx dy dz]', 'repeat what is in the selection count times, each next to the last (default: up)'),
    'undo': ('.undo [n]', 'take back the last n (1) edits'),
    'redo': ('.redo [n]', 'do again what was undone'),
    'save': ('.save', 'put all edits into the map file (the old file is kept as .bak)'),
    'tp': ('.tp <x y z>', 'go to a place (~ is relative to you)'),
    'spawn': ('.spawn', 'back to the spawn of the map'),
    'coords': ('.coords', 'where you are'),
    'clear': ('.clear', 'clear the chat'),
}


class Rend:
    # the state of editing: the selection, the clipboard, what can be undone / redone, and the edits of the map
    def __init__(self, world, block_names, edits=None, map_path=None, max_blocks=4_000_000, undo_blocks=8_000_000):
        self.world = world
        self.block_names = set(block_names)
        self.names = [AIR] + sorted(block_names) # AIR is 0 in the compact arrays of undo
        self.index = {name: i for i, name in enumerate(self.names)}
        self.map_path = map_path
        self.max_blocks = max_blocks
        self.undo_blocks = undo_blocks # the most blocks all the undo steps together remember; the oldest steps are forgotten first
        self.pos1 = None
        self.pos2 = None
        self.state = {} # the clipboard
        self.undo_stack = []
        self.redo_stack = []
        self.base_edits = list(edits or []) # in the map file already, and in the world: they can't be undone
        self.session_ops = [] # the ops done since, that still count (undone ones are gone)
        self.saved = list(self.base_edits)

    # --- the world

    def apply(self, changes, ops):
        # changes {position: new block name}: makes them and remembers them for undo; returns how many blocks really changed
        blocks = self.world.blocks
        real = {pos: name for pos, name in changes.items() if blocks.get(pos, AIR) != name}

        if not real: # nothing to do, so nothing to undo and nothing to keep in the edits
            return 0

        if len(real) > self.max_blocks:
            raise RendError(f'that would change {len(real):,} blocks, the limit is {self.max_blocks:,} (REND_MAX_BLOCKS in .env.pre)')

        positions = np.array(list(real), dtype=np.int32).reshape(-1, 3)
        before = np.array([self.index[blocks.get(pos, AIR)] for pos in real], dtype=np.uint8)
        after = np.array([self.index[name] for name in real.values()], dtype=np.uint8)
        self.world.edit(real)
        self.undo_stack.append(Change(positions, before, after, ops))
        self.redo_stack.clear()
        self.session_ops.extend(ops)

        total = sum(len(change) for change in self.undo_stack)

        while len(self.undo_stack) > 1 and total > self.undo_blocks: # forget the oldest steps
            total -= len(self.undo_stack.pop(0))

        return len(real)

    def revert(self, change, use_after):
        values = change.after if use_after else change.before
        self.world.edit({tuple(pos): self.names[v] for pos, v in zip(change.positions.tolist(), values.tolist())})

    def undo(self, count=1):
        # returns (how many edits were taken back, how many blocks that was)
        done = blocks = 0

        while done < count and self.undo_stack:
            change = self.undo_stack.pop()
            self.revert(change, use_after=False)
            self.redo_stack.append(change)

            for op in change.ops:
                self.session_ops = without(self.session_ops, op)

            done += 1
            blocks += len(change)

        return done, blocks

    def redo(self, count=1):
        done = blocks = 0

        while done < count and self.redo_stack:
            change = self.redo_stack.pop()
            self.revert(change, use_after=True)
            self.undo_stack.append(change)
            self.session_ops.extend(change.ops)
            done += 1
            blocks += len(change)

        return done, blocks

    def edits(self):
        # what the map file should hold: the edits it had and the ones of this session (with the copies a later paste needs)
        return self.base_edits + self.session_ops

    def unsaved(self):
        return self.edits() != self.saved

    def run_op(self, op):
        # works out an op and applies it; returns how many blocks changed
        changes = changes_of(op, self.world.blocks, self.state)

        if op['op'] == 'copy':
            self.session_ops.append(op) # the edits need it: a later paste uses what was copied

            return 0

        return self.apply(changes, [op])

    # --- understanding a command

    def block(self, text):
        return parse_blocks(text, self.block_names | {AIR})

    def number(self, text, what):
        try:
            return int(text)
        except ValueError:
            raise RendError(f'{what} has to be a whole number, not "{text}"')

    def coordinate(self, text, base, what):
        # a number, or ~ (the block you are in) or ~5 (5 away from it)
        if text.startswith('~'):
            return base + (self.number(text[1:], what) if len(text) > 1 else 0)

        return self.number(text, what)

    def position(self, args, ctx, what):
        # x y z (or ~ ~ ~), or "look", or nothing (where you stand)
        if not args:
            return tuple(ctx.player)

        if len(args) == 1 and args[0] == 'look':
            hit = ctx.look()

            if hit is None:
                raise RendError('you are not looking at a block (it has to be within 100 blocks)')

            return tuple(hit[0])

        if len(args) != 3:
            raise RendError(f'{what} needs x y z, or look, or nothing')

        return tuple(self.coordinate(args[i], ctx.player[i], 'a coordinate') for i in range(3))

    def selection(self):
        if self.pos1 is None or self.pos2 is None:
            raise RendError('select two corners first (.pos1 and .pos2)')

        return self.pos1, self.pos2

    def check_size(self, a, b):
        size = volume(a, b)

        if size > self.max_blocks:
            raise RendError(f'that is {size:,} blocks, the limit is {self.max_blocks:,} (REND_MAX_BLOCKS in .env.pre)')

    def run(self, line, ctx):
        # runs a command (a line that starts with "."); returns what to tell the user: a list of (kind, text); never raises
        words = line.strip().split()

        if not words or not words[0].startswith('.') or len(words[0]) < 2:
            return [(ERROR, 'a command starts with a . and a name, like .help')]

        name, args = words[0][1:].lower(), words[1:]
        handler = getattr(self, f'command_{name}', None)

        if handler is None or name not in HELP:
            close = [n for n in HELP if n.startswith(name[:2])][:5]

            return [(ERROR, f'unknown command .{name}' + (f' (maybe {", ".join("." + n for n in close)}?)' if close else ', try .help'))]

        try:
            return handler(args, ctx)
        except RendError as e:
            return [(ERROR, str(e))]
        except OSError as e: # the map file can't be written, ...
            return [(ERROR, f'{e.strerror or e}: {getattr(e, "filename", "") or ""}'.strip(' :'))]
        except Exception as e: # a bug in a command must not end the game (and the edits made so far are still there)
            traceback.print_exc()

            return [(ERROR, f'something went wrong in .{name}: {type(e).__name__}: {e}')]

    def usage(self, name):
        return f'usage: {HELP[name][0]}'

    def done(self, text, count):
        return [(OK, text if count else 'nothing changed (it was like that already)')]

    # --- the commands

    def command_help(self, args, ctx):
        if args:
            name = args[0].lstrip('.').lower()

            if name not in HELP:
                raise RendError(f'no command .{name}')

            return [(INFO, HELP[name][0]), (INFO, HELP[name][1])]

        lines = [(INFO, 'rend commands (type .help <command> for details):')]
        lines += [(INFO, ' '.join('.' + n for n in list(HELP)[i:i + 6])) for i in range(0, len(HELP), 6)]
        lines.append((INFO, 'anything that does not start with a . is a chat message'))

        return lines

    def command_pos1(self, args, ctx):
        return self.set_corner(1, args, ctx)

    def command_pos2(self, args, ctx):
        return self.set_corner(2, args, ctx)

    def set_corner(self, number, args, ctx):
        pos = self.position(args, ctx, f'.pos{number}')

        if number == 1:
            self.pos1 = pos
        else:
            self.pos2 = pos

        text = f'position {number} is {pos[0]} {pos[1]} {pos[2]}'

        if self.pos1 is not None and self.pos2 is not None:
            text += f' ({volume(self.pos1, self.pos2):,} blocks selected)'

        return [(OK, text)]

    def command_sel(self, args, ctx):
        if self.pos1 is None and self.pos2 is None:
            return [(INFO, 'nothing is selected (.pos1 and .pos2)')]

        a, b = self.pos1, self.pos2

        if a is None or b is None:
            return [(INFO, f'one corner: {a or b} (the other is missing)')]

        low, high = corners(a, b)

        return [(INFO, f'{low[0]} {low[1]} {low[2]} to {high[0]} {high[1]} {high[2]}: {high[0] - low[0] + 1} x {high[1] - low[1] + 1} x {high[2] - low[2] + 1} = {volume(a, b):,} blocks')]

    def command_desel(self, args, ctx):
        self.pos1 = self.pos2 = None

        return [(OK, 'selection cleared')]

    def region_op(self, kind, args, ctx, **extra):
        a, b = self.selection()
        self.check_size(a, b)
        op = {'op': kind, 'from': list(a), 'to': list(b), **extra}

        return self.run_op(op)

    def command_set(self, args, ctx):
        if len(args) != 1:
            raise RendError(self.usage('set'))

        blocks = self.block(args[0])
        count = self.region_op('set', args, ctx, blocks=blocks, seed=random.getrandbits(32))

        return self.done(f'set {count:,} blocks', count)

    def command_walls(self, args, ctx):
        if len(args) != 1:
            raise RendError(self.usage('walls'))

        count = self.region_op('walls', args, ctx, blocks=self.block(args[0]), seed=random.getrandbits(32))

        return self.done(f'built walls of {count:,} blocks', count)

    def command_hollow(self, args, ctx):
        count = self.region_op('hollow', args, ctx)

        return self.done(f'took away {count:,} blocks inside', count)

    def command_replace(self, args, ctx):
        if len(args) != 2:
            raise RendError(self.usage('replace'))

        match = ['*'] if args[0] == '*' else sorted(self.block(args[0]) if args[0].upper() != AIR else {AIR: 1})
        count = self.region_op('replace', args, ctx, match=match, blocks=self.block(args[1]), seed=random.getrandbits(32))

        return self.done(f'replaced {count:,} blocks', count)

    def shape_arguments(self, args, ctx):
        # the "hollow" and "at x y z" at the end of .sphere and .cyl: returns (the arguments before them, hollow, the center)
        args = list(args)
        center = tuple(ctx.player)
        hollow = False

        if 'at' in args:
            i = args.index('at')
            center = self.position(args[i + 1:], ctx, 'at')
            args = args[:i]

        if args and args[-1] == 'hollow':
            hollow = True
            args = args[:-1]

        return args, hollow, center

    def command_sphere(self, args, ctx):
        args, hollow, center = self.shape_arguments(args, ctx)

        if len(args) != 2:
            raise RendError(self.usage('sphere'))

        try:
            radius = float(args[1])
        except ValueError:
            raise RendError(f'the radius has to be a number, not "{args[1]}"')

        if not 0 < radius <= 500 or (4 / 3) * math.pi * radius ** 3 > self.max_blocks * 1.3:
            raise RendError('that radius is too big (or not above 0)')

        op = {'op': 'sphere', 'center': list(center), 'radius': radius, 'hollow': hollow, 'blocks': self.block(args[0]), 'seed': random.getrandbits(32)}
        count = self.run_op(op)

        return self.done(f'made a ball of {count:,} blocks', count)

    def command_cyl(self, args, ctx):
        args, hollow, center = self.shape_arguments(args, ctx)

        if len(args) != 3:
            raise RendError(self.usage('cyl'))

        try:
            radius = float(args[1])
        except ValueError:
            raise RendError(f'the radius has to be a number, not "{args[1]}"')

        height = self.number(args[2], 'the height')

        if radius <= 0 or height <= 0 or math.pi * radius * radius * height > self.max_blocks * 1.3:
            raise RendError('that radius / height is too big (or not above 0)')

        op = {'op': 'cyl', 'center': list(center), 'radius': radius, 'height': height, 'hollow': hollow, 'blocks': self.block(args[0]), 'seed': random.getrandbits(32)}
        count = self.run_op(op)

        return self.done(f'made a tower of {count:,} blocks', count)

    def command_copy(self, args, ctx):
        a, b = self.selection()
        self.check_size(a, b)
        self.run_op({'op': 'copy', 'from': list(a), 'to': list(b), 'origin': list(ctx.player)})

        return [(OK, f'copied {volume(a, b):,} blocks')]

    def command_cut(self, args, ctx):
        a, b = self.selection()
        self.check_size(a, b)
        self.run_op({'op': 'copy', 'from': list(a), 'to': list(b), 'origin': list(ctx.player)})
        count = self.run_op({'op': 'set', 'from': list(a), 'to': list(b), 'blocks': {AIR: 1}, 'seed': 0})

        return [(OK, f'cut {volume(a, b):,} blocks ({count:,} taken away)')]

    def command_paste(self, args, ctx):
        if args not in ([], ['noair']):
            raise RendError(self.usage('paste'))

        count = self.run_op({'op': 'paste', 'at': list(ctx.player), 'skip_air': bool(args)})

        return self.done(f'pasted, {count:,} blocks changed', count)

    def offset_from(self, args, ctx, size, default):
        # "<distance> <direction>", "<direction>" or "<dx> <dy> <dz>"; with a direction alone the distance is the size of the selection along it
        if len(args) == 3 and all(self.is_number(a) for a in args):
            return tuple(int(a) for a in args)

        if len(args) == 2 and self.is_number(args[0]) and args[1] in DIRECTIONS:
            step = DIRECTIONS[args[1]]
            return tuple(step[i] * int(args[0]) for i in range(3))

        if len(args) == 1 and args[0] in DIRECTIONS:
            step = DIRECTIONS[args[0]]
            return tuple(step[i] * size[i] for i in range(3))

        if not args and default:
            step = DIRECTIONS[default]
            return tuple(step[i] * size[i] for i in range(3))

        raise RendError('give a direction (up down north south east west), a distance and a direction, or 3 numbers')

    def is_number(self, text):
        try:
            int(text)

            return True
        except ValueError:
            return False

    def command_move(self, args, ctx):
        a, b = self.selection()
        self.check_size(a, b)
        low, high = corners(a, b)
        size = tuple(high[i] - low[i] + 1 for i in range(3))
        offset = self.offset_from(args, ctx, size, None)

        if offset == (0, 0, 0):
            raise RendError('that does not move anything')

        count = self.run_op({'op': 'move', 'from': list(a), 'to': list(b), 'offset': list(offset)})

        return self.done(f'moved, {count:,} blocks changed', count)

    def command_stack(self, args, ctx):
        a, b = self.selection()
        low, high = corners(a, b)
        size = tuple(high[i] - low[i] + 1 for i in range(3))

        if not args:
            raise RendError(self.usage('stack'))

        copies = self.number(args[0], 'the count')

        if copies < 1 or volume(a, b) * copies > self.max_blocks:
            raise RendError(f'the count has to be at least 1 and the result at most {self.max_blocks:,} blocks')

        offset = self.offset_from(args[1:], ctx, size, 'up')
        count = self.run_op({'op': 'stack', 'from': list(a), 'to': list(b), 'offset': list(offset), 'count': copies})

        return self.done(f'stacked {copies} times, {count:,} blocks changed', count)

    def command_undo(self, args, ctx):
        n = self.number(args[0], 'the number') if args else 1
        done, blocks = self.undo(n)

        return [(OK, f'undid {done} edit{"s" if done != 1 else ""} ({blocks:,} blocks)') if done else (INFO, 'nothing to undo')]

    def command_redo(self, args, ctx):
        n = self.number(args[0], 'the number') if args else 1
        done, blocks = self.redo(n)

        return [(OK, f'redid {done} edit{"s" if done != 1 else ""} ({blocks:,} blocks)') if done else (INFO, 'nothing to redo')]

    def command_save(self, args, ctx):
        if self.map_path is None:
            raise RendError('this map has no file to save to')

        write_edits(self.map_path, self.edits())
        self.saved = list(self.edits())

        return [(OK, f'saved {len(self.edits())} edits into {os.path.basename(self.map_path)} (the old file is {os.path.basename(self.map_path)}.bak)')]

    def command_tp(self, args, ctx):
        if len(args) != 3:
            raise RendError(self.usage('tp'))

        x, y, z = (self.coordinate(args[i], ctx.player[i], 'a coordinate') for i in range(3))
        ctx.teleport(x + 0.5, y, z + 0.5)

        return [(OK, f'went to {x} {y} {z}')]

    def command_spawn(self, args, ctx):
        ctx.spawn()

        return [(OK, 'back at the spawn')]

    def command_coords(self, args, ctx):
        return [(INFO, f'you are in the block {ctx.player[0]} {ctx.player[1]} {ctx.player[2]}')]

    def command_clear(self, args, ctx):
        return [('clear', '')]
