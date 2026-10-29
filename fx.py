import contextlib
import difflib
import json
import math
import os
import re

import log
from effects import REGISTRY

# the stack of effects that is on the screen (the active shader), the library of saved shaders, and how a typed value is understood
# effects/ is the menu of effects, fxrender.py draws a stack, fxcommands.py is the chat commands, gui.py is the menu opened with ]

NAME_MAX = 32 # the longest name of a shader
NAME_PATTERN = re.compile(r'[a-z0-9][a-z0-9_-]*') # lowercase letters, digits, _ and - (it is the name of a file)


class FxError(Exception):
    # something a person typed that can't be done; the message says why and goes to the chat
    pass


# ------ values

COLOR_NAMES = {
    'black': (0.0, 0.0, 0.0), 'white': (1.0, 1.0, 1.0), 'gray': (0.5, 0.5, 0.5), 'grey': (0.5, 0.5, 0.5), 'silver': (0.75, 0.75, 0.75),
    'red': (1.0, 0.0, 0.0), 'green': (0.0, 1.0, 0.0), 'blue': (0.0, 0.0, 1.0), 'yellow': (1.0, 1.0, 0.0), 'cyan': (0.0, 1.0, 1.0), 'magenta': (1.0, 0.0, 1.0),
    'orange': (1.0, 0.5, 0.0), 'pink': (1.0, 0.4, 0.7), 'purple': (0.6, 0.2, 0.9), 'brown': (0.45, 0.25, 0.1), 'teal': (0.0, 0.5, 0.5),
    'navy': (0.0, 0.0, 0.5), 'lime': (0.5, 1.0, 0.0), 'gold': (1.0, 0.8, 0.0), 'sky': (0.5, 0.8, 1.0),
}

BOOLEAN_WORDS = {'yes': True, 'true': True, 'on': True, '1': True, 'no': False, 'false': False, 'off': False, '0': False}


def fmt(value):
    return f'{value:g}'


def format_value(param, value):
    # a value the way it is typed and shown
    if param.kind in ('float', 'int'):
        return fmt(value)
    if param.kind == 'bool':
        return 'yes' if value else 'no'
    if param.kind == 'color':
        return '#' + ''.join(f'{round(min(max(c, 0.0), 1.0) * 255):02x}' for c in value)
    if param.kind == 'point':
        return f'{fmt(value[0])},{fmt(value[1])}'

    return value


def kind_text(param):
    # what a setting is, for the info of an effect
    if param.kind == 'float':
        return f'number {fmt(param.low)} to {fmt(param.high)}'
    if param.kind == 'int':
        return f'whole number {fmt(param.low)} to {fmt(param.high)}'
    if param.kind == 'bool':
        return 'yes or no'
    if param.kind == 'choice':
        return 'one of ' + ', '.join(param.choices)
    if param.kind == 'color':
        return 'color (#rrggbb, r,g,b or a name like orange)'

    return 'point (x,y from 0 to 1, 0,0 is the bottom left)'


def parse_number(text, what):
    try:
        value = float(text)
    except ValueError:
        raise FxError(f'{what} has to be a number, not "{text}"')

    if not math.isfinite(value):
        raise FxError(f'{what} has to be a number, not "{text}"')

    return value


