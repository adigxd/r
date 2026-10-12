from OpenGL.GL import *

# ./
import log

def read_source(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        log.error('Shader read failed', path=path, error=e)

        return None

def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)

    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        log.error('Shader compile failed', info=glGetShaderInfoLog(shader))
        glDeleteShader(shader)

        return None

    return shader

def build_program(vertex_source, fragment_source):
    if not vertex_source or not fragment_source: # source file failed to load
        return None

    vertex_shader = compile_shader(vertex_source, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_source, GL_FRAGMENT_SHADER)

    if not vertex_shader or not fragment_shader:
        if vertex_shader:
            glDeleteShader(vertex_shader)
        if fragment_shader:
            glDeleteShader(fragment_shader)

        return None

    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        log.error('Shader link failed', info=glGetProgramInfoLog(program))
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        glDeleteProgram(program)

        return None

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program
