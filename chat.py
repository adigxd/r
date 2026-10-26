import ctypes
import time

import numpy as np
from OpenGL.GL import *
import pygame

import log

# the chat: T opens it, Enter sends what was typed, Escape closes it
# a line that starts with a . is a rend command (see rend.py); anything else is a chat message
# it is drawn over the finished picture (after the post-processing), as rectangles and text; the text is drawn by pygame into a picture that is put on a rectangle

COLORS = {'chat': (1.0, 1.0, 1.0), 'ok': (0.6, 1.0, 0.65), 'info': (0.85, 0.85, 0.85), 'error': (1.0, 0.45, 0.45), 'command': (0.75, 0.9, 1.0)}
MAX_TEXT = 256 # the longest line that can be typed


class Chat:
    def __init__(self, program, font_path, font_size, lines, history, fade_time, width, commands=()):
        # program: the shader of ui.vert / ui.frag (None: no drawing, only the typing and the messages, for tests)
        # font_size is for a window 1080 high; lines are shown while the chat is closed; history is how many lines are remembered; fade_time how long a message stays; width is a share of the window
        self.program = program
        self.font_path = font_path
        self.font_size = font_size
        self.lines = lines
        self.history = history
        self.fade_time = fade_time
        self.width = width
        self.commands = sorted(commands) # the names of the commands, for Tab
        self.open = False
        self.text = ''
        self.cursor = 0
        self.sent = [] # what was sent, for the up / down keys
        self.sent_index = None
        self.messages = [] # (kind, text, time)
        self.scroll = 0 # how many lines back from the newest the chat is scrolled
        self.ignore_text = None # (text, until): the letter that opened the chat arrives as typing too, and must not be in the line
        self.fonts = {}
        self.textures = {} # (size, text) -> (texture, width, height)
        self.wrap_memory = None # (what was asked, the rows) of the last wrap_input

        if program is not None:
            self.vao = glGenVertexArrays(1)
            self.vbo = glGenBuffers(1)
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, 6 * 4 * 4, None, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, None)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
            glEnableVertexAttribArray(1)
            glBindVertexArray(0)

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
        # Tab: finish the name of a command
        if not self.text.startswith('.') or ' ' in self.text[:self.cursor]:
            return

        start = self.text[1:self.cursor].lower()
        matches = [name for name in self.commands if name.startswith(start)]

        if not matches:
            return

        common = matches[0]

        for name in matches[1:]:
            while not name.startswith(common):
                common = common[:-1]

        self.text = '.' + common + self.text[self.cursor:]
        self.cursor = 1 + len(common)

        if len(matches) > 1:
            self.add('info', ' '.join('.' + name for name in matches))

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
            self.insert(self.clipboard_text())

        return None

    def clipboard_text(self):
        try:
            pygame.scrap.init()
            data = pygame.scrap.get_text()

            return data.replace('\r', ' ').replace('\n', ' ') if data else ''
        except Exception:
            return ''

    # --- drawing

    def font(self, size):
        if size not in self.fonts:
            try:
                self.fonts[size] = pygame.font.Font(self.font_path, size)
            except Exception as e:
                log.error('Chat font failed to load, using the default one', path=self.font_path, error=e)
                self.fonts[size] = pygame.font.Font(None, size)

        return self.fonts[size]

    def texture(self, size, text):
        # the text as a picture on the graphics card: white, with its shape in the alpha (the color comes from the shader); remembered
        key = (size, text)

        if key not in self.textures:
            if len(self.textures) > 600:
                glDeleteTextures([t[0] for t in self.textures.values()])
                self.textures.clear()

            surface = self.font(size).render(text, True, (255, 255, 255))
            width, height = surface.get_size()
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(surface, 'RGBA', False))
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            self.textures[key] = (texture, width, height)

        return self.textures[key]

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

    def quad(self, x, y, w, h, color, texture=None):
        # a rectangle in pixels from the top left; with a texture it is the picture of some text
        data = np.array([x, y, 0, 0, x + w, y, 1, 0, x + w, y + h, 1, 1, x, y, 0, 0, x + w, y + h, 1, 1, x, y + h, 0, 1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
        glUniform4f(glGetUniformLocation(self.program, 'u_color'), *color)
        glUniform1i(glGetUniformLocation(self.program, 'u_textured'), 0 if texture is None else 1)

        if texture is not None:
            glBindTexture(GL_TEXTURE_2D, texture)

        glDrawArrays(GL_TRIANGLES, 0, 6)

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

        glUseProgram(self.program)
        glUniform2f(glGetUniformLocation(self.program, 'u_screen'), width, height)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glActiveTexture(GL_TEXTURE0)
        glUniform1i(glGetUniformLocation(self.program, 'u_texture'), 0)
        glBindVertexArray(self.vao)

        bottom = height - margin - input_h

        for i, (kind, text, alpha) in enumerate(rows):
            y = bottom - (i + 1) * line_h

            self.quad(margin, y, box_w, line_h, (0, 0, 0, 0.45 * alpha))

            if text:
                texture, tw, th = self.texture(size, text)
                self.quad(margin + pad, y, tw, th, (*COLORS.get(kind, COLORS['chat']), alpha), texture)

        if self.open:
            y = height - margin - input_h
            self.quad(margin, y, box_w, input_h, (0, 0, 0, 0.7))
            color = COLORS['command'] if self.text.startswith('.') else COLORS['chat']

            for i, (start, end) in enumerate(input_rows):
                if end > start:
                    texture, tw, th = self.texture(size, self.text[start:end])
                    self.quad(margin + pad, y + pad + i * line_h, tw, th, (*color, 1.0), texture)

            if int(now * 2) % 2 == 0: # the caret blinks
                caret_row = max(i for i, (start, end) in enumerate(input_rows) if start <= self.cursor)
                caret_x = margin + pad + font.size(self.text[input_rows[caret_row][0]:self.cursor])[0]
                self.quad(caret_x, y + pad + caret_row * line_h, max(2, round(2 * scale)), line_h, (1, 1, 1, 0.9))

        glBindVertexArray(0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
