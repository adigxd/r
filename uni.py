from OpenGL.GL import *

def _UNI_MAT(pro_sha, mat_m, mat_v, mat_p):
    loc_mat_m = glGetUniformLocation(pro_sha, 'MAT_M')
    loc_mat_v = glGetUniformLocation(pro_sha, 'MAT_V')
    loc_mat_p = glGetUniformLocation(pro_sha, 'MAT_P')

    glUniformMatrix4fv(loc_mat_m, 1, GL_TRUE, mat_m)
    glUniformMatrix4fv(loc_mat_v, 1, GL_TRUE, mat_v)
    glUniformMatrix4fv(loc_mat_p, 1, GL_TRUE, mat_p)

# other uniforms that dont fit in the above function, such as lighting and textures
def _UNI_ETC(pro_sha, tex_id, lit_pos, lit_rad, lit_int, lit_col):
    # set texture uniform
    tex_loc = glGetUniformLocation(pro_sha, 'ATL')
    glActiveTexture(GL_TEXTURE0) # this sets the active texture unit to 0, which is the default texture unit; this means that subsequent texture operations will affect the texture bound to GL_TEXTURE0
    glBindTexture(GL_TEXTURE_2D, tex_id) # this binds the texture with the ID 'tex' to the GL_TEXTURE_2D target of the currently active texture unit (which is GL_TEXTURE0); this makes the texture available for use in shaders when sampling from GL_TEXTURE0
    glUniform1i(tex_loc, 0) # this sets the uniform variable at location 'tex_loc' in the shader to the value 0, which corresponds to GL_TEXTURE0; this tells the shader to use the texture bound to GL_TEXTURE0 when sampling from the 'tex' uniform

    # set lighting uniforms
    loc_lit_pos = glGetUniformLocation(pro_sha, 'LIT_POS')
    loc_lit_rad = glGetUniformLocation(pro_sha, 'LIT_RAD')
    loc_lit_int = glGetUniformLocation(pro_sha, 'LIT_INT')
    loc_lit_col = glGetUniformLocation(pro_sha, 'LIT_COL')

    glUniform3fv(loc_lit_pos, 1, lit_pos)
    glUniform1f(loc_lit_rad, lit_rad)
    glUniform1f(loc_lit_int, lit_int)
    glUniform3fv(loc_lit_col, 1, lit_col)