import time
import traceback

from effects import REGISTRY, CATEGORIES, CATEGORY_DOCS
from fx import FxError, fmt, format_value, kind_text, effect_named, param_named, parse_params, parse_value, find_name, instance_from_json

# the chat commands .fx (the stack of effects on the screen) and .shader (the library of saved shaders)
# like rend.py, run() gets a line and returns what to tell the user as a list of (kind, text), and never raises

OK, INFO, ERROR = 'ok', 'info', 'error'

DELETE_WAIT = 60 # seconds a shader waits to be deleted for good: the command has to be repeated within this time

ALIASES = {
    'fx': {'rm': 'remove', 'del': 'remove', 'delete': 'remove', 'duplicate': 'dup', 'copy': 'dup', 'show': 'stack', 'ls': 'list', 'view': 'info'},
    'shader': {'ls': 'list', 'load': 'use', 'previous': 'prev', 'show': 'info', 'remove': 'delete', 'rm': 'delete', 'del': 'delete', 'cp': 'copy', 'mv': 'rename'},
}

HELP = {
    'fx': [
        ('.fx list [category]', 'the menu of effects (categories: ' + ', '.join(CATEGORIES) + ')'),
        ('.fx info <effect>', 'what an effect does and all its settings'),
        ('.fx add <effect> [settings]', 'put an effect on top of the stack (it is applied after the others); settings are name=value, or just the values in the order .fx info lists them: .fx add dither bayer8 4 2'),
        ('.fx insert <n> <effect> [settings]', 'put an effect at place n of the stack'),
        ('.fx stack', 'the effects that are on the screen, the top one is applied last (on top of the others), 1 is applied first'),
        ('.fx set <n> <settings>', 'change settings of effect n: .fx set 2 levels=4 type=bayer4 (or .fx set 2 levels 4)'),
        ('.fx reset <n> [setting]', 'put one setting (or all) of effect n back to what it starts as'),
        ('.fx remove <n>', 'take effect n out of the stack'),
        ('.fx move <n> <to>', 'move effect n to place <to>'),
        ('.fx up <n> [steps] / .fx down <n> [steps]', 'move an effect up (towards the top: applied after more of the others) or down'),
        ('.fx top <n> / .fx bottom <n>', 'make effect n the last / the first one applied'),
        ('.fx swap <a> <b>', 'swap two effects'),
        ('.fx dup <n>', 'copy effect n (right after it)'),
        ('.fx on <n> / .fx off <n> / .fx toggle <n>', 'switch an effect on or off without removing it'),
        ('.fx mix <n> <0-1>', 'how much of effect n is used (0 none, 1 all)'),
        ('.fx clear', 'take every effect out: the picture is shown as it is'),
        ('.fx undo [n] / .fx redo [n]', 'take back / do again changes to the stack'),
        ('.fx speed [x]', 'the speed of every animation (1 is normal, 0 freezes them)'),
        ('.fx cost', 'how many full-screen passes the stack needs'),
    ],
    'shader': [
        ('.shader list', 'every shader (built-in ones first, then yours in alphabetical order); the one on the screen is marked with *'),
        ('.shader use <name | n>', 'show a shader (Backslash goes through them all, Shift+Backslash goes back)'),
        ('.shader next / .shader prev', 'the next / previous one'),
        ('.shader save <name> [overwrite]', 'keep what is on the screen as a new shader of your own (it joins the list and Backslash)'),
        ('.shader add <name | n>', 'put the effects of a shader on top of the stack'),
        ('.shader reset', 'throw away your changes: the shader as it was saved'),
        ('.shader rename <name> <new>', 'rename a shader of yours'),
        ('.shader copy <name> <new>', 'copy any shader (also a built-in one) into one of yours'),
        ('.shader delete <name>', 'delete a shader of yours for good (repeat the command to confirm)'),
        ('.shader info [name]', 'what is in a shader'),
        ('.fx clear', 'the way to "no shader": nothing on the screen (or .shader use default)'),
    ],
}