def parse_color(text, what):
    t = text.lower().strip()

    if t in COLOR_NAMES:
        return COLOR_NAMES[t]

    if t.startswith('#'):
        digits = t[1:]

        if len(digits) == 3:
            digits = ''.join(d * 2 for d in digits)

        if len(digits) != 6 or any(d not in '0123456789abcdef' for d in digits):
            raise FxError(f'{what} has to be a color like #ff8000, #f80, 1,0.5,0 or a name like orange, not "{text}"')

        return tuple(int(digits[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    parts = t.split(',')

    if len(parts) != 3:
        raise FxError(f'{what} has to be a color like #ff8000, #f80, 1,0.5,0 or a name like orange, not "{text}"')

    values = [parse_number(part, what) for part in parts]

    if max(values) > 1.0:
        values = [v / 255.0 for v in values] # 0 to 255, like in a paint program

    return tuple(min(max(v, 0.0), 1.0) for v in values)


def parse_point(text, what):
    parts = text.split(',')

    if len(parts) != 2:
        raise FxError(f'{what} has to be a point like 0.5,0.5 (x,y from 0 to 1, 0,0 is the bottom left), not "{text}"')

    return tuple(min(max(parse_number(part, what), -1.0), 2.0) for part in parts)


def parse_choice(text, choices, what):
    key = text.lower()

    if key in choices:
        return key

    if key.isdigit() and 1 <= int(key) <= len(choices):
        return choices[int(key) - 1] # the number in the list, counting from 1

    starts = [c for c in choices if c.startswith(key)]

    if len(starts) == 1:
        return starts[0]

    raise FxError(f'{what} can be {", ".join(choices)}, not "{text}"')


def parse_value(param, text):
    # returns (value, note); the note is empty, or tells that a number was moved into the allowed range
    what = param.name

    if param.kind in ('float', 'int'):
        number = parse_number(text, what)

        if param.kind == 'int':
            number = int(round(number))

        value = min(max(number, param.low), param.high)

        if param.kind == 'float':
            value = float(value)

        note = f'{what} {fmt(number)} is outside {fmt(param.low)} to {fmt(param.high)}, using {fmt(value)}' if value != number else ''

        return value, note

    if param.kind == 'bool':
        key = text.lower()

        if key not in BOOLEAN_WORDS:
            raise FxError(f'{what} has to be yes or no (also on, off, true, false, 1, 0), not "{text}"')

        return BOOLEAN_WORDS[key], ''

    if param.kind == 'choice':
        return parse_choice(text, param.choices, what), ''

    if param.kind == 'color':
        return parse_color(text, what), ''

    return parse_point(text, what), ''


def value_text(param, value):
    # a value from a file as text, so it goes through the same checks as a typed one
    if isinstance(value, bool):
        return 'yes' if value else 'no'
    if isinstance(value, (list, tuple)):
        return ','.join(repr(float(v)) for v in value)

    return str(value)


def json_value(value):
    return [float(v) for v in value] if isinstance(value, tuple) else value


# ------ finding things by name

def find_name(text, names, what, hint):
    # exact, then the only name that starts with it; otherwise says what is close
    key = text.lower()

    if key in names:
        return key

    starts = [n for n in names if n.startswith(key)]

    if len(starts) == 1:
        return starts[0]

    close = starts[:4] or difflib.get_close_matches(key, names, n=3, cutoff=0.6)

    raise FxError(f'no {what} "{text}"' + (f' (maybe {", ".join(close)}?)' if close else f', {hint}'))


def effect_named(text):
    return REGISTRY[find_name(text, list(REGISTRY), 'effect', '.fx list shows them')]


def param_named(effect, text):
    return effect.by_name[find_name(text, list(effect.by_name), f'setting of {effect.name}', f'.fx info {effect.name} shows them')]


def parse_params(effect, words):
    # the words after an effect name: name=value, or values one after the other in the order .fx info lists the settings of the effect
    # (the settings that every effect has, mix and speed and seed, can only be named); returns ({name: value}, [notes])
    values = {}
    notes = []
    positional = []

    for word in words:
        if '=' in word:
            name, _, text = word.partition('=')

            if not text:
                raise FxError(f'{name}= needs a value')

            param = param_named(effect, name)
            values[param.name], note = parse_value(param, text)

            if note:
                notes.append(note)
        else:
            positional.append(word)

    free = [p for p in effect.own if p.name not in values]

    if len(positional) > len(free):
        raise FxError(f'{effect.name} has {len(effect.own)} settings ({", ".join(p.name for p in effect.own) or "none"}); to set mix, speed or seed write mix=0.5')

    for param, text in zip(free, positional):
        values[param.name], note = parse_value(param, text)

        if note:
            notes.append(note)

    return values, notes


# ------ the stack

class Instance:
    # one effect in a stack, with its values
    def __init__(self, effect, values=None, enabled=True):
        self.effect = effect
        self.values = {p.name: p.default for p in effect.params}
        self.enabled = enabled
        self.time = 0.0 # how far its animation has gone (seconds, times its speed)

        if values:
            self.values.update(values)

    def copy(self):
        return Instance(self.effect, dict(self.values), self.enabled)

    def non_default(self):
        return {p.name: self.values[p.name] for p in self.effect.params if self.values[p.name] != p.default}

    def to_json(self):
        data = {'effect': self.effect.name}
        params = {name: json_value(value) for name, value in self.non_default().items()}

        if params:
            data['params'] = params
        if not self.enabled:
            data['enabled'] = False

        return data


def instance_from_json(data, where, warnings):
    # an effect from a file; settings that are wrong are left out (the file keeps working), and every problem is added to warnings
    if not isinstance(data, dict) or data.get('effect') not in REGISTRY:
        raise FxError(f'{where}: no effect {data.get("effect") if isinstance(data, dict) else data!r}')

    effect = REGISTRY[data['effect']]
    values = {}

    for name, raw in (data.get('params') or {}).items():
        param = effect.by_name.get(name)

        if param is None:
            warnings.append(f'{where}: {effect.name} has no setting {name}')
            continue

        try:
            values[name], note = parse_value(param, value_text(param, raw))
        except FxError as e:
            warnings.append(f'{where}: {e}')

    return Instance(effect, values, data.get('enabled', True) is not False)


class Stack:
    # the effects on the screen, the first one is applied first; every change can be undone
    def __init__(self, undo_steps=100):
        self.items = []
        self.speed = 1.0 # the speed of every animation
        self.undo_steps = undo_steps
        self.undo_list = []
        self.redo_list = []
        self.version = 0 # goes up with every change, so what draws the stack knows when to look again

    def snapshot(self):
        data = {'effects': [item.to_json() for item in self.items]}

        if self.speed != 1.0:
            data['speed'] = self.speed

        return data

    def restore(self, data):
        self.items = [instance_from_json(d, 'undo', []) for d in data['effects']]
        self.speed = data.get('speed', 1.0)

    @contextlib.contextmanager
    def change(self):
        # everything done inside is one step of undo (and nothing is remembered if nothing changed)
        before = self.snapshot()

        try:
            yield
        finally:
            if self.snapshot() != before:
                self.undo_list.append(before)
                del self.undo_list[:-self.undo_steps]
                self.redo_list.clear()
                self.version += 1

    def set_live(self, item, name, value):
        # a value that is being dragged: it shows at once, but only commit() (when the drag ends) makes it one step of undo
        item.values[name] = value
        self.version += 1

    def commit(self, before):
        # before: the snapshot from before the drag
        if self.snapshot() != before:
            self.undo_list.append(before)
            del self.undo_list[:-self.undo_steps]
            self.redo_list.clear()
            self.version += 1

    def undo(self):
        if not self.undo_list:
            return False

        self.redo_list.append(self.snapshot())
        self.restore(self.undo_list.pop())
        self.version += 1

        return True

    def redo(self):
        if not self.redo_list:
            return False

        self.undo_list.append(self.snapshot())
        self.restore(self.redo_list.pop())
        self.version += 1

        return True

    def index(self, number):
        # the place in the list of the effect with this number (counting from 1)
        if not self.items:
            raise FxError('the stack is empty (.fx add <effect> puts one in)')

        if not 1 <= number <= len(self.items):
            raise FxError(f'there is no effect {number}, the stack has {len(self.items)} (1 to {len(self.items)})')

        return number - 1

    def add(self, effect, values=None, at=None):
        # at the end (the last one is applied last, on top of the others), or at a place
        with self.change():
            item = Instance(effect, values)

            if at is None or at > len(self.items):
                self.items.append(item)
            else:
                self.items.insert(max(at, 1) - 1, item)

        return item

    def remove(self, number):
        with self.change():
            return self.items.pop(self.index(number))

    def move(self, number, to):
        # to is the number the effect should have afterwards
        i = self.index(number)

        with self.change():
            item = self.items.pop(i)
            self.items.insert(min(max(to, 1), len(self.items) + 1) - 1, item)

        return self.items.index(item) + 1

    def swap(self, a, b):
        i, j = self.index(a), self.index(b)

        with self.change():
            self.items[i], self.items[j] = self.items[j], self.items[i]

    def duplicate(self, number):
        i = self.index(number)

        with self.change():
            self.items.insert(i + 1, self.items[i].copy())

    def set_value(self, number, name, value):
        item = self.items[self.index(number)]

        with self.change():
            item.values[name] = value

    def reset(self, number, name=None):
        item = self.items[self.index(number)]

        with self.change():
            for p in item.effect.params:
                if name is None or p.name == name:
                    item.values[p.name] = p.default

    def set_enabled(self, number, enabled):
        item = self.items[self.index(number)]

        with self.change():
            item.enabled = enabled

    def set_speed(self, speed):
        with self.change():
            self.speed = speed

    def clear(self):
        with self.change():
            self.items = []
            self.speed = 1.0

    def load(self, data):
        # puts a whole shader in (one step of undo)
        with self.change():
            self.restore(data)

    def passes(self):
        # how many full-screen passes the stack costs
        return sum(len(item.effect.passes) for item in self.items if item.enabled)


# ------ the library

def dumps_shader(data):
    # the file of a shader, with every effect on one line so it is easy to read and edit
    lines = ['{', f'  "name": {json.dumps(data["name"], ensure_ascii=False)},']

    if data.get('description'):
        lines.append(f'  "description": {json.dumps(data["description"], ensure_ascii=False)},')
    if data.get('speed', 1.0) != 1.0:
        lines.append(f'  "speed": {data["speed"]},')

    effects = [f'    {json.dumps(effect, ensure_ascii=False)}' for effect in data['effects']]
    lines.append('  "effects": [' + ('\n' + ',\n'.join(effects) + '\n  ' if effects else '') + ']')
    lines.append('}')

    return '\n'.join(lines) + '\n'


def shader_from_json(name, data, where, warnings):
    # a shader from a file, checked: effects that don't exist are left out
    if not isinstance(data, dict) or not isinstance(data.get('effects', []), list):
        raise FxError(f'{where}: a shader has to be {{"effects": [...]}}')

    effects = []

    for i, entry in enumerate(data.get('effects', []), 1):
        try:
            effects.append(instance_from_json(entry, f'{where}, effect {i}', warnings).to_json())
        except FxError as e:
            warnings.append(str(e))

    speed = data.get('speed', 1.0)
    speed = float(speed) if isinstance(speed, (int, float)) and not isinstance(speed, bool) and math.isfinite(speed) else 1.0

    return {'name': name, 'description': str(data.get('description', '')), 'speed': speed, 'effects': effects}


def snapshot_of(shader):
    data = {'effects': shader['effects']}

    if shader['speed'] != 1.0:
        data['speed'] = shader['speed']

    return data


class Library:
    # the shaders you can choose from: the built-in ones (read only, in the order they are written in the defaults file), then your own (files in a folder, in alphabetical order)
    def __init__(self, defaults_path, custom_dir):
        self.defaults_path = defaults_path
        self.custom_dir = custom_dir
        self.defaults = []
        self.custom = {}
        self.warnings = []
        self.load()

    def warn(self, text):
        self.warnings.append(text)
        log.error('Shader file problem', problem=text)

    def load(self):
        self.defaults = []
        self.custom = {}
        found = []

        try:
            with open(self.defaults_path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            log.error('Default shaders read failed', path=self.defaults_path, error=e)
            data = {'shaders': []}

        for entry in data.get('shaders', []):
            name = entry.get('name', '') if isinstance(entry, dict) else ''

            if not NAME_PATTERN.fullmatch(name) or any(d['name'] == name for d in self.defaults):
                self.warn(f'{self.defaults_path}: bad or repeated shader name {name!r}')
                continue

            try:
                self.defaults.append(shader_from_json(name, entry, name, found))
            except FxError as e:
                self.warn(str(e))

        if not self.defaults: # without a first shader there is nothing to start on: an empty one is always there
            self.defaults.append({'name': 'default', 'description': 'the picture as it is', 'speed': 1.0, 'effects': []})

        reserved = {d['name'] for d in self.defaults}

        if os.path.isdir(self.custom_dir):
            for file in sorted(os.listdir(self.custom_dir)):
                stem, ext = os.path.splitext(file)

                if ext.lower() != '.json':
                    continue

                path = os.path.join(self.custom_dir, file)

                if not NAME_PATTERN.fullmatch(stem) or len(stem) > NAME_MAX or stem in reserved:
                    self.warn(f'{path}: the file name is not a usable shader name (lowercase letters, digits, _ and -, up to {NAME_MAX}, and not one of the built-in names)')
                    continue

                try:
                    with open(path, encoding='utf-8') as f:
                        self.custom[stem] = shader_from_json(stem, json.load(f), file, found)
                except (OSError, ValueError, FxError) as e:
                    self.warn(f'{path}: {e}')

        for text in found:
            self.warn(text)

    def names(self):
        return [d['name'] for d in self.defaults] + sorted(self.custom, key=lambda n: (n.lower(), n))

    def is_default(self, name):
        return any(d['name'] == name for d in self.defaults)

    def get(self, name):
        for d in self.defaults:
            if d['name'] == name:
                return d

        if name in self.custom:
            return self.custom[name]

        raise FxError(f'no shader "{name}"')

    def resolve(self, text):
        # what a person typed (a name, a number from .shader list, or the start of a name) to the name of a shader
        names = self.names()

        if text.isdigit():
            if not 1 <= int(text) <= len(names):
                raise FxError(f'there is no shader {text}, they are 1 to {len(names)} (.shader list)')

            return names[int(text) - 1]

        return find_name(text, names, 'shader', '.shader list shows them')

    def check_new_name(self, name):
        if not NAME_PATTERN.fullmatch(name) or len(name) > NAME_MAX:
            raise FxError(f'a shader name is lowercase letters, digits, _ and - (up to {NAME_MAX}), like my-look, not "{name}"')

        if self.is_default(name):
            raise FxError(f'"{name}" is one of the built-in shaders, pick another name')

    def write(self, shader):
        os.makedirs(self.custom_dir, exist_ok=True)
        path = os.path.join(self.custom_dir, shader['name'] + '.json')
        temporary = path + '.tmp'

        with open(temporary, 'w', encoding='utf-8', newline='\n') as f:
            f.write(dumps_shader(shader))

        os.replace(temporary, path) # a crash in the middle can't leave half a shader

    def save(self, name, snapshot, description=None, overwrite=False):
        # puts a stack (its snapshot) into the library as a new shader of your own
        self.check_new_name(name)

        if name in self.custom and not overwrite:
            raise FxError(f'"{name}" already exists (.shader save {name} overwrite replaces it)')

        old = self.custom.get(name)
        shader = {'name': name, 'description': description if description is not None else (old['description'] if old else ''), 'speed': snapshot.get('speed', 1.0), 'effects': snapshot['effects']}
        self.write(shader)
        self.custom[name] = shader

        return shader

    def delete(self, name):
        if self.is_default(name):
            raise FxError(f'"{name}" is built in and can not be deleted')

        self.get(name)
        os.remove(os.path.join(self.custom_dir, name + '.json'))
        del self.custom[name]

    def rename(self, old, new):
        if self.is_default(old):
            raise FxError(f'"{old}" is built in and can not be renamed (.shader copy {old} <name> makes a copy of your own)')

        self.check_new_name(new)

        if new in self.custom:
            raise FxError(f'"{new}" already exists')

        shader = dict(self.get(old), name=new)
        self.write(shader)
        os.remove(os.path.join(self.custom_dir, old + '.json'))
        del self.custom[old]
        self.custom[new] = shader

    def copy(self, source, new):
        self.check_new_name(new)

        if new in self.custom:
            raise FxError(f'"{new}" already exists')

        shader = dict(self.get(source), name=new)
        self.write(shader)
        self.custom[new] = shader


class Fx:
    # the whole state: the library, the stack on the screen, and which shader of the library the stack came from
    def __init__(self, library, undo_steps=100):
        self.library = library
        self.stack = Stack(undo_steps)
        self.current = None # the name of the shader the stack was loaded from (None: it is a new one)
        self.use(library.names()[0])
        self.stack.undo_list.clear()

    def use(self, name):
        shader = self.library.get(name)
        self.stack.load(snapshot_of(shader))
        self.current = name

    def modified(self):
        # the stack is not what the shader of that name has (or it has no name yet and something is in it)
        if self.current is None or self.current not in self.library.names():
            return bool(self.stack.items)

        return self.stack.snapshot() != snapshot_of(self.library.get(self.current))

    def cycle(self, step):
        names = self.library.names()

        if self.current in names:
            index = (names.index(self.current) + step) % len(names)
        else:
            index = 0 if step > 0 else len(names) - 1

        self.use(names[index])

        return names[index]

    def neighbor_effects(self):
        # the effects of the shaders that Backslash goes to from here (the next one and the previous one), so they can be got ready
        names = self.library.names()
        index = names.index(self.current) if self.current in names else None
        near = names[:1] if index is None else [names[(index + 1) % len(names)], names[(index - 1) % len(names)]]

        return [REGISTRY[entry['effect']] for name in near for entry in self.library.get(name)['effects']]

    def save(self, name, description=None, overwrite=False):
        self.library.save(name, self.stack.snapshot(), description, overwrite)
        self.current = name

    def delete(self, name):
        self.library.delete(name)

        if self.current == name:
            self.current = None # what is on the screen stays, it just has no shader behind it any more

    def rename(self, old, new):
        self.library.rename(old, new)

        if self.current == old:
            self.current = new
