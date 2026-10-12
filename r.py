import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import argparse
import math
import numpy as np
from multiprocessing import Process, Queue, Manager, freeze_support, set_start_method
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
import random
import time

# ./
import buffers
from camera import Camera
import config
import glsl
import log
import matrices
import uniforms
from world import World

# ------

def load_texture(path):
    # this function loads an image file as a texture and returns the texture ID, width, and height; it uses pygame to load the image and convert it to a format suitable for OpenGL, then creates an OpenGL texture object and uploads the image data to it
    try:
        img = pygame.image.load(path) # load the image file as a pygame surface
        img_data = pygame.image.tostring(img, 'RGBA', True) # convert the surface to a string of pixel data in RGBA format (the True argument flips the image vertically to match OpenGL's coordinate system)
        width, height = img.get_size() # get the width and height of the surface

        texture = glGenTextures(1) # generate a new texture object and get its ID
        glBindTexture(GL_TEXTURE_2D, texture) # bind the texture object to the GL_TEXTURE_2D target, making it the current texture for subsequent texture operations
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data) # specify the texture image data for the currently bound texture object (the img_data string contains the pixel data for the image)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR) # set the texture minifying function to use linear filtering with mipmaps (this determines how the texture is sampled when it needs to be shrunk down)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # set the texture magnification function to use linear filtering (this determines how the texture is sampled when it needs to be enlarged)
        glGenerateMipmap(GL_TEXTURE_2D) # generate mipmaps for the currently bound texture object (this creates smaller versions of the texture for use when the texture is viewed at a distance or at a small size)

        return texture, width, height
    except Exception as e:
        log.error('Texture load failed', path=path, error=e)

        return None, None, None

# ------