def plural(count, word):
    return f'{count} {word}' + ('' if count == 1 else 's')


class FxCommands:
    def __init__(self, fx):
        self.fx = fx
        self.pending_delete = None # (name, time) of the shader that waits for its second delete command

    @property
    def stack(self):
        return self.fx.stack

    @property
    def library(self):
        return self.fx.library

    # --- running

    def run(self, line):
        words = line.strip().split()

        if not words or words[0].lower() not in ('.fx', '.shader'):
            return [(ERROR, 'a shader command starts with .fx or .shader')]

        group, args = words[0][1:].lower(), words[1:]

        if not args or args[0].lower() == 'help':
            return self.help_lines(group)

        sub = args[0].lower()
        handler = getattr(self, f'{group}_{ALIASES[group].get(sub, sub)}', None)

        if handler is None:
            names = self.sub_names(group)
            close = [n for n in names if n.startswith(sub[:2])][:5]

            return [(ERROR, f'unknown command .{group} {sub}' + (f' (maybe {", ".join(close)}?)' if close else f', try .{group} help'))]

        try:
            return handler(args[1:])
        except FxError as e:
            return [(ERROR, str(e))]
        except OSError as e: # a shader file can't be written, ...
            return [(ERROR, f'{e.strerror or e}: {getattr(e, "filename", "") or ""}'.strip(' :'))]
        except Exception as e: # a bug in a command must not end the game
            traceback.print_exc()

            return [(ERROR, f'something went wrong in .{group} {sub}: {type(e).__name__}: {e}')]

    def sub_names(self, group):
        prefix = group + '_'

        return [n[len(prefix):] for n in dir(self) if n.startswith(prefix)]

    def help_lines(self, group=None):
        lines = []

        for g in ([group] if group in HELP else list(HELP)):
            lines.append((INFO, f'.{g} commands:'))
            lines += [(INFO, f'{usage}  -  {what}') for usage, what in HELP[g]]

        if group not in HELP:
            lines.append((INFO, 'start with: .fx list, then .fx add <effect>'))

        return lines

    def number(self, text, what='the effect'):
        try:
            return int(text)
        except ValueError:
            raise FxError(f'{what} is a whole number (its number in .fx stack), not "{text}"')

    def need(self, args, count, usage):
        if len(args) < count:
            raise FxError(f'usage: {usage}')

    # --- showing things

    def params_text(self, item):
        shown = ' '.join(f'{name}={format_value(item.effect.by_name[name], value)}' for name, value in item.non_default().items())

        return shown or '(starting values)'

    def stack_lines(self):
        fx = self.fx
        name = fx.current or 'new'
        header = f'on the screen: {name}' + (' (changed, .shader save to keep it)' if fx.modified() else '')

        if self.stack.speed != 1.0:
            header += f'   animation speed {fmt(self.stack.speed)}'

        if not self.stack.items:
            return [(INFO, header), (INFO, 'no effects: the picture is shown as it is (.fx add <effect>, or .shader list)')]

        lines = [(INFO, header + '   (the top one is applied last, 1 is applied first)')]

        for i, item in reversed(list(enumerate(self.stack.items, 1))):
            lines.append((INFO, f'{i:>2} {"" if item.enabled else "(off) "}{item.effect.name}  {self.params_text(item)}'))

        return lines

    def fx_list(self, args):
        if args:
            category = find_name(args[0], CATEGORIES, 'category', 'categories are ' + ', '.join(CATEGORIES))
            effects = [e for e in REGISTRY.values() if e.category == category]

            return [(INFO, f'{category}: {CATEGORY_DOCS[category]}')] + [(INFO, f'{e.name} - {e.doc}') for e in effects] + [(INFO, '.fx info <effect> shows the settings')]

        lines = [(INFO, f'{len(REGISTRY)} effects (.fx list <category> says what they do, .fx info <effect> shows the settings):')]

        for category in CATEGORIES:
            names = [e.name for e in REGISTRY.values() if e.category == category]
            lines.append((INFO, f'{category} ({len(names)}): ' + ' '.join(names)))

        return lines

    def fx_info(self, args):
        self.need(args, 1, '.fx info <effect>')
        effect = effect_named(args[0])
        lines = [(INFO, f'{effect.name} ({effect.category}): {effect.doc}')]

        if effect.own:
            lines.append((INFO, 'settings (name=value, or only the values in this order):'))

        for i, p in enumerate(effect.own, 1):
            lines.append((INFO, f'{i} {p.name}: {kind_text(p)}, starts as {format_value(p, p.default)} - {p.doc}'))

        extra = [p for p in effect.params if p not in effect.own]
        lines.append((INFO, 'every effect also has (name=value only): ' + ', '.join(f'{p.name} ({kind_text(p)}, starts as {format_value(p, p.default)})' for p in extra)))

        return lines

    # --- changing the stack

    def settings(self, effect, words, allow_pairs=False):
        # the settings in the words after an effect: name=value, positional values, and (when allow_pairs) "name value"
        if allow_pairs:
            joined = []
            i = 0

            while i < len(words):
                if '=' not in words[i] and words[i].lower() in effect.by_name and i + 1 < len(words):
                    joined.append(f'{words[i].lower()}={words[i + 1]}')
                    i += 2
                else:
                    joined.append(words[i])
                    i += 1

            words = joined

        return parse_params(effect, words)

    def fx_add(self, args):
        self.need(args, 1, '.fx add <effect> [settings]')
        effect = effect_named(args[0])
        values, notes = self.settings(effect, args[1:])
        item = self.stack.add(effect, values)
        number = self.stack.items.index(item) + 1

        return [(OK, f'added {effect.name} as effect {number}' + (' (applied last)' if number == len(self.stack.items) else ''))] + [(INFO, n) for n in notes]

    def fx_insert(self, args):
        self.need(args, 2, '.fx insert <n> <effect> [settings]')
        place = self.number(args[0], 'the place')
        effect = effect_named(args[1])
        values, notes = self.settings(effect, args[2:])
        item = self.stack.add(effect, values, at=place)

        return [(OK, f'put {effect.name} at place {self.stack.items.index(item) + 1}')] + [(INFO, n) for n in notes]

    def fx_stack(self, args):
        return self.stack_lines()

    def fx_set(self, args):
        self.need(args, 2, '.fx set <n> <name=value> ...')
        number = self.number(args[0])
        item = self.stack.items[self.stack.index(number)]
        values, notes = self.settings(item.effect, args[1:], allow_pairs=True)

        with self.stack.change():
            for name, value in values.items():
                item.values[name] = value

        return [(OK, f'effect {number} ({item.effect.name}): ' + ' '.join(f'{n}={format_value(item.effect.by_name[n], v)}' for n, v in values.items()))] + [(INFO, n) for n in notes]

    def fx_reset(self, args):
        self.need(args, 1, '.fx reset <n> [setting]')
        number = self.number(args[0])
        item = self.stack.items[self.stack.index(number)]
        name = param_named(item.effect, args[1]).name if len(args) > 1 else None
        self.stack.reset(number, name)

        return [(OK, f'effect {number} ({item.effect.name}): ' + (f'{name} is back to {format_value(item.effect.by_name[name], item.effect.by_name[name].default)}' if name else 'all settings are back to their starting values'))]

    def fx_remove(self, args):
        self.need(args, 1, '.fx remove <n>')
        item = self.stack.remove(self.number(args[0]))

        return [(OK, f'removed {item.effect.name} ({len(self.stack.items)} left)')]

    def fx_move(self, args):
        self.need(args, 2, '.fx move <n> <to>')
        item = self.stack.items[self.stack.index(self.number(args[0]))]
        place = self.stack.move(self.number(args[0]), self.number(args[1], 'the place'))

        return [(OK, f'{item.effect.name} is now effect {place} of {len(self.stack.items)}')]

    def step(self, args, direction, usage):
        self.need(args, 1, usage)
        number = self.number(args[0])
        steps = self.number(args[1], 'the steps') if len(args) > 1 else 1
        item = self.stack.items[self.stack.index(number)]
        place = self.stack.move(number, number + direction * steps)

        return [(OK, f'{item.effect.name} is now effect {place} of {len(self.stack.items)}')]

    def fx_up(self, args):
        return self.step(args, +1, '.fx up <n> [steps]')

    def fx_down(self, args):
        return self.step(args, -1, '.fx down <n> [steps]')

    def fx_top(self, args):
        self.need(args, 1, '.fx top <n>')
        item = self.stack.items[self.stack.index(self.number(args[0]))]
        self.stack.move(self.number(args[0]), len(self.stack.items))

        return [(OK, f'{item.effect.name} is now the last one applied')]

    def fx_bottom(self, args):
        self.need(args, 1, '.fx bottom <n>')
        item = self.stack.items[self.stack.index(self.number(args[0]))]
        self.stack.move(self.number(args[0]), 1)

        return [(OK, f'{item.effect.name} is now the first one applied')]

    def fx_swap(self, args):
        self.need(args, 2, '.fx swap <a> <b>')
        self.stack.swap(self.number(args[0]), self.number(args[1]))

        return [(OK, f'swapped {args[0]} and {args[1]}')]

    def fx_dup(self, args):
        self.need(args, 1, '.fx dup <n>')
        number = self.number(args[0])
        self.stack.duplicate(number)

        return [(OK, f'copied effect {number} (the copy is effect {number + 1})')]

    def switch(self, args, enabled, usage):
        self.need(args, 1, usage)
        number = self.number(args[0])
        item = self.stack.items[self.stack.index(number)]
        self.stack.set_enabled(number, enabled if enabled is not None else not item.enabled)

        return [(OK, f'{item.effect.name} is {"on" if item.enabled else "off"}')]

    def fx_on(self, args):
        return self.switch(args, True, '.fx on <n>')

    def fx_off(self, args):
        return self.switch(args, False, '.fx off <n>')

    def fx_toggle(self, args):
        return self.switch(args, None, '.fx toggle <n>')

    def fx_mix(self, args):
        self.need(args, 2, '.fx mix <n> <0-1>')
        number = self.number(args[0])
        item = self.stack.items[self.stack.index(number)]
        value, note = parse_value(item.effect.by_name['mix'], args[1])
        self.stack.set_value(number, 'mix', value)

        return [(OK, f'{item.effect.name} is used for {fmt(value * 100)}%')] + ([(INFO, note)] if note else [])

    def fx_clear(self, args):
        if not self.stack.items:
            return [(OK, 'nothing was on the screen')]

        count = len(self.stack.items)
        self.stack.clear()

        return [(OK, f'cleared {plural(count, "effect")}: the picture is shown as it is (.fx undo brings them back)')]

    def fx_undo(self, args):
        count = self.number(args[0], 'the count') if args else 1
        done = sum(1 for _ in range(count) if self.stack.undo())

        return [(OK, f'took back {done} change{"" if done == 1 else "s"}')] if done else [(INFO, 'nothing to take back')]

    def fx_redo(self, args):
        count = self.number(args[0], 'the count') if args else 1
        done = sum(1 for _ in range(count) if self.stack.redo())

        return [(OK, f'did {done} change{"" if done == 1 else "s"} again')] if done else [(INFO, 'nothing to do again')]

    def fx_speed(self, args):
        if not args:
            return [(INFO, f'animation speed is {fmt(self.stack.speed)} (.fx speed <x>: 1 is normal, 0 freezes, negative runs backwards)')]

        try:
            value = float(args[0])
        except ValueError:
            raise FxError(f'the speed is a number, not "{args[0]}"')

        if not -50.0 <= value <= 50.0:
            raise FxError('the speed is between -50 and 50')

        self.stack.set_speed(value)

        return [(OK, f'animation speed is {fmt(value)}')]

    def fx_cost(self, args):
        items = [i for i in self.stack.items if i.enabled]

        passes = self.stack.passes()

        return [(INFO, f'{plural(len(items), "effect")} on, {passes} full-screen {"pass" if passes == 1 else "passes"} per frame')]

    # --- the shaders

    def shader_list(self, args):
        names = self.library.names()
        built_in = [d['name'] for d in self.library.defaults]
        mark = lambda i, n: f'{i}{"*" if n == self.fx.current else ""} {n}'
        lines = [(INFO, 'built in: ' + '  '.join(mark(i, n) for i, n in enumerate(names, 1) if n in built_in))]
        yours = [mark(i, n) for i, n in enumerate(names, 1) if n not in built_in]
        lines.append((INFO, 'yours: ' + ('  '.join(yours) if yours else 'none yet (.shader save <name> keeps what is on the screen)')))
        lines.append((INFO, '* is on the screen' + (' (changed since it was saved)' if self.fx.modified() and self.fx.current else '') + '; .shader use <name or number>, Backslash goes to the next'))

        return lines

    def shader_use(self, args):
        self.need(args, 1, '.shader use <name | n>')
        name = self.library.resolve(args[0])
        self.fx.use(name)

        return [(OK, f'shader {name}' + (f' ({plural(len(self.stack.items), "effect")})' if self.stack.items else ''))]

    def shader_next(self, args):
        return [(OK, f'shader {self.fx.cycle(+1)}')]

    def shader_prev(self, args):
        return [(OK, f'shader {self.fx.cycle(-1)}')]

    def shader_save(self, args):
        self.need(args, 1, '.shader save <name> [overwrite]')
        name = args[0].lower()
        overwrite = len(args) > 1 and args[1].lower() == 'overwrite'

        if len(args) > 1 and not overwrite:
            raise FxError(f'usage: .shader save <name> [overwrite] (a name has no spaces, "{args[1]}" is not "overwrite")')

        existed = name in self.library.custom
        self.fx.save(name, overwrite=overwrite)

        return [(OK, f'saved as {name}' + (' (replaced the old one)' if existed else '') + f', it is shader {self.library.names().index(name) + 1} in the list')]

    def shader_add(self, args):
        self.need(args, 1, '.shader add <name | n>')
        name = self.library.resolve(args[0])
        shader = self.library.get(name)

        if not shader['effects']:
            return [(INFO, f'{name} has no effects, nothing to add')]

        with self.stack.change():
            for entry in shader['effects']:
                self.stack.items.append(instance_from_json(entry, name, []))

        return [(OK, f'added the {plural(len(shader["effects"]), "effect")} of {name} on top (now {len(self.stack.items)} in the stack)')]

    def shader_reset(self, args):
        name = self.fx.current

        if name is None or name not in self.library.names():
            raise FxError('what is on the screen has no saved shader to go back to (.fx clear empties it)')

        self.fx.use(name)

        return [(OK, f'{name} is back as it was saved')]

    def shader_rename(self, args):
        self.need(args, 2, '.shader rename <name> <new>')
        old = self.library.resolve(args[0])
        self.fx.rename(old, args[1].lower())

        return [(OK, f'{old} is now {args[1].lower()}')]

    def shader_copy(self, args):
        self.need(args, 2, '.shader copy <name> <new>')
        source = self.library.resolve(args[0])
        self.library.copy(source, args[1].lower())

        return [(OK, f'copied {source} as {args[1].lower()}')]

    def shader_delete(self, args):
        self.need(args, 1, '.shader delete <name>')
        name = self.library.resolve(args[0])

        if self.library.is_default(name):
            raise FxError(f'{name} is built in and can not be deleted')

        now = time.monotonic()

        if self.pending_delete and self.pending_delete[0] == name and now - self.pending_delete[1] < DELETE_WAIT:
            self.pending_delete = None
            self.fx.delete(name)

            return [(OK, f'deleted {name} for good')]

        self.pending_delete = (name, now)

        return [(INFO, f'this deletes {name} for good: type the same command again to do it (.shader delete {name})')]

    def shader_info(self, args):
        name = self.library.resolve(args[0]) if args else self.fx.current

        if name is None:
            return self.stack_lines()

        shader = self.library.get(name)
        kind = 'built in' if self.library.is_default(name) else 'yours'
        lines = [(INFO, f'{name} ({kind}): ' + (shader['description'] or plural(len(shader['effects']), 'effect')))]

        for i, entry in enumerate(shader['effects'], 1):
            effect = REGISTRY[entry['effect']]
            params = ' '.join(f'{k}={format_value(effect.by_name[k], tuple(v) if isinstance(v, list) else v)}' for k, v in (entry.get('params') or {}).items())
            lines.append((INFO, f'{i:>2} {"" if entry.get("enabled", True) else "(off) "}{effect.name}  {params or "(starting values)"}'))

        if not shader['effects']:
            lines.append((INFO, 'no effects: the picture as it is'))

        return lines

    # --- Tab

    def complete(self, words, current):
        # the words typed before the one being finished, and that one; returns the names that can follow (the ones that start with `current`)
        # words[0] is .fx or .shader
        group = words[0][1:].lower()
        done = [w.lower() for w in words[1:]]

        if group not in ('fx', 'shader'):
            return []

        if '=' in current:
            return self.value_choices(words, current)

        if not done:
            names = self.sub_names(group) + ['help']
        else:
            sub = ALIASES[group].get(done[0], done[0])
            names = self.complete_fx(sub, done) if group == 'fx' else self.complete_shader(sub, done)

        return sorted(n for n in set(names) if n.lower().startswith(current.lower()))

    def complete_fx(self, sub, done):
        if sub in ('add', 'info') and len(done) == 1:
            return list(REGISTRY)

        if sub == 'insert' and len(done) == 2:
            return list(REGISTRY)

        if sub == 'list' and len(done) == 1:
            return CATEGORIES

        effect = None

        try:
            if sub == 'add' and len(done) >= 2:
                effect = effect_named(done[1])
            elif sub == 'insert' and len(done) >= 3:
                effect = effect_named(done[2])
            elif sub in ('set', 'reset') and len(done) >= 2:
                effect = self.stack.items[int(done[1]) - 1].effect
        except (FxError, ValueError, IndexError):
            return []

        if effect is None:
            return []

        if sub == 'reset':
            return [p.name for p in effect.params] if len(done) == 2 else []

        return [p.name + '=' for p in effect.params]

    def complete_shader(self, sub, done):
        if sub in ('use', 'add', 'info', 'rename', 'copy', 'delete') and len(done) == 1:
            return self.library.names() if sub != 'rename' and sub != 'delete' else list(self.library.custom)

        return []

    def value_choices(self, words, current):
        # for a word like type=ba: the choices of that setting, written with the name in front (so the whole word can be finished)
        if '=' not in current or len(words) < 3:
            return []

        sub = words[1].lower()
        name, _, partial = current.partition('=')

        try:
            if sub == 'add' and len(words) >= 3:
                effect = effect_named(words[2])
            elif sub == 'insert' and len(words) >= 4:
                effect = effect_named(words[3])
            elif sub == 'set':
                effect = self.stack.items[int(words[2]) - 1].effect
            else:
                return []

            param = param_named(effect, name)
        except (FxError, ValueError, IndexError):
            return []

        if param.kind == 'choice':
            return sorted(f'{param.name}={c}' for c in param.choices if c.startswith(partial.lower()))

        if param.kind == 'bool':
            return sorted(f'{param.name}={c}' for c in ('yes', 'no') if c.startswith(partial.lower()))

        return []
