import time
from OpenGL.GL import *
import pygame


class Cancelled(Exception):
    # raised by LoadingBar.update when the player closes the game while it is still loading
    pass


class LoadingBar:
    # a bar that fills while the game starts up, so a map that takes seconds to build doesn't look like a frozen black screen
    # it is drawn by clearing small rectangles of the screen, which needs no shader, buffer or texture, so it works before anything else is loaded

    def __init__(self, wants_exit, fps=30, width=0.3):
        # fps: how often it is redrawn at most; width: how wide it is, as a share of the window (LOADING_BAR_FPS, LOADING_BAR_WIDTH in .env.pre)
        self.wants_exit = wants_exit # called with every event that comes in while loading; True means the player wants out
        self.interval = 1 / fps
        self.next_draw = 0.0
        self.width = width

    def update(self, fraction):
        # fraction: how far along the loading is (0 to 1); this can be called as often as it likes, the bar is redrawn at most `fps` times a second
        # it also handles events, so the window stays responsive and can be closed while the map builds
        now = time.perf_counter()

        if now < self.next_draw and fraction < 1:
            return

        self.next_draw = now + self.interval

        for event in pygame.event.get():
            if self.wants_exit(event):
                raise Cancelled

        self.draw(fraction)

    def draw(self, fraction):
        width, height = pygame.display.get_window_size()
        fraction = min(1.0, max(0.0, fraction))

        outline = max(1, round(height / 720)) # thickness of the border, and of the gap between it and the fill
        bar_width = round(width * self.width)
        bar_height = max(8, round(height / 60))
        x = (width - bar_width) // 2
        y = (height - bar_height) // 2

        def fill(left, bottom, w, h, gray):
            glScissor(left, bottom, w, h)
            glClearColor(gray, gray, gray, 1)
            glClear(GL_COLOR_BUFFER_BIT)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glDisable(GL_SCISSOR_TEST)
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        glEnable(GL_SCISSOR_TEST)
        fill(x, y, bar_width, bar_height, 0.4) # border
        fill(x + outline, y + outline, bar_width - 2 * outline, bar_height - 2 * outline, 0.0) # empty inside
        fill(x + 2 * outline, y + 2 * outline, round((bar_width - 4 * outline) * fraction), bar_height - 4 * outline, 0.9) # the part that is done
        glDisable(GL_SCISSOR_TEST)

        pygame.display.flip()
