import ctypes
import numpy as np
from OpenGL.GL import *

# ./
import log

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

def make_framebuffer(width, height):
    # frame buffer for post-processing: the scene is drawn into this instead of the screen, then a post-processing shader draws it to the screen
    # returns (fbo, texture, rbo), or None if the frame buffer can't be used; has to be made again whenever the window size changes
    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)

    # create texture to render to
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

    # create renderbuffer for depth and stencil attachments
    rbo = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # check framebuffer status
    complete = glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    if not complete:
        log.error('Framebuffer not complete', width=width, height=height)
        delete_framebuffer(fbo, texture, rbo)

        return None

    return fbo, texture, rbo

def delete_framebuffer(fbo, texture, rbo):
    glDeleteFramebuffers(1, [fbo])
    glDeleteTextures(1, [texture])
    glDeleteRenderbuffers(1, [rbo])