def main(map_name):
    # all settings come from the map file ("config"), so it has to load before anything else starts
    settings, world_data = config.load(map_name)

    if settings is None: # the reason has already been printed
        exit(1)

    wireframe = False # debug wireframe mode toggle

    # pygame setup
    resolution = (settings.width, settings.height)
    pygame.init()
    pygame.mixer.init(frequency=settings.mixer_frequency, size=settings.mixer_size, channels=settings.mixer_channels, buffer=settings.mixer_buffer)
    pygame.mixer.set_num_channels(2)
    pygame.display.set_mode(resolution, DOUBLEBUF | OPENGL | pygame.FULLSCREEN)
    pygame.display.set_caption('r')
    pygame.display.set_icon(pygame.image.load('./resources/icon.png'))

    # music setup
    try:
        pygame.mixer.music.load(settings.music_path)
        pygame.mixer.music.set_volume(settings.music_volume)
        pygame.mixer.music.play(-1)
    except Exception as e:
        log.error('Music load failed', path=settings.music_path, error=e)

    # opengl setup
    glEnable(GL_DEPTH_TEST)
    # glEnable(GL_BLEND)
    # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # https://www.khronos.org/opengl/wiki/Blending
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)
    glClearColor(*settings.background_color, 1) # set background color

    # ------

    # frame buffer setup for post-processing
    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)

    # create texture to render to
    fbo_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, fbo_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, settings.width, settings.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, fbo_texture, 0)

    # create renderbuffer for depth and stencil attachments
    rbo = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, settings.width, settings.height)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # check framebuffer status
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        log.error('Framebuffer not complete')
        pygame.quit()
        exit()

    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # ------

    # perspective matrix setup
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(settings.fov, settings.width / settings.height, settings.near_clip, settings.far_clip)
    glMatrixMode(GL_MODELVIEW)

    # ------

    # world setup
    world = World(settings.seed, settings.tile_size, settings.atlas_size)
    world.build(world_data) # build the world from the map file; this will be replaced with dynamic chunk loading and generation based on the player's position in the world, but for now it serves as a simple test case to ensure that the rendering pipeline is working correctly with the block vertex data and texture coordinates from the atlas

    # ------

    # camera and mouse setup
    camera = Camera(settings.fly, settings.jump_speed, settings.gravity, settings.player_width, settings.player_height, list(settings.start_pos), settings.speed, settings.mouse_sensitivity, world=world)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    # ------

    # lighting setup
    light_pos = settings.light_pos
    light_radius = settings.light_radius
    light_intensity = settings.light_intensity
    light_color = settings.light_color

    # ------

    # texture setup
    atlas_id, atlas_width, atlas_height = load_texture(settings.atlas_path)

    # block_vao: block vertex array object
    # block_vertex_count: block vertex count for rendering; these will be generated dynamically based on the chunks that are loaded, and will be used to render the blocks in the scene with the appropriate texture coordinates from the atlas
    block_vao, block_vertex_count = world.get_mesh() # get the vertex array object and vertex count for rendering the blocks in the scene; this will be updated dynamically based on the chunks that are loaded and the blocks they contain, allowing for efficient rendering of only the visible blocks with the appropriate texture coordinates from the atlas

    # ------

    # shader setup
    block_vertex_source = glsl.read_source(settings.block_vertex_shader)
    block_fragment_source = glsl.read_source(settings.block_fragment_shader)

    if not block_vertex_source or not block_fragment_source:
        pygame.quit()
        exit()

    block_program = glsl.build_program(block_vertex_source, block_fragment_source)

    if not block_program:
        pygame.quit()
        exit()

    post_vertex_source = glsl.read_source(settings.post_vertex_shader)
    post_fragment_sources = {
        'default': glsl.read_source(settings.post_default_shader),
        'edge': glsl.read_source(settings.post_edge_shader),
        'dither': glsl.read_source(settings.post_dither_shader)
    }

    if not post_vertex_source or not any(post_fragment_sources.values()):
        pygame.quit()
        exit()

    post_programs = {
        'default': glsl.build_program(post_vertex_source, post_fragment_sources['default']),
        'edge': glsl.build_program(post_vertex_source, post_fragment_sources['edge']),
        'dither': glsl.build_program(post_vertex_source, post_fragment_sources['dither'])
    }

    if not any(post_programs.values()):
        pygame.quit()
        exit()

    post_effects = [effect for effect, program in post_programs.items() if program] # only cycle through effects that built
    post_index = 0

    post_vao, post_vbo, post_ebo = buffers.make_post_quad() # post-processing buffer objects for full-screen quad

    glUseProgram(block_program)

    # ------

    # matrices setup
    aspect = settings.width / settings.height # aspect ratio for perspective matrix
    projection = matrices.projection_matrix(settings.fov, aspect, settings.near_clip, settings.far_clip) # perspective projection matrix
    model = matrices.model_matrix() # use defaults for model matrix (no transformations)

    glLineWidth(settings.line_width) # set line width for wireframe rendering (if used)

    # ------

    # frame rate is how many frames are rendered per second,
    # while tick rate is how many times the game loop updates per second;
    # you can have a high tick rate for smooth input and physics,
    # but a lower frame rate to save resources
    clock = pygame.time.Clock() # clock for controlling frame rate

    prev_pos = (None, None, None) # previous position for movement delta calculations

    frame_count = 0

    while True:
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT) or (event.type == pygame.ACTIVEEVENT and event.gain == 0):
                # cleanup and exit
                pygame.mixer.music.stop()

                for post_program in post_programs.values():
                    if post_program:
                        glDeleteProgram(post_program)

                glDeleteProgram(block_program)
                glDeleteFramebuffers(1, [fbo])
                glDeleteTextures(1, [fbo_texture])
                glDeleteRenderbuffers(1, [rbo])
                glDeleteVertexArrays(1, [post_vao])
                glDeleteBuffers(1, [post_vbo, post_ebo])

                pygame.quit()

                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSLASH:
                # cycle through post-processing effects
                post_index = (post_index + 1) % len(post_effects)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                # do it like this to ensure post-processing effects in frame buffer are captured

                # ensures that all rendering commands, such as rendering the scene to the FBO,
                # applying post-processing shaders, and drawing to the default framebuffer,
                # are fully executed before you read the pixel data with glReadPixels()

                glFinish() # wait for all OpenGL commands to complete
                pixels = glReadPixels(0, 0, settings.width, settings.height, GL_RGBA, GL_UNSIGNED_BYTE) # read pixel data from the default framebuffer (the screen)
                surface = pygame.image.frombuffer(pixels, resolution, 'RGBA') # create a pygame surface from the pixel data (surface is a 2D image that can be drawn on the screen)
                surface = pygame.transform.flip(surface, False, True) # flip the surface vertically (OpenGL's origin is bottom-left, while Pygame's is top-left)

                screenshot_path = os.path.join(settings.screenshot_dir, f'{int(time.time())}.png') # create a unique file path for the screenshot using the current timestamp
                pygame.image.save(surface, screenshot_path) # save the surface as a PNG image to the specified file path
                log.debug('Screenshot saved', path=screenshot_path)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RCTRL:
                # wireframe toggle for debugging
                wireframe = not wireframe

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    camera.set_speed(settings.speed * settings.sprint_multiplier)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    camera.set_speed(settings.speed)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                camera.set_pos(list(settings.start_pos))

        dt = clock.tick(settings.max_fps) / 1000.0

        mouse_rel = pygame.mouse.get_rel() # get the relative movement of the mouse since the last call to this function
        keys = pygame.key.get_pressed() # get the current state of all keyboard buttons

        camera.update(keys, mouse_rel, dt) # update camera position and rotation based on input

        # update light position
        light_pos = camera.pos

        # snap light position
        light_pos_snapped = [
            math.floor(camera.pos[0]) + 0.5,
            math.floor(camera.pos[1]) + 0.5,
            math.floor(camera.pos[2]) + 0.5
        ]

        #if frame_count % 256 == 0:
        #    log.debug('camera', pos=camera.pos, rot=camera.rot)

        # camera.apply_transform() # look

        glBindFramebuffer(GL_FRAMEBUFFER, fbo) # bind the frame buffer object for off-screen rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # clear the color and depth buffers for the new frame

        # wireframe only applies to the scene; it has to be set before the scene is drawn (and undone before the post-processing quad, or the quad itself gets drawn as lines)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL) # wireframe makes blocks look like lines, which is useful for debugging; toggle with Right Ctrl

        glUseProgram(block_program) # use the main shader program for rendering the scene

        view = matrices.view_matrix(camera.pos, camera.rot) # generate the view matrix based on the camera's position and rotation

        uniforms.set_matrices(block_program, model, view, projection) # set the uniform variables for the main shader program (model, view, projection matrices)
        uniforms.set_scene(block_program, atlas_id, light_pos_snapped, light_radius, light_intensity, light_color) # set other uniform variables (e.g. textures)

        block_vao, block_vertex_count = world.get_mesh() # get the vertex array object and vertex count for rendering the blocks in the scene; this will be updated dynamically based on the chunks that are loaded and the blocks they contain, allowing for efficient rendering of only the visible blocks with the appropriate texture coordinates from the atlas

        if block_vao is not None: # if the block vertex array object has been generated (i.e. there are blocks to render)
             glBindVertexArray(block_vao) # bind the block VAO for rendering
             glDrawArrays(GL_TRIANGLES, 0, block_vertex_count) # draw the blocks as triangles using the vertex count for rendering
             # future: switch to indexed drawing with glDrawElements and an element buffer object (EBO) for better performance and memory efficiency when rendering complex scenes with many blocks
             # switch to glDrawElements when using an EBO: glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, None) where index_count is the count of indices in the EBO for rendering the blocks

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL) # post-processing quad is always solid

        # Post-processing pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        post_program = post_programs[post_effects[post_index]]

        glUseProgram(post_program)
        glDisable(GL_DEPTH_TEST) # disable depth testing for post-processing effects

        # Bind the FBO texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, fbo_texture)
        uniforms.set_post(post_program, 0, (settings.width, settings.height))

        # Draw the fullscreen quad
        glBindVertexArray(post_vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glEnable(GL_DEPTH_TEST) # re-enable depth testing

        pygame.display.flip() # update the display with the rendered frame

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='r')
    parser.add_argument('map', nargs='?', default='1', help='map file in maps/, with or without .json; it also holds all settings (default: 1)')
    args = parser.parse_args()

    main(args.map)
