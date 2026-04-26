from OpenGL.GL import *

# ./
import dbg

def _SHA_GEN(pth):
    try:
        with open(pth, 'r') as f:
            return f.read()
    except Exception as e:
        dbg._DBG(dbg._TAG_ERR, ['_SHA_GEN'], [f'{e}'])

def _SHA_COM(sha_src, sha_typ):
    sha = glCreateShader(sha_typ)
    glShaderSource(sha, sha_src)
    glCompileShader(sha)
    
    if glGetShaderiv(sha, GL_COMPILE_STATUS) != GL_TRUE:
        dbg._DBG(dbg._TAG_ERR, ['glGetShaderiv'], [f'{glGetShaderInfoLog(sha)}'])
    
    return sha

def _SHA_PRO(sha_src_vec, sha_src_frc):
    sha_vec = _SHA_COM(sha_src_vec, GL_VERTEX_SHADER)
    sha_frc = _SHA_COM(sha_src_frc, GL_FRAGMENT_SHADER)
    
    if not sha_vec or not sha_frc:
        return None

    pro = glCreateProgram()
    glAttachShader(pro, sha_vec)
    glAttachShader(pro, sha_frc)
    glLinkProgram(pro)

    if glGetProgramiv(pro, GL_LINK_STATUS) != GL_TRUE:
        dbg.__DBG(dbg._TAG_ERR, ['glGetProgramiv'], [f'{glGetProgramInfoLog(pro)}'])
        return None
    
    glDeleteShader(sha_vec)
    glDeleteShader(sha_frc)

    return pro