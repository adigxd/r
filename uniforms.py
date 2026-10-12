import math
import numpy as np
from OpenGL.GL import *

def set_matrices(program, model, view, projection):
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_model'), 1, GL_TRUE, model)
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_view'), 1, GL_TRUE, view)
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_projection'), 1, GL_TRUE, projection)

# other uniforms that dont fit in the above function, such as lighting and textures
# lights and lighting are the map's "lights" and "lighting" (see config.py); player_pos is needed for the lights that follow the player
def set_scene(program, atlas_id, lights, lighting, player_pos):
    # set texture uniform
    atlas_loc = glGetUniformLocation(program, 'u_atlas')
    glActiveTexture(GL_TEXTURE0) # this sets the active texture unit to 0, which is the default texture unit; this means that subsequent texture operations will affect the texture bound to GL_TEXTURE0
    glBindTexture(GL_TEXTURE_2D, atlas_id) # this binds the atlas texture to the GL_TEXTURE_2D target of the currently active texture unit (which is GL_TEXTURE0); this makes the texture available for use in shaders when sampling from GL_TEXTURE0
    glUniform1i(atlas_loc, 0) # this sets the 'u_atlas' sampler in the shader to the value 0, which corresponds to GL_TEXTURE0; this tells the shader to use the texture bound to GL_TEXTURE0 when sampling from it

    # set lights (the shader has one array per attribute, one entry per light)
    count = len(lights)
    glUniform1i(glGetUniformLocation(program, 'u_light_count'), count)

    if count:
        positions = []

        for light in lights:
            if light.follow_player:
                pos = [player_pos[i] + light.pos[i] for i in range(3)] # light.pos is the offset from the player
            else:
                pos = list(light.pos)

            if light.snap:
                pos = [math.floor(v) + 0.5 for v in pos] # middle of the block the light is in

            positions.append(pos)

        glUniform3fv(glGetUniformLocation(program, 'u_light_pos'), count, np.array(positions, dtype=np.float32))
        glUniform3fv(glGetUniformLocation(program, 'u_light_color'), count, np.array([light.color for light in lights], dtype=np.float32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_radius'), count, np.array([light.radius for light in lights], dtype=np.float32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_intensity'), count, np.array([light.intensity for light in lights], dtype=np.float32))
        glUniform1iv(glGetUniformLocation(program, 'u_light_falloff'), count, np.array([light.falloff for light in lights], dtype=np.int32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_falloff_scale'), count, np.array([light.falloff_scale for light in lights], dtype=np.float32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_diffuse'), count, np.array([light.diffuse for light in lights], dtype=np.float32))

    # set the rest of the lighting
    glUniform1f(glGetUniformLocation(program, 'u_ambient'), lighting.ambient)
    glUniform3fv(glGetUniformLocation(program, 'u_ambient_color'), 1, np.array(lighting.ambient_color, dtype=np.float32))
    glUniform1f(glGetUniformLocation(program, 'u_brightness'), lighting.brightness)
    glUniform1i(glGetUniformLocation(program, 'u_per_block'), int(lighting.per_block))
    glUniform1fv(glGetUniformLocation(program, 'u_face_shade'), 6, np.array(lighting.face_shade, dtype=np.float32))

# uniforms for post-processing shaders
def set_post(program, texture_unit, resolution):
    # set texture uniform for post-processing
    glUniform1i(glGetUniformLocation(program, 'u_texture'), texture_unit)

    # set resolution uniform
    glUniform2f(glGetUniformLocation(program, 'u_resolution'), resolution[0], resolution[1])
