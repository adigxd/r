import numpy as np
from OpenGL.GL import *

# the box of the rend selection, drawn as lines in the world: the whole selection, and the two corner blocks
# two passes: solid where it is not hidden, and faint through the blocks, so the box can always be found

REGION = (0.25, 0.9, 1.0)
CORNER_1 = (1.0, 0.45, 0.2)
CORNER_2 = (0.4, 0.55, 1.0)
EDGES = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4), (0, 4), (1, 5), (3, 7), (2, 6)] # the 12 edges of a box, by the numbers of its corners


def box_lines(low, high, grow=0.004):
    # the 24 vertices of the lines of the box of the blocks from low to high (both included), a little bigger than the blocks so it is not inside their faces
    x0, y0, z0 = (low[0] - grow, low[1] - grow, low[2] - grow)
    x1, y1, z1 = (high[0] + 1 + grow, high[1] + 1 + grow, high[2] + 1 + grow)
    points = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]

    return [points[i] for edge in EDGES for i in edge]


class SelectionBox:
    def __init__(self, program):
        self.program = program
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 24 * 3 * 4, None, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    def draw(self, view, projection, pos1, pos2):
        # pos1, pos2: the corners (or None)
        shapes = []

        if pos1 is not None and pos2 is not None:
            low = tuple(min(pos1[i], pos2[i]) for i in range(3))
            high = tuple(max(pos1[i], pos2[i]) for i in range(3))
            shapes.append((box_lines(low, high, 0.01), REGION))

        if pos1 is not None:
            shapes.append((box_lines(pos1, pos1, 0.02), CORNER_1))

        if pos2 is not None:
            shapes.append((box_lines(pos2, pos2, 0.02), CORNER_2))

        if not shapes:
            return

        glUseProgram(self.program)
        glUniformMatrix4fv(glGetUniformLocation(self.program, 'u_view'), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.program, 'u_projection'), 1, GL_TRUE, projection)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindVertexArray(self.vao)
        color_at = glGetUniformLocation(self.program, 'u_color')

        for vertices, color in shapes:
            data = np.array(vertices, dtype=np.float32)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)

            glDepthFunc(GL_ALWAYS) # faint, through everything
            glUniform4f(color_at, *color, 0.22)
            glDrawArrays(GL_LINES, 0, 24)

            glDepthFunc(GL_LEQUAL) # solid, where it is not hidden
            glUniform4f(color_at, *color, 1.0)
            glDrawArrays(GL_LINES, 0, 24)

        glDepthFunc(GL_LESS)
        glBindVertexArray(0)
        glDisable(GL_BLEND)
