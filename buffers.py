import ctypes
import numpy as np
from OpenGL.GL import *

# Creates and returns OpenGL buffers for a fullscreen quad used in post-processing effects.
# The function sets up vertex and element buffers for a quad covering the entire screen,
# with appropriate position and texture coordinate attributes for use in shaders.
def make_post_quad():
    # Vertex positions and texture coordinates for a fullscreen quad
    vertices = np.array([
        # Positions (x, y, z) # Texture coords (u, v)
        -1.0, -1.0, 0.0, 0.0, 0.0,
         1.0, -1.0, 0.0, 1.0, 0.0,
         1.0, 1.0, 0.0, 1.0, 1.0,
        -1.0, 1.0, 0.0, 0.0, 1.0
    ], dtype=np.float32)

    indices = np.array([
        0, 1, 2, # First triangle
        0, 2, 3 # Second triangle
    ], dtype=np.uint32)

    # Create VAO and buffers
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    # Position attribute
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, None)
    glEnableVertexAttribArray(0)

    # Texture coordinate attribute
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize,
                         ctypes.c_void_p(3 * vertices.itemsize))
    glEnableVertexAttribArray(1)

    # Unbind VAO
    glBindVertexArray(0)

    return vao, vbo, ebo

def make_textured_mesh(vertex_data, index_data):
    vao = glGenVertexArrays(1) # VAO stores the state of vertex attribute pointers and buffer bindings
    glBindVertexArray(vao)

    vbo = glGenBuffers(1) # VBO stores vertex data (positions, colors, etc.)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

    ebo = glGenBuffers(1) # EBO (or IBO) stores indices for indexed drawing (which vertices to draw)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)

    # Position attribute
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertex_data.itemsize, None)
    glEnableVertexAttribArray(0)

    # Texture coordinate attribute
    # The vertex data is interleaved (position followed by texture coords), so the stride is 5 * sizeof(float) (3 for position + 2 for texture coords)
    # 2 for texture because we have 2 texture coordinates (u, v); the offset for texture coordinates is 3 * sizeof(float) because the first 3 floats are for position
    # u is the horizontal texture coordinate, v is the vertical texture coordinate
    # the texture coordinates are used in the shader to sample from a texture, which is essential for post-processing effects where we render to a texture and then sample from it
    # in simple words: the position attribute tells the shader where to draw the vertices on the screen, while the texture coordinate attribute tells the shader how to map a texture onto those vertices
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertex_data.itemsize,
                         ctypes.c_void_p(3 * vertex_data.itemsize))
    glEnableVertexAttribArray(1)

    glBindVertexArray(0) # Unbind VAO to prevent accidental modifications

    return vao, vbo, ebo

def make_block_mesh(vertex_data):
    # Buffer for cube mesh data (position + normal + uv)
    # Vertex format: 8 floats per vertex (x, y, z, nx, ny, nz, u, v)
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

    stride = 8 * vertex_data.itemsize

    # Position attribute (3 floats)
    # location = 0
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, None)
    glEnableVertexAttribArray(0)

    # Normal attribute (3 floats, offset 12 bytes)
    # location = 1
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                         ctypes.c_void_p(3 * vertex_data.itemsize))
    glEnableVertexAttribArray(1)

    # Texture coordinate attribute (2 floats, offset 24 bytes)
    # location = 2
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride,
                         ctypes.c_void_p(6 * vertex_data.itemsize))
    glEnableVertexAttribArray(2)

    glBindVertexArray(0)

    return vao, vbo
