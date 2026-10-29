import collections
import ctypes

import numpy as np
from OpenGL.GL import *
import pygame

import log

# draws flat rectangles and text over the finished picture, for the chat and the menu of effects (shaders/ui.vert and ui.frag)
# everything is in pixels from the top left of the window; text is drawn by pygame into a picture that is put on a rectangle, and the pictures are remembered


def clipboard_text():
    # what was copied, as one line ('' if it can't be read)
    try:
        pygame.scrap.init()
        data = pygame.scrap.get_text()

        return data.replace('\r', ' ').replace('\n', ' ') if data else ''
    except Exception:
        return ''


class Painter:
    def __init__(self, program, font_path, max_textures=2000):
        # program: the shader of ui.vert / ui.frag (None: nothing can be drawn, only the sizes of text can be asked, for tests)
        self.program = program
        self.font_path = font_path
        self.max_textures = max_textures
        self.fonts = {}
        self.textures = collections.OrderedDict() # (size, text) -> (texture, width, height), the one used longest ago first
        self.height = 0

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

            self.screen_location = glGetUniformLocation(program, 'u_screen')
            self.color_location = glGetUniformLocation(program, 'u_color')
            self.textured_location = glGetUniformLocation(program, 'u_textured')
            self.texture_location = glGetUniformLocation(program, 'u_texture')

    # --- text

    def font(self, size):
        if size not in self.fonts:
            try:
                self.fonts[size] = pygame.font.Font(self.font_path, size)
            except Exception as e:
                log.error('Font failed to load, using the default one', path=self.font_path, error=e)
                self.fonts[size] = pygame.font.Font(None, size)

        return self.fonts[size]

    def text_width(self, size, text):
        return self.font(size).size(text)[0]

    def texture(self, size, text):
        # the text as a picture on the graphics card: white, with its shape in the alpha (the color comes from the shader); remembered
        key = (size, text)

        if key in self.textures:
            self.textures.move_to_end(key)

            return self.textures[key]

        if len(self.textures) >= self.max_textures: # forget the ones not used for the longest time
            for _ in range(self.max_textures // 10):
                texture, _, _ = self.textures.popitem(last=False)[1]
                glDeleteTextures([texture])

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

    # --- drawing (between begin and end)

    def begin(self, width, height):
        glUseProgram(self.program)
        glUniform2f(self.screen_location, width, height)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glActiveTexture(GL_TEXTURE0)
        glUniform1i(self.texture_location, 0)
        glBindVertexArray(self.vao)
        self.height = height

    def end(self):
        glDisable(GL_SCISSOR_TEST)
        glBindVertexArray(0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

    def clip(self, x, y, w, h):
        # only what is inside this rectangle is drawn, until clip() is called again or end()
        glEnable(GL_SCISSOR_TEST)
        glScissor(int(x), int(self.height - y - h), max(0, int(w)), max(0, int(h)))

    def unclip(self):
        glDisable(GL_SCISSOR_TEST)

    def quad(self, x, y, w, h, color, texture=None):
        # a rectangle; with a texture it is the picture of some text
        data = np.array([x, y, 0, 0, x + w, y, 1, 0, x + w, y + h, 1, 1, x, y, 0, 0, x + w, y + h, 1, 1, x, y + h, 0, 1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
        glUniform4f(self.color_location, *color)
        glUniform1i(self.textured_location, 0 if texture is None else 1)

        if texture is not None:
            glBindTexture(GL_TEXTURE_2D, texture)

        glDrawArrays(GL_TRIANGLES, 0, 6)

    def rect(self, x, y, w, h, color):
        self.quad(x, y, w, h, color)

    def text(self, x, y, text, size, color):
        # returns how wide it is
        if not text:
            return 0

        texture, w, h = self.texture(size, text)
        self.quad(x, y, w, h, color, texture)

        return w
