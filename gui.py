import time
import traceback

import pygame

from effects import REGISTRY, CATEGORIES
from fx import FxError, format_value, parse_value
from uidraw import clipboard_text

# the menu of effects, opened and closed with ]: a panel on the right side of the window with the effects that are on the screen (stack), the menu of effects to add (add) and the shaders (library)
# it does what the .fx and .shader commands do, on the same state, so both can be used together; it looks like the chat (JetBrains Mono, black, no rounded corners)
# it is drawn with immediate-mode widgets: every frame the widgets draw themselves and look at what the mouse did since the last frame, so what is drawn and what is clickable can't disagree (scrolling included)

TEXT = (0.92, 0.92, 0.92)
DIM = (0.52, 0.52, 0.52)
LINE = (1.0, 1.0, 1.0, 0.12)
ACCENT = (0.75, 0.9, 1.0) # like the commands typed in the chat
GOOD = (0.6, 1.0, 0.65)
BAD = (1.0, 0.45, 0.45)

TIP_TIME = 4.0 # seconds a message stays at the bottom
DELETE_TIME = 3.0 # seconds "sure?" waits for the second click on delete
HINT = 'wheel scrolls, shift + wheel changes the value under the pointer, right click puts it back'


def rgba(color, alpha):
    return (color[0], color[1], color[2], alpha)


def brighter(color, amount=0.35):
    return tuple(c + (1.0 - c) * amount for c in color[:3])


class Field:
    # a line of text being typed
    def __init__(self, text='', limit=64):
        self.text = text
        self.cursor = len(text)
        self.limit = limit

    def insert(self, text):
        text = ''.join(c for c in text if c.isprintable())[:max(0, self.limit - len(self.text))]
        self.text = self.text[:self.cursor] + text + self.text[self.cursor:]
        self.cursor += len(text)

    def key(self, event):
        # returns 'enter' or 'escape' when the line is finished, otherwise None
        key = event.key
        ctrl = bool(event.mod & pygame.KMOD_CTRL)

        if key == pygame.K_ESCAPE:
            return 'escape'
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return 'enter'

        if key == pygame.K_BACKSPACE and self.cursor:
            self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
            self.cursor -= 1
        elif key == pygame.K_DELETE:
            self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
        elif key == pygame.K_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif key == pygame.K_RIGHT:
            self.cursor = min(len(self.text), self.cursor + 1)
        elif key == pygame.K_HOME:
            self.cursor = 0
        elif key == pygame.K_END:
            self.cursor = len(self.text)
        elif key == pygame.K_v and ctrl:
            self.insert(clipboard_text())

        return None


