import numpy as np
from OpenGL.GL import *

# ./
from lights import light_position

def set_matrices(program, model, view, projection):
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_model'), 1, GL_TRUE, model)
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_view'), 1, GL_TRUE, view)
    glUniformMatrix4fv(glGetUniformLocation(program, 'u_projection'), 1, GL_TRUE, projection)

def light_capacity():
    # how many lights this graphics card can take at once: its limit on uniform numbers for a fragment shader divided by what one light needs
    # one light is 2 vectors and 5 single numbers, and every entry of an array can take a slot of 4 numbers, so 7 slots = 28 numbers; 128 numbers are kept for the other uniforms of the shader
    components = int(glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_COMPONENTS))

    return max(1, (components - 128) // 28)

# other uniforms that dont fit in the above function, such as lighting and textures
# lights is the lights to use this frame (see LightSet.select in lights.py) and lighting is the map's "lighting" (see config.py); player_pos is needed for the lights that follow the player
def set_scene(program, atlas_id, lights, lighting, player_pos, weights=None):
    # weights: how much of its intensity each light gets (0 to 1), for lights that are fading in or out (see LightSet.select); no weights means all of it
    # set texture uniform
    atlas_loc = glGetUniformLocation(program, 'u_atlas')
    glActiveTexture(GL_TEXTURE0) # this sets the active texture unit to 0, which is the default texture unit; this means that subsequent texture operations will affect the texture bound to GL_TEXTURE0
    glBindTexture(GL_TEXTURE_2D, atlas_id) # this binds the atlas texture to the GL_TEXTURE_2D target of the currently active texture unit (which is GL_TEXTURE0); this makes the texture available for use in shaders when sampling from GL_TEXTURE0
    glUniform1i(atlas_loc, 0) # this sets the 'u_atlas' sampler in the shader to the value 0, which corresponds to GL_TEXTURE0; this tells the shader to use the texture bound to GL_TEXTURE0 when sampling from it

    # set lights (the shader has one array per attribute, one entry per light)
    count = len(lights)
    glUniform1i(glGetUniformLocation(program, 'u_light_count'), count)

    if count:
        positions = [light_position(light, player_pos) for light in lights]

        glUniform3fv(glGetUniformLocation(program, 'u_light_pos'), count, np.array(positions, dtype=np.float32))
        glUniform3fv(glGetUniformLocation(program, 'u_light_color'), count, np.array([light.color for light in lights], dtype=np.float32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_radius'), count, np.array([light.radius for light in lights], dtype=np.float32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_intensity'), count, np.array([light.intensity * (weights[i] if weights else 1.0) for i, light in enumerate(lights)], dtype=np.float32))
        glUniform1iv(glGetUniformLocation(program, 'u_light_falloff'), count, np.array([light.falloff for light in lights], dtype=np.int32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_falloff_scale'), count, np.array([light.falloff_scale for light in lights], dtype=np.float32))
        glUniform1fv(glGetUniformLocation(program, 'u_light_diffuse'), count, np.array([light.diffuse for light in lights], dtype=np.float32))

    # set the rest of the lighting
    glUniform1f(glGetUniformLocation(program, 'u_ambient'), lighting.ambient)
    glUniform3fv(glGetUniformLocation(program, 'u_ambient_color'), 1, np.array(lighting.ambient_color, dtype=np.float32))
    glUniform1f(glGetUniformLocation(program, 'u_brightness'), lighting.brightness)
    glUniform1i(glGetUniformLocation(program, 'u_per_block'), int(lighting.per_block))
    glUniform1fv(glGetUniformLocation(program, 'u_face_shade'), 6, np.array(lighting.face_shade, dtype=np.float32))

# which of the two passes the block shader is drawing: 0 = opaque blocks and cutouts (a pixel is solid or gone), 1 = translucent blocks (blended with what is behind them)
def set_translucent(program, translucent):
    glUniform1i(glGetUniformLocation(program, 'u_translucent'), translucent)
