from OpenGL.GL import *

def set_matrices(program, model, view, projection):
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_model'), 1, GL_TRUE, model)
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_view'), 1, GL_TRUE, view)
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_projection'), 1, GL_TRUE, projection)

# other uniforms that dont fit in the above function, such as lighting and textures
def set_scene(program, atlas_id, light_pos, light_radius, light_intensity, light_color):
    # set texture uniform
    atlas_loc = glGetUniformLocation(program, 'u_atlas')
    glActiveTexture(GL_TEXTURE0) # this sets the active texture unit to 0, which is the default texture unit; this means that subsequent texture operations will affect the texture bound to GL_TEXTURE0
    glBindTexture(GL_TEXTURE_2D, atlas_id) # this binds the atlas texture to the GL_TEXTURE_2D target of the currently active texture unit (which is GL_TEXTURE0); this makes the texture available for use in shaders when sampling from GL_TEXTURE0
    glUniform1i(atlas_loc, 0) # this sets the 'u_atlas' sampler in the shader to the value 0, which corresponds to GL_TEXTURE0; this tells the shader to use the texture bound to GL_TEXTURE0 when sampling from it

    # set lighting uniforms
    glUniform3fv(glGetUniformLocation(program, 'u_light_pos'), 1, light_pos)
    glUniform1f(glGetUniformLocation(program, 'u_light_radius'), light_radius)
    glUniform1f(glGetUniformLocation(program, 'u_light_intensity'), light_intensity)
    glUniform3fv(glGetUniformLocation(program, 'u_light_color'), 1, light_color)

# uniforms for post-processing shaders
def set_post(program, texture_unit, resolution):
    # set texture uniform for post-processing
    glUniform1i(glGetUniformLocation(program, 'u_texture'), texture_unit)

    # set resolution uniform
    glUniform2f(glGetUniformLocation(program, 'u_resolution'), resolution[0], resolution[1])