class Gui:
    def __init__(self, painter, fx, notify, font_size, width, alpha):
        # painter: uidraw.Painter; fx: the fx.Fx state; notify(kind, text): where messages of actions that matter go too (the chat)
        # font_size is for a window 1080 high; width is a share of the window
        self.painter = painter
        self.fx = fx
        self.notify = notify
        self.font_size = font_size
        self.width_share = width
        self.alpha = alpha

        self.open = False
        self.tab = 'stack'
        self.scroll = {'stack': 0, 'add': 0, 'library': 0}
        self.content_height = 0
        self.expanded = set() # id() of the effects whose settings are shown
        self.colors_open = set() # (id() of an effect, setting) whose color has its three sliders shown
        self.category = 'all'
        self.search = Field()
        self.save_name = Field(limit=32)
        self.focus = None # (key, field, on_enter) of the line being typed
        self.drag = None # the key of the slider being dragged
        self.drag_before = None
        self.mouse = (-1, -1)
        self.presses = [] # (button, position) since the last frame
        self.releases = []
        self.wheels = [] # (dy, shift held)
        self.status = None # (kind, text, time)
        self.tip = ''
        self.pending_delete = None # (name, time): the shader that waits for the second click on delete
        self.pending_overwrite = None # the name that waits for the second click on save
        self.glyphs = {}
        self.clip_rect = None
        self.record = None # a test can put a dict here: it gets the place of every widget, by name

    # --- opening, typing

    def toggle(self):
        self.open = not self.open

        if self.open:
            self.mouse = pygame.mouse.get_pos()
        else:
            self.blur()
            self.drag = None

    def typing(self):
        return self.open and self.focus is not None

    def focus_field(self, key, field, on_enter=None):
        self.focus = (key, field, on_enter)
        pygame.key.start_text_input()
        pygame.key.set_repeat(400, 35)

    def blur(self):
        if self.focus is not None:
            self.focus = None
            pygame.key.stop_text_input()
            pygame.key.set_repeat()

    def say(self, kind, text, tell=False):
        # a message at the bottom of the menu; tell: it goes to the chat too
        self.status = (kind, text, time.time())

        if tell and self.notify:
            self.notify(kind, text)

    # --- events (they are only noted here, the widgets act on them in draw)

    def handle(self, event):
        # returns True if the event belongs to the menu (it is open, and it is a mouse event or typing into a line)
        if not self.open:
            return False

        t = event.type

        if t == pygame.MOUSEMOTION:
            self.mouse = event.pos

            return True

        if t == pygame.MOUSEBUTTONDOWN:
            self.mouse = event.pos
            self.presses.append((event.button, event.pos))

            return True

        if t == pygame.MOUSEBUTTONUP:
            self.releases.append(event.button)

            return True

        if t == pygame.MOUSEWHEEL:
            self.wheels.append((event.y, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)))

            return True

        if self.focus is not None:
            key, field, on_enter = self.focus

            if t == pygame.TEXTINPUT:
                field.insert(event.text)

                return True

            if t == pygame.KEYDOWN:
                done = field.key(event)

                if done == 'escape':
                    self.blur()
                elif done == 'enter':
                    self.blur()

                    if on_enter:
                        on_enter(field.text)

                return True

        return False

    def note(self, name, rect):
        if self.record is not None:
            self.record[name] = rect

    # --- looking at the mouse

    def inside(self, rect, pos):
        x, y, w, h = rect

        if not (x <= pos[0] < x + w and y <= pos[1] < y + h):
            return False

        if self.clip_rect is not None:
            cx, cy, cw, ch = self.clip_rect

            return cx <= pos[0] < cx + cw and cy <= pos[1] < cy + ch

        return True

    def visible(self, y, h):
        if self.clip_rect is None:
            return True

        return y + h > self.clip_rect[1] and y < self.clip_rect[1] + self.clip_rect[3]

    def hover(self, rect, tip=None):
        hot = self.inside(rect, self.mouse) and self.drag is None

        if hot and tip:
            self.tip = tip

        return hot

    def pressed(self, rect, buttons=(1,)):
        # the button that was pressed on the rectangle since the last frame, or None
        for i, (button, pos) in enumerate(self.presses_now):
            if button in buttons and self.inside(rect, pos):
                del self.presses_now[i]

                return button

        return None

    def wheel_over(self, rect):
        # shift + wheel over a rectangle: how many notches
        total = 0

        if self.inside(rect, self.mouse):
            for entry in list(self.wheels_now):
                if entry[1]:
                    total += entry[0]
                    self.wheels_now.remove(entry)

        return total

    # --- pieces

    def glyph(self, char, fallback):
        # a symbol the font has, or a plain letter
        if char not in self.glyphs:
            metrics = self.painter.font(self.fs).metrics(char)
            self.glyphs[char] = char if metrics and metrics[0] is not None else fallback

        return self.glyphs[char]

    def fit(self, text, width):
        # the text cut short with ... to fit
        p = self.painter

        if p.text_width(self.fs, text) <= width:
            return text

        low, high = 0, len(text)

        while low < high:
            mid = (low + high + 1) // 2

            if p.text_width(self.fs, text[:mid] + '...') <= width:
                low = mid
            else:
                high = mid - 1

        return text[:low] + '...'

    def wrap(self, text, width, lines):
        p = self.painter
        rows, row = [], ''

        for word in text.split(' '):
            candidate = word if not row else row + ' ' + word

            if p.text_width(self.fs, candidate) <= width or not row:
                row = candidate
            else:
                rows.append(row)
                row = word

        rows.append(row)

        if len(rows) > lines:
            rows = rows[:lines]
            rows[-1] = self.fit(rows[-1] + ' ...', width)

        return rows

    def button(self, x, y, label, color=TEXT, tip=None, enabled=True, underline=False, padx=None):
        # returns (clicked, width)
        p = self.painter
        padx = self.pad // 2 if padx is None else padx
        w = p.text_width(self.fs, label) + 2 * padx
        rect = (x, y, w, self.rh)

        if not self.visible(y, self.rh):
            return False, w

        self.note(f'button:{label}', rect)
        hot = enabled and self.hover(rect, tip)

        if hot:
            p.rect(x, y, w, self.rh, (1, 1, 1, 0.08))

        shown = brighter(color) if hot else (color if enabled else rgba(DIM, 0.6))
        p.text(x + padx, y + (self.rh - self.lh) // 2, label, self.fs, (*shown[:3], 1.0))

        if underline:
            p.rect(x + padx, y + self.rh - 3, w - 2 * padx, 2, (*ACCENT, 0.9))

        return (enabled and self.pressed(rect) == 1), w

    def field_box(self, x, y, w, field, focused, placeholder, now):
        p = self.painter
        h = self.rh
        p.rect(x, y + 2, w, h - 4, (1, 1, 1, 0.12 if focused else 0.06))

        if focused:
            p.rect(x, y + h - 4, w, 2, (*ACCENT, 0.9))

        padx = self.pad // 2
        room = w - 2 * padx
        shown = field.text

        while shown and p.text_width(self.fs, shown) > room: # a line longer than the box shows its end
            shown = shown[1:]

        ty = y + (h - self.lh) // 2

        if shown:
            p.text(x + padx, ty, shown, self.fs, (*TEXT, 1.0))
        elif placeholder:
            p.text(x + padx, ty, placeholder, self.fs, (*DIM, 1.0))

        if focused and int(now * 2) % 2 == 0:
            cut = len(field.text) - len(shown)
            caret = x + padx + p.text_width(self.fs, field.text[cut:field.cursor])
            p.rect(caret, ty, 2, self.lh, (1, 1, 1, 0.9))

    def edit_here(self, key, x, y, w, now):
        # a line being typed in place of a value; returns True while it is there
        if self.focus is None or self.focus[0] != key:
            return False

        self.field_box(x, y, w, self.focus[1], True, '', now)

        return True

    def start_edit(self, key, text, on_enter):
        self.focus_field(key, Field(text, 40), on_enter)

    def separator(self, y):
        if self.visible(y, 1):
            self.painter.rect(self.x0, y, self.cw, 1, LINE)

    # --- the settings of an effect

    def set_param(self, item, name, value):
        with self.fx.stack.change():
            item.values[name] = value

    def reset_param(self, item, param):
        self.set_param(item, param.name, param.default)

    def slider(self, y, key, label, value, low, high, apply, reset, tip, integer=False, indent=0, text=None, now=0.0):
        # a label, a line to drag along, the value; click the value to type it, right click puts it back
        # apply(value, live): live is True while dragging (one step of undo for the whole drag, taken at the end)
        p = self.painter

        if not self.visible(y, self.rh):
            return

        x = self.x0 + indent
        label_w = int(self.cw * 0.30) - indent
        value_w = int(self.cw * 0.20)
        track_x = x + label_w
        track_w = self.cw - indent - label_w - value_w - self.pad // 2
        value_x = track_x + track_w + self.pad // 2
        span = (high - low) or 1.0
        fraction = min(max((value - low) / span, 0.0), 1.0)

        p.text(x, y + (self.rh - self.lh) // 2, self.fit(label, label_w - 4), self.fs, (*DIM, 1.0))

        track_rect = (track_x - 6, y, track_w + 12, self.rh)
        value_rect = (value_x, y, value_w, self.rh)
        self.note(f'slider:{key}', track_rect)
        self.note(f'value:{key}', value_rect)
        hot = self.hover(track_rect, tip) or self.drag == key
        cy = y + self.rh // 2
        fill = int(track_w * fraction)
        p.rect(track_x, cy - 1, track_w, 2, (1, 1, 1, 0.20))
        p.rect(track_x, cy - 1, fill, 2, (*ACCENT, 0.9 if hot else 0.65))
        handle_h = round(14 * self.scale)
        p.rect(track_x + fill - 2, cy - handle_h // 2, 4, handle_h, (*(brighter(ACCENT) if hot else ACCENT), 1.0))

        shown = text if text is not None else (str(int(value)) if integer else f'{value:.4g}')

        if not self.edit_here(key, value_x, y, value_w, now):
            value_hot = self.hover(value_rect, 'click to type a value')
            p.text(value_x + self.pad // 2, y + (self.rh - self.lh) // 2, self.fit(shown, value_w - self.pad // 2), self.fs, (*(brighter(TEXT) if value_hot else TEXT), 1.0))

            if self.pressed(value_rect) == 1:
                self.start_edit(key, shown, lambda t: self.typed(t, apply))

        button = self.pressed(track_rect, (1, 3))

        if button == 3:
            reset()
        elif button == 1:
            self.drag = key
            self.drag_before = self.fx.stack.snapshot()

        if self.drag == key:
            apply(self.slider_value(self.mouse[0], track_x, track_w, low, high, integer), True)

        notches = self.wheel_over((x, y, self.cw - indent, self.rh))

        if notches:
            step = 1 if integer else span / 50.0
            apply(self.slider_value_of(value + notches * step, low, high, integer), False)

    def slider_value(self, mouse_x, track_x, track_w, low, high, integer):
        fraction = min(max((mouse_x - track_x) / max(track_w, 1), 0.0), 1.0)

        return self.slider_value_of(low + fraction * (high - low), low, high, integer)

    def slider_value_of(self, value, low, high, integer):
        value = min(max(value, low), high)

        if integer:
            return int(round(value))

        return round(value, 3 if high - low <= 10 else 2 if high - low <= 100 else 1)

    def typed(self, text, apply):
        # a value typed into a slider's value
        try:
            apply(float(text), False)
        except ValueError:
            self.say('error', f'"{text}" is not a number')

    def param_row(self, y, item, param, now):
        p = self.painter
        key = f'{id(item)}:{param.name}'
        name = param.name
        stack = self.fx.stack
        x = self.x0 + self.indent
        label_w = int(self.cw * 0.30) - self.indent
        value_x = x + label_w
        tip = f'{param.name}: {param.doc}' if param.doc else param.name
        value = item.values[name]
        sub_indent = self.indent + round(14 * self.scale)

        def reset():
            self.reset_param(item, param)

        def channel_apply(i):
            # sets one number of a color or a point
            def apply(v, live):
                v = self.slider_value_of(v, 0.0, 1.0, False)
                new = tuple(v if j == i else c for j, c in enumerate(item.values[name]))

                if live:
                    stack.set_live(item, name, new)
                else:
                    self.set_param(item, name, new)

            return apply

        if param.kind in ('float', 'int'):
            integer = param.kind == 'int'

            def apply(v, live):
                v = self.slider_value_of(v, param.low, param.high, integer)

                if live:
                    stack.set_live(item, name, v)
                else:
                    self.set_param(item, name, v)

            self.slider(y, key, name, value, param.low, param.high, apply, reset, tip, integer, self.indent, now=now)

            return y + self.rh

        row_visible = self.visible(y, self.rh)
        ty = y + (self.rh - self.lh) // 2
        rect = (value_x, y, self.cw - self.indent - label_w, self.rh)

        if row_visible:
            p.text(x, ty, self.fit(name, label_w - 4), self.fs, (*DIM, 1.0))

        hot = row_visible and self.hover(rect, tip)
        self.note(f'param:{key}', rect)

        if param.kind == 'bool':
            if row_visible:
                p.text(value_x, ty, 'yes' if value else 'no', self.fs, (*(ACCENT if value else DIM), 1.0))
                clicked = self.pressed(rect, (1, 3))

                if clicked == 1:
                    self.set_param(item, name, not value)
                elif clicked == 3:
                    reset()

            return y + self.rh

        if param.kind == 'choice':
            if row_visible:
                left, right = self.glyph('‹', '<'), self.glyph('›', '>')
                p.text(value_x, ty, f'{left} {value} {right}', self.fs, (*(brighter(TEXT) if hot else TEXT), 1.0))
                clicked = self.pressed(rect, (1, 3))
                notches = self.wheel_over(rect)
                choices = param.choices
                index = choices.index(value)

                if clicked == 1:
                    self.set_param(item, name, choices[(index + 1) % len(choices)])
                elif clicked == 3:
                    self.set_param(item, name, choices[(index - 1) % len(choices)])
                elif notches:
                    self.set_param(item, name, choices[(index + notches) % len(choices)])

            return y + self.rh

        if param.kind == 'color':
            open_key = (id(item), name)

            if row_visible:
                swatch = (value_x, y + 4, round(2.4 * self.lh), self.rh - 8)
                self.note(f'swatch:{key}', swatch)
                p.rect(*swatch, (*value, 1.0))
                p.rect(swatch[0], swatch[1], swatch[2], 1, (1, 1, 1, 0.35))
                p.rect(swatch[0], swatch[1] + swatch[3] - 1, swatch[2], 1, (1, 1, 1, 0.35))
                hex_x = value_x + swatch[2] + self.pad // 2
                hex_text = format_value(param, value)
                hex_rect = (hex_x, y, p.text_width(self.fs, hex_text) + 8, self.rh)

                if not self.edit_here(key, hex_x, y, self.x0 + self.cw - hex_x, now):
                    hex_hot = self.hover(hex_rect, 'click to type a color: #rrggbb, 1,0.5,0 or a name like orange')
                    p.text(hex_x, ty, hex_text, self.fs, (*(brighter(TEXT) if hex_hot else TEXT), 1.0))

                    if self.pressed(hex_rect) == 1:
                        self.start_edit(key, hex_text, lambda t: self.typed_value(item, param, t))

                clicked = self.pressed(swatch, (1, 3))

                if clicked == 1:
                    self.colors_open.symmetric_difference_update({open_key})
                elif clicked == 3:
                    reset()

            y += self.rh

            if open_key in self.colors_open:
                for i, channel in enumerate('rgb'):
                    self.slider(y, f'{key}:{channel}', channel, value[i], 0.0, 1.0, channel_apply(i), reset, tip, indent=sub_indent, now=now)
                    y += self.rh

            return y

        # a point: its text, and a slider for each of its two numbers
        point_text = format_value(param, value)

        if row_visible:
            if not self.edit_here(key, value_x, y, self.x0 + self.cw - value_x, now):
                p.text(value_x, ty, point_text, self.fs, (*(brighter(TEXT) if hot else TEXT), 1.0))

                if self.pressed(rect) == 1:
                    self.start_edit(key, point_text, lambda t: self.typed_value(item, param, t))

        y += self.rh

        for i, axis in enumerate('xy'):
            self.slider(y, f'{key}:{axis}', axis, value[i], 0.0, 1.0, channel_apply(i), reset, tip, indent=sub_indent, now=now)
            y += self.rh

        return y

    def typed_value(self, item, param, text):
        # a color or a point typed in
        try:
            value, note = parse_value(param, text)
        except FxError as e:
            self.say('error', str(e))

            return

        self.set_param(item, param.name, value)

    # --- the three tabs

    def tab_stack(self, y, now):
        fx = self.fx
        stack = fx.stack
        x = self.x0
        clicked, w = self.button(x, y, 'expand all', DIM, 'show the settings of every effect')

        if clicked:
            self.expanded = {id(i) for i in stack.items}

        clicked, w2 = self.button(x + w, y, 'collapse all', DIM, 'hide the settings')

        if clicked:
            self.expanded.clear()

        clicked, w3 = self.button(x + w + w2, y, 'clear', BAD, 'take every effect out (the picture as it is)')

        if clicked and stack.items:
            stack.clear()
            self.say('ok', 'cleared, the picture is shown as it is (undo brings it back)')

        y += self.rh

        def speed_apply(v, live):
            v = self.slider_value_of(v, -5.0, 5.0, False)

            if live:
                stack.speed = v
                stack.version += 1
            else:
                stack.set_speed(v)

        self.slider(y, 'speed', 'speed', stack.speed, -5.0, 5.0, speed_apply, lambda: stack.set_speed(1.0), 'the speed of every animation (1 is normal, 0 freezes them)', now=now)
        y += self.rh + self.pad // 2

        if not stack.items:
            for line in self.wrap('nothing on the screen: the picture is shown as it is. Add an effect in the add tab, or pick a shader in the library.', self.cw, 4):
                self.painter.text(x, y, line, self.fs, (*DIM, 1.0))
                y += self.lh

            return y

        alive = {id(i) for i in stack.items}
        self.expanded &= alive
        self.colors_open = {k for k in self.colors_open if k[0] in alive}

        for number, item in reversed(list(enumerate(stack.items, 1))): # the top of the stack (applied last) is at the top
            y = self.card(y, number, item, now)

        return y

    def card(self, y, number, item, now):
        p = self.painter
        stack = self.fx.stack
        effect = item.effect
        key = id(item)
        open_ = key in self.expanded
        up, down = self.glyph('↑', 'up'), self.glyph('↓', 'dn')
        cross = self.glyph('×', 'x')
        names = [('on' if item.enabled else 'off'), up, down, 'copy', cross]
        widths = [p.text_width(self.fs, n) + self.pad for n in names]
        buttons_w = sum(widths)
        right = self.x0 + self.cw - buttons_w

        if self.visible(y, self.rh):
            header = (self.x0, y, right - self.x0, self.rh)
            self.note(f'card:{number}', header)
            hot = self.hover(header, effect.doc)

            if hot:
                p.rect(*header, (1, 1, 1, 0.05))

            caret = self.glyph('▾' if open_ else '▸', 'v' if open_ else '>')
            color = TEXT if item.enabled else DIM
            tx = self.x0 + self.pad // 2
            ty = y + (self.rh - self.lh) // 2
            tx += p.text(tx, ty, caret, self.fs, (*DIM, 1.0)) + self.pad // 2
            tx += p.text(tx, ty, f'{number}', self.fs, (*DIM, 1.0)) + self.pad // 2
            p.text(tx, ty, effect.name, self.fs, (*(brighter(color) if hot else color), 1.0))

            if self.pressed(header) == 1:
                self.expanded.symmetric_difference_update({key})

            x = right
            tips = ['switch this effect on or off', 'move it up: it is applied after more of the others', 'move it down: it is applied before more of the others', 'copy it (the copy goes above it)', 'take it out of the stack']
            colors = [GOOD if item.enabled else DIM, TEXT, TEXT, TEXT, BAD]

            for i, label in enumerate(names):
                enabled = not (i == 1 and number == len(stack.items)) and not (i == 2 and number == 1)
                self.note(f'card:{number}:{["on", "up", "down", "copy", "remove"][i]}', (x, y, widths[i], self.rh))
                clicked, w = self.button(x, y, label, colors[i], tips[i], enabled, padx=self.pad // 2)

                if clicked:
                    if i == 0:
                        stack.set_enabled(number, not item.enabled)
                    elif i == 1:
                        stack.move(number, number + 1)
                    elif i == 2:
                        stack.move(number, number - 1)
                    elif i == 3:
                        stack.duplicate(number)
                        self.expanded.add(id(stack.items[number]))
                    else:
                        stack.remove(number)
                        self.say('ok', f'removed {effect.name}')

                x += widths[i]

        y += self.rh

        if open_:
            self.indent = round(14 * self.scale)

            for param in effect.params:
                y = self.param_row(y, item, param, now)

            clicked, w = self.button(self.x0 + self.indent, y, 'reset settings', DIM, 'every setting of this effect back to what it starts as')

            if clicked:
                stack.reset(number)

            y += self.rh
            self.indent = 0

        self.separator(y)

        return y + 1 + self.pad // 4

    def tab_add(self, y, now):
        p = self.painter
        x = self.x0

        box = (x, y, self.cw, self.rh)
        self.note('search', box)
        focused = self.focus is not None and self.focus[0] == 'search'
        self.field_box(x, y, self.cw, self.search, focused, 'search the effects', now)

        if self.visible(y, self.rh) and self.pressed(box) == 1:
            self.focus_field('search', self.search)

        y += self.rh + self.pad // 4
        cx = x

        for name in ['all'] + CATEGORIES:
            clicked, w = self.button(cx, y, name, ACCENT if self.category == name else DIM, None, underline=self.category == name, padx=self.pad // 3)
            cx += w

            if clicked:
                self.category = name

        y += self.rh + self.pad // 4
        self.separator(y)
        y += 1 + self.pad // 4

        query = self.search.text.strip().lower()
        name_w = int(self.cw * 0.30)
        shown = 0

        for name, effect in REGISTRY.items():
            if self.category != 'all' and effect.category != self.category:
                continue

            if query and query not in name and query not in effect.doc.lower():
                continue

            shown += 1

            if self.visible(y, self.rh):
                rect = (x, y, self.cw, self.rh)
                self.note(f'add:{name}', rect)
                hot = self.hover(rect, f'{name}: {effect.doc}  (click to add it on top)')

                if hot:
                    p.rect(*rect, (1, 1, 1, 0.07))

                ty = y + (self.rh - self.lh) // 2
                p.text(x + self.pad // 2, ty, name, self.fs, (*(ACCENT if hot else TEXT), 1.0))
                p.text(x + name_w, ty, self.fit(effect.doc, self.cw - name_w - 4), self.fs, (*DIM, 1.0))

                if self.pressed(rect) == 1:
                    item = self.fx.stack.add(effect)
                    self.expanded.add(id(item))
                    self.say('ok', f'added {name} on top ({len(self.fx.stack.items)} in the stack)')

            y += self.rh

        if not shown:
            p.text(x, y, 'no effect matches', self.fs, (*DIM, 1.0))
            y += self.rh

        return y

    def unique_name(self, base):
        names = set(self.fx.library.names())
        name = base

        for n in range(2, 1000):
            if name not in names:
                break

            name = f'{base}-{n}'

        return name

    def tab_library(self, y, now):
        p = self.painter
        fx = self.fx
        lib = fx.library
        x = self.x0

        label_w = p.text_width(self.fs, 'save as')
        p.text(x, y + (self.rh - self.lh) // 2, 'save as', self.fs, (*DIM, 1.0))
        save_w = p.text_width(self.fs, 'save') + self.pad
        box_x = x + label_w + self.pad // 2
        box = (box_x, y, self.cw - label_w - save_w - self.pad, self.rh)
        self.note('save field', box)
        focused = self.focus is not None and self.focus[0] == 'save'
        self.field_box(box[0], y, box[2], self.save_name, focused, 'a name like my-look', now)

        def save(text=None):
            name = self.save_name.text.strip().lower()

            try:
                existed = name in lib.custom

                if existed and self.pending_overwrite != name:
                    self.pending_overwrite = name
                    self.say('error', f'{name} already exists: click save again to replace it')

                    return

                fx.save(name, overwrite=existed)
                self.pending_overwrite = None
                self.save_name.text = ''
                self.save_name.cursor = 0
                self.say('ok', f'saved as {name}', tell=True)
            except FxError as e:
                self.say('error', str(e))

        if self.visible(y, self.rh) and self.pressed(box) == 1:
            self.focus_field('save', self.save_name, save)

        clicked, w = self.button(box[0] + box[2] + self.pad // 2, y, 'save', ACCENT, 'keep what is on the screen as a new shader of your own', bool(self.save_name.text.strip()))

        if clicked:
            save()

        y += self.rh
        clicked, w = self.button(x, y, 'clear (no effects)', BAD, 'take every effect out')

        if clicked and fx.stack.items:
            fx.stack.clear()
            fx.current = None
            self.say('ok', 'cleared, the picture is shown as it is')

        y += self.rh + self.pad // 4
        self.separator(y)
        y += 1 + self.pad // 4

        names = lib.names()
        built_in = [d['name'] for d in lib.defaults]
        modified = fx.modified()

        for group, members in (('built in', [n for n in names if n in built_in]), ('yours', [n for n in names if n not in built_in])):
            p.text(x, y + (self.rh - self.lh) // 2, group + ('' if members else ' (none yet: save one above)'), self.fs, (*DIM, 1.0))
            y += self.rh

            for name in members:
                y = self.shader_row(y, names.index(name) + 1, name, modified, now)

        return y

    def shader_row(self, y, number, name, modified, now):
        p = self.painter
        fx = self.fx
        lib = fx.library
        x = self.x0
        mine = not lib.is_default(name)
        current = fx.current == name
        labels = (['rename', 'copy', 'delete'] if mine else ['copy'])

        if self.pending_delete and self.pending_delete[0] == name and time.time() - self.pending_delete[1] < DELETE_TIME:
            labels[-1] = 'sure?' if mine else labels[-1]
        elif self.pending_delete and self.pending_delete[0] == name:
            self.pending_delete = None

        widths = [p.text_width(self.fs, label) + self.pad for label in labels]
        right = x + self.cw - sum(widths)

        if not self.visible(y, self.rh):
            return y + self.rh

        row = (x, y, right - x, self.rh)
        self.note(f'shader:{name}', row)
        shader = lib.get(name)
        hot = self.hover(row, f'{name}: ' + (shader['description'] or f'{len(shader["effects"])} effects') + '  (click to show it)')

        if hot:
            p.rect(*row, (1, 1, 1, 0.06))

        if current:
            p.rect(x, y + 3, 3, self.rh - 6, (*ACCENT, 1.0))

        ty = y + (self.rh - self.lh) // 2
        tx = x + self.pad // 2 + 4
        p.text(tx, ty, f'{number}', self.fs, (*DIM, 1.0))
        tx += p.text_width(self.fs, '99') + self.pad // 2
        key = f'rename:{name}'

        if not self.edit_here(key, tx, y, right - tx, now):
            label = name + (' *' if current and modified else '')
            p.text(tx, ty, self.fit(label, right - tx - 4), self.fs, (*(ACCENT if current else (brighter(TEXT) if hot else TEXT)), 1.0))

            if self.pressed(row) == 1:
                fx.use(name)
                self.say('ok', f'shader {name}')

        bx = right

        for i, label in enumerate(labels):
            color = BAD if label in ('delete', 'sure?') else TEXT
            clicked, w = self.button(bx, y, label, color, None, padx=self.pad // 2)
            bx += widths[i]

            if not clicked:
                continue

            try:
                if label == 'rename':
                    self.start_edit(key, name, lambda t, old=name: self.rename(old, t))
                elif label == 'copy':
                    new = self.unique_name(f'{name}-copy')
                    lib.copy(name, new)
                    self.say('ok', f'copied as {new}', tell=True)
                elif label == 'delete':
                    self.pending_delete = (name, time.time())
                    self.say('info', f'click again to delete {name} for good')
                else:
                    fx.delete(name)
                    self.pending_delete = None
                    self.say('ok', f'deleted {name} for good', tell=True)
            except FxError as e:
                self.say('error', str(e))

        return y + self.rh

    def rename(self, old, new):
        try:
            self.fx.rename(old, new.strip().lower())
            self.say('ok', f'{old} is now {new.strip().lower()}', tell=True)
        except FxError as e:
            self.say('error', str(e))

    # --- drawing

    def draw(self, width, height, now=None):
        if not self.open:
            return

        now = time.time() if now is None else now
        p = self.painter
        self.scale = height / 1080
        self.fs = max(11, round(self.font_size * self.scale))
        self.lh = p.font(self.fs).get_linesize()
        self.rh = self.lh + round(10 * self.scale)
        self.pad = round(16 * self.scale)
        self.indent = 0
        panel_w = max(round(440 * self.scale), round(width * self.width_share))
        px = width - panel_w
        self.x0 = px + self.pad
        self.cw = panel_w - 2 * self.pad

        self.presses_now = self.presses
        self.presses = []
        self.releases_now, self.releases = self.releases, []
        self.wheels_now = self.wheels
        self.wheels = []
        self.tip = ''
        self.clip_rect = None

        p.begin(width, height)

        try:
            self.draw_panel(width, height, now, px, panel_w)
        except Exception:
            traceback.print_exc()
            self.open = False
            self.blur()
            self.say('error', 'the menu had an error and was closed (see the console)', tell=True)
        finally:
            p.end()

    def draw_panel(self, width, height, now, px, panel_w):
        p = self.painter
        releases, self.releases_now = self.releases_now, []
        p.rect(px, 0, panel_w, height, (0, 0, 0, self.alpha))
        p.rect(px, 0, 1, height, LINE)

        # the top: which shader, undo / redo, the tabs
        fx = self.fx
        y = self.pad
        title = (fx.current or 'new') + (' *' if fx.modified() else '')
        p.text(self.x0, y + (self.rh - self.lh) // 2, self.fit(title, self.cw // 2), self.fs, (*TEXT, 1.0))
        undo_w = p.text_width(self.fs, 'undo') + self.pad
        redo_w = p.text_width(self.fs, 'redo') + self.pad
        clicked, w = self.button(self.x0 + self.cw - undo_w - redo_w, y, 'undo', TEXT, 'take back the last change', bool(fx.stack.undo_list))

        if clicked:
            fx.stack.undo()

        clicked, w = self.button(self.x0 + self.cw - redo_w, y, 'redo', TEXT, 'do the change again', bool(fx.stack.redo_list))

        if clicked:
            fx.stack.redo()

        y += self.rh
        tx = self.x0

        for tab, label in (('stack', f'stack {len(fx.stack.items)}'), ('add', 'add'), ('library', f'library {len(fx.library.names())}')):
            clicked, w = self.button(tx, y, label, ACCENT if self.tab == tab else DIM, None, underline=self.tab == tab)
            tx += w

            if clicked and self.tab != tab:
                self.tab = tab
                self.blur()

        y += self.rh + self.pad // 4
        p.rect(px, y, panel_w, 1, LINE)
        top = y + 1

        # the bottom: a message, or what the pointer is over
        foot_lines = 2
        foot_h = foot_lines * self.lh + self.pad
        bottom = height - foot_h
        p.rect(px, bottom, panel_w, 1, LINE)

        # the part that scrolls
        view_h = bottom - top
        self.clip_rect = (px, top, panel_w, view_h)
        p.clip(px, top, panel_w, view_h)
        scroll = self.scroll[self.tab]
        start = top + self.pad // 2 - scroll

        if self.tab == 'stack':
            end = self.tab_stack(start, now)
        elif self.tab == 'add':
            end = self.tab_add(start, now)
        else:
            end = self.tab_library(start, now)

        self.content_height = end - start + self.pad
        p.unclip()
        self.clip_rect = None

        # scrolling (the wheel notches that no slider took) and the scroll bar
        max_scroll = max(0, self.content_height - view_h)

        for dy, shift in self.wheels_now:
            if px <= self.mouse[0] and top <= self.mouse[1] < bottom:
                scroll -= dy * self.rh * 3

        self.scroll[self.tab] = min(max(scroll, 0), max_scroll)

        if max_scroll:
            bar_h = max(self.rh, int(view_h * view_h / self.content_height))
            bar_y = top + int((view_h - bar_h) * self.scroll[self.tab] / max_scroll)
            p.rect(width - 4, bar_y, 3, bar_h, (1, 1, 1, 0.25))

        # a click on nothing leaves the line being typed
        if self.presses_now and self.focus is not None:
            self.blur()

        if 1 in releases and self.drag is not None:
            self.fx.stack.commit(self.drag_before)
            self.drag = None

        # the bottom text
        if self.status and now - self.status[2] < TIP_TIME:
            kind, text = self.status[0], self.status[1]
            color = BAD if kind == 'error' else GOOD if kind == 'ok' else TEXT
        elif self.tip:
            text, color = self.tip, DIM
        else:
            text, color = HINT, DIM

        for i, line in enumerate(self.wrap(text, self.cw, foot_lines)):
            p.text(self.x0, bottom + self.pad // 2 + i * self.lh, line, self.fs, (*color, 1.0))
