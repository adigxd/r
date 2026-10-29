import time

import pygame

from uidraw import Painter, clipboard_text

# the chat: T opens it, Enter sends what was typed, Escape closes it
# a line that starts with a . is a rend command (see rend.py); anything else is a chat message
# it is drawn over the finished picture (after the post-processing), as rectangles and text (uidraw.py)

COLORS = {'chat': (1.0, 1.0, 1.0), 'ok': (0.6, 1.0, 0.65), 'info': (0.85, 0.85, 0.85), 'error': (1.0, 0.45, 0.45), 'command': (0.75, 0.9, 1.0)}
MAX_TEXT = 256 # the longest line that can be typed


class Chat:
    def __init__(self, program, font_path, font_size, lines, history, fade_time, width, commands=(), completer=None):
        # program: the shader of ui.vert / ui.frag (None: no drawing, only the typing and the messages, for tests)
        # font_size is for a window 1080 high; lines are shown while the chat is closed; history is how many lines are remembered; fade_time how long a message stays; width is a share of the window
        self.painter = Painter(program, font_path) # also used by the menu of effects
        self.font_size = font_size
        self.lines = lines
        self.history = history
        self.fade_time = fade_time
        self.width = width
        self.commands = sorted(commands) # the names of the commands, for Tab
        self.completer = completer # completer(words, current): the words that can come after the words of a command typed so far, for Tab (None: only the names of commands are finished)
        self.open = False
        self.text = ''
        self.cursor = 0
        self.sent = [] # what was sent, for the up / down keys
        self.sent_index = None
        self.messages = [] # (kind, text, time)
        self.scroll = 0 # how many lines back from the newest the chat is scrolled
        self.ignore_text = None # (text, until): the letter that opened the chat arrives as typing too, and must not be in the line
        self.wrap_memory = None # (what was asked, the rows) of the last wrap_input

    # --- messages

    def add(self, kind, text, now=None):
        self.messages.append((kind, text, time.time() if now is None else now))
        del self.messages[:-self.history]

        if self.scroll:
            self.scroll = 0

    def clear(self):
        self.messages.clear()
        self.scroll = 0

    # --- typing

    def open_chat(self, now=None):
        self.open = True
        self.text = ''
        self.cursor = 0
        self.sent_index = None
        self.scroll = 0
        self.ignore_text = ('t', (time.time() if now is None else now) + 0.3)
        pygame.key.start_text_input()
        pygame.key.set_repeat(400, 35) # backspace and the arrows repeat while the chat is open

    def close_chat(self):
        self.open = False
        pygame.key.stop_text_input()
        pygame.key.set_repeat()

    def insert(self, text):
        text = ''.join(c for c in text if c.isprintable())
        room = MAX_TEXT - len(self.text)
        text = text[:room]
        self.text = self.text[:self.cursor] + text + self.text[self.cursor:]
        self.cursor += len(text)

    def word_start(self):
        i = self.cursor

        while i > 0 and self.text[i - 1] == ' ':
            i -= 1

        while i > 0 and self.text[i - 1] != ' ':
            i -= 1

        return i

    def word_end(self):
        i = self.cursor

        while i < len(self.text) and self.text[i] == ' ':
            i += 1

        while i < len(self.text) and self.text[i] != ' ':
            i += 1

        return i

    def complete(self):
        # Tab: finish the name of a command, or the word of a command that is being typed (the completer says which words can come)
        if not self.text.startswith('.'):
            return

        words = self.text[:self.cursor].split(' ')
        current = words.pop() # the word the cursor is in (empty right after a space)

        if not words:
            lead = '.'
            matches = [name for name in self.commands if name.startswith(current[1:].lower())]
            shown = ['.' + name for name in matches]
        elif self.completer is not None:
            lead = ''
            matches = shown = self.completer(words, current)
        else:
            return

        if not matches:
            return

        common = matches[0]

        for name in matches[1:]:
            while not name.lower().startswith(common.lower()):
                common = common[:-1]

        start = self.cursor - len(current)
        self.text = self.text[:start] + lead + common + self.text[self.cursor:]
        self.cursor = start + len(lead) + len(common)

        if len(matches) > 1:
            self.add('info', ' '.join(shown))

    def handle(self, event, now=None):
        # one event while the chat is open; returns the line to run if Enter was pressed on one, otherwise None
        now = time.time() if now is None else now

        if event.type == pygame.TEXTINPUT:
            if self.ignore_text and event.text.lower() == self.ignore_text[0] and now < self.ignore_text[1]:
                self.ignore_text = None
            else:
                self.insert(event.text)

            return None

        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll + event.y * 3)

            return None

        if event.type != pygame.KEYDOWN:
            return None

        key = event.key
        ctrl = bool(event.mod & pygame.KMOD_CTRL)

        if key == pygame.K_ESCAPE:
            self.close_chat()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            line = self.text.strip()
            self.close_chat()

            if line:
                if not self.sent or self.sent[-1] != line:
                    self.sent.append(line)

                return line
        elif key == pygame.K_BACKSPACE:
            start = self.word_start() if ctrl else max(0, self.cursor - 1)
            self.text = self.text[:start] + self.text[self.cursor:]
            self.cursor = start
        elif key == pygame.K_DELETE:
            end = self.word_end() if ctrl else min(len(self.text), self.cursor + 1)
            self.text = self.text[:self.cursor] + self.text[end:]
        elif key == pygame.K_LEFT:
            self.cursor = self.word_start() if ctrl else max(0, self.cursor - 1)
        elif key == pygame.K_RIGHT:
            self.cursor = self.word_end() if ctrl else min(len(self.text), self.cursor + 1)
        elif key == pygame.K_HOME:
            self.cursor = 0
        elif key == pygame.K_END:
            self.cursor = len(self.text)
        elif key == pygame.K_UP and self.sent:
            self.sent_index = len(self.sent) - 1 if self.sent_index is None else max(0, self.sent_index - 1)
            self.text = self.sent[self.sent_index]
            self.cursor = len(self.text)
        elif key == pygame.K_DOWN and self.sent_index is not None:
            self.sent_index += 1

            if self.sent_index >= len(self.sent):
                self.sent_index = None
                self.text = ''
            else:
                self.text = self.sent[self.sent_index]

            self.cursor = len(self.text)
        elif key == pygame.K_PAGEUP:
            self.scroll += self.lines
        elif key == pygame.K_PAGEDOWN:
            self.scroll = max(0, self.scroll - self.lines)
        elif key == pygame.K_TAB:
            self.complete()
        elif key == pygame.K_v and ctrl:
            self.insert(clipboard_text())

        return None

    # --- drawing

    def font(self, size):
        return self.painter.font(size)

    def wrap(self, text, font, max_width):
        # the text cut into rows that fit; breaks at spaces, and inside a word that is too long for a row
        rows, row = [], ''

        for word in text.split(' '):
            candidate = word if not row else row + ' ' + word

            if font.size(candidate)[0] <= max_width:
                row = candidate

                continue

            if row:
                rows.append(row)

            row = ''

            while font.size(word)[0] > max_width and len(word) > 1: # a word longer than a row
                cut = len(word)

                while cut > 1 and font.size(word[:cut])[0] > max_width:
                    cut -= 1

                rows.append(word[:cut])
                word = word[cut:]

            row = word

        rows.append(row)

        return rows

    def wrap_input(self, text, font, max_width):
        # the rows of the line being typed, as (start, end) places in the text that together are all of it: a row breaks after a space when there is one in it, otherwise in the middle of the word
        # (remembered, because the same line is asked for every frame)
        key = (text, max_width, id(font))

        if self.wrap_memory is not None and self.wrap_memory[0] == key:
            return self.wrap_memory[1]

        rows = []
        start = 0

        while True:
            i = start
            last_space = -1

            while i < len(text) and font.size(text[start:i + 1])[0] <= max_width:
                i += 1

                if text[i - 1] == ' ':
                    last_space = i

            if i >= len(text):
                rows.append((start, len(text)))

                break

            end = last_space if last_space > start else max(i, start + 1)
            rows.append((start, end))
            start = end

        self.wrap_memory = (key, rows)

        return rows

    def draw(self, width, height, now=None):
        # the messages (the newest at the bottom) and, while it is open, the line being typed
        now = time.time() if now is None else now
        scale = height / 1080
        size = max(10, round(self.font_size * scale))
        font = self.font(size)
        line_h = font.get_linesize()
        pad = max(3, round(4 * scale))
        margin = max(6, round(12 * scale))
        box_w = max(320, round(width * self.width))
        text_w = box_w - 2 * pad
        input_rows = self.wrap_input(self.text, font, text_w) if self.open else [(0, 0)] # a long line being typed goes on in more rows (the box grows upwards), it is never squeezed
        input_h = len(input_rows) * line_h + 2 * pad
        rows = [] # (kind, text, alpha), newest first

        want = self.lines * 2 if self.open else self.lines
        skip = self.scroll if self.open else 0

        for kind, text, when in reversed(self.messages):
            age = now - when

            if not self.open and age >= self.fade_time:
                break

            alpha = 1.0 if self.open or age < self.fade_time - 1 else max(0.0, self.fade_time - age)

            for row in reversed(self.wrap(text, font, text_w)):
                rows.append((kind, row, alpha))

            if len(rows) >= want + skip:
                break

        rows = rows[skip:skip + want]

        if not rows and not self.open:
            return

        painter = self.painter
        painter.begin(width, height)

        bottom = height - margin - input_h

        for i, (kind, text, alpha) in enumerate(rows):
            y = bottom - (i + 1) * line_h

            painter.rect(margin, y, box_w, line_h, (0, 0, 0, 0.45 * alpha))
            painter.text(margin + pad, y, text, size, (*COLORS.get(kind, COLORS['chat']), alpha))

        if self.open:
            y = height - margin - input_h
            painter.rect(margin, y, box_w, input_h, (0, 0, 0, 0.7))
            color = COLORS['command'] if self.text.startswith('.') else COLORS['chat']

            for i, (start, end) in enumerate(input_rows):
                painter.text(margin + pad, y + pad + i * line_h, self.text[start:end], size, (*color, 1.0))

            if int(now * 2) % 2 == 0: # the caret blinks
                caret_row = max(i for i, (start, end) in enumerate(input_rows) if start <= self.cursor)
                caret_x = margin + pad + font.size(self.text[input_rows[caret_row][0]:self.cursor])[0]
                painter.rect(caret_x, y + pad + caret_row * line_h, max(2, round(2 * scale)), line_h, (1, 1, 1, 0.9))

        painter.end()
