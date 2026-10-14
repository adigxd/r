import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import argparse
import numpy as np
from OpenGL.GL import *
import pygame
from pygame.locals import *
import time

# ./
import atlas
import buffers
from camera import Camera
import config
import glsl
import log
import matrices
import uniforms
from world import World

# ------

def load_texture(path, mipmaps, tile_size):
    # this function loads an image file as a texture and returns the texture ID; it uses pygame to load the image and convert it to a format suitable for OpenGL, then creates an OpenGL texture object and uploads the image data to it
    try:
        img = pygame.image.load(path) # load the image file as a pygame surface
        img_data = pygame.image.tostring(img, 'RGBA', True) # convert the surface to a string of pixel data in RGBA format (the True argument flips the image vertically to match OpenGL's coordinate system)

        # pixels that are completely see-through get black as their color, whatever the png has hidden in them: the shader relies on that when it undoes the smoothing of mipmaps at the edge of a cutout
        pixels = np.frombuffer(img_data, dtype=np.uint8).reshape(-1, 4).copy()
        pixels[pixels[:, 3] == 0, :3] = 0
        img_data = pixels.tobytes()
        width, height = img.get_size() # get the width and height of the surface

        texture = glGenTextures(1) # generate a new texture object and get its ID
        glBindTexture(GL_TEXTURE_2D, texture) # bind the texture object to the GL_TEXTURE_2D target, making it the current texture for subsequent texture operations
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data) # specify the texture image data for the currently bound texture object (the img_data string contains the pixel data for the image)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # up close every texel stays a sharp square

        if mipmaps:
            # mipmaps are smaller versions of the texture (half the size, again half, ...) that get used when it is far away or small, which stops it from shimmering
            # every tile is tile_size wide, so the smallest version that still keeps every tile apart from its neighbours is 1 texel per tile; going past that would blend neighbouring tiles together
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, tile_size.bit_length() - 1)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR) # sharp texels, with a smooth blend between two sizes of the texture
            glGenerateMipmap(GL_TEXTURE_2D) # generate the smaller versions of the currently bound texture object
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        return texture
    except Exception as e:
        log.error('Texture load failed', path=path, error=e)

        return None

# ------

def main(map_name):
    # all settings come from .env.pre / .env and the map file, so they have to load before anything else starts
    settings, world_data = config.load(map_name)

    if settings is None: # the reason has already been printed
        exit(1)

    wireframe = False # debug wireframe mode toggle
    focus_grace_until = 0.0 # switching fullscreen makes the window lose and regain focus, which must not exit the game

    # pygame setup
    pygame.init()
    pygame.mixer.init(frequency=settings.mixer_frequency, size=settings.mixer_size, channels=settings.mixer_channels, buffer=settings.mixer_buffer)
    pygame.mixer.set_num_channels(2)
    pygame.display.set_mode((settings.width, settings.height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption('r')
    pygame.display.set_icon(pygame.image.load('./resources/icon.png'))

    # fullscreen is a borderless window as big as the screen, at the screen's own resolution: the monitor never switches video mode, so there is no black flicker (the window starts windowed and switches, the same way F11 does)
    if settings.fullscreen:
        focus_grace_until = time.time() + 1.0
        pygame.display.toggle_fullscreen()

    width, height = pygame.display.get_window_size() # the real size of the window (the size of the screen when it is fullscreen); everything that depends on the size uses these

    # music setup (a map without "music" just has none)
    if settings.music:
        music_path = os.path.join(settings.music_dir, settings.music)

        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(settings.music_volume)
            pygame.mixer.music.play(-1)
        except Exception as e:
            log.error('Music load failed', path=music_path, error=e)

    # opengl setup
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)
    glClearColor(*settings.background_color, 1) # set background color

    # ------

    # frame buffer setup for post-processing
    framebuffer = buffers.make_framebuffer(width, height)

    if framebuffer is None: # the reason has already been printed
        pygame.quit()
        exit()

    fbo, fbo_texture, rbo = framebuffer

    # ------

    # world setup
    world = World(settings.seed, settings.tile_size, settings.atlas_size, atlas.tile_opacities(settings.atlas_path, settings.tile_size, settings.atlas_size))
    world.build(world_data) # build the world from the map file; this will be replaced with dynamic chunk loading and generation based on the player's position in the world, but for now it serves as a simple test case to ensure that the rendering pipeline is working correctly with the block vertex data and texture coordinates from the atlas

    # ------

    # camera and mouse setup
    camera = Camera(settings.fly, settings.jump_speed, settings.gravity, settings.player_width, settings.player_height, list(settings.start_pos), settings.speed, settings.mouse_sensitivity, world=world)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    # ------

    # texture setup
    atlas_id = load_texture(settings.atlas_path, settings.mipmaps, settings.tile_size)

    if atlas_id is None: # the reason has already been printed
        pygame.quit()
        exit()

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

    if not post_vertex_source:
        pygame.quit()
        exit()

    post_programs = [] # every post-processing shader that built, in the order they cycle
    post_index = 0

    for path in settings.post_fragment_shaders:
        post_program = glsl.build_program(post_vertex_source, glsl.read_source(path))

        if post_program: # a shader that failed has already printed why, and just isn't in the cycle
            post_programs.append(post_program)

    if not post_programs:
        pygame.quit()
        exit()

    post_vao, post_vbo, post_ebo = buffers.make_post_quad() # post-processing buffer objects for full-screen quad

    glUseProgram(block_program)

    # ------

    # matrices setup
    projection = matrices.projection_matrix(settings.fov, width / height, settings.near_clip, settings.far_clip) # perspective projection matrix
    model = matrices.model_matrix() # use defaults for model matrix (no transformations)

    glLineWidth(settings.line_width) # set line width for wireframe rendering (if used)

    # ------

    # frame rate is how many frames are rendered per second,
    # while tick rate is how many times the game loop updates per second;
    # you can have a high tick rate for smooth input and physics,
    # but a lower frame rate to save resources
    clock = pygame.time.Clock() # clock for controlling frame rate

    while True:
        for event in pygame.event.get():
            focus_lost = event.type == pygame.ACTIVEEVENT and event.gain == 0 and time.time() > focus_grace_until

            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT) or focus_lost:
                # cleanup and exit
                pygame.mixer.music.stop()

                for program in post_programs:
                    glDeleteProgram(program)

                glDeleteProgram(block_program)
                buffers.delete_framebuffer(fbo, fbo_texture, rbo)
                glDeleteVertexArrays(1, [post_vao])
                glDeleteBuffers(1, [post_vbo, post_ebo])

                pygame.quit()

                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                # switch between fullscreen and windowed; the window changes size, so everything that has the window's size has to be made again
                # (OpenGL objects like textures, shaders and buffers survive the switch, only the frame buffer and the projection depend on the size)
                focus_grace_until = time.time() + 1.0
                pygame.display.toggle_fullscreen()
                width, height = pygame.display.get_window_size() # get_surface() keeps reporting the old size

                buffers.delete_framebuffer(fbo, fbo_texture, rbo)
                framebuffer = buffers.make_framebuffer(width, height)

                if framebuffer is None: # the reason has already been printed
                    pygame.quit()
                    exit()

                fbo, fbo_texture, rbo = framebuffer
                glViewport(0, 0, width, height)
                projection = matrices.projection_matrix(settings.fov, width / height, settings.near_clip, settings.far_clip)

                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSLASH:
                # cycle through post-processing effects
                post_index = (post_index + 1) % len(post_programs)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                # do it like this to ensure post-processing effects in frame buffer are captured

                # ensures that all rendering commands, such as rendering the scene to the FBO,
                # applying post-processing shaders, and drawing to the default framebuffer,
                # are fully executed before you read the pixel data with glReadPixels()

                glFinish() # wait for all OpenGL commands to complete
                pixels = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE) # read pixel data from the default framebuffer (the screen)
                surface = pygame.image.frombuffer(pixels, (width, height), 'RGBA') # create a pygame surface from the pixel data (surface is a 2D image that can be drawn on the screen)
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

        glBindFramebuffer(GL_FRAMEBUFFER, fbo) # bind the frame buffer object for off-screen rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # clear the color and depth buffers for the new frame

        # wireframe only applies to the scene; it has to be set before the scene is drawn (and undone before the post-processing quad, or the quad itself gets drawn as lines)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL) # wireframe makes blocks look like lines, which is useful for debugging; toggle with Right Ctrl

        glUseProgram(block_program) # use the main shader program for rendering the scene

        view = matrices.view_matrix(camera.pos, camera.rot) # generate the view matrix based on the camera's position and rotation

        uniforms.set_matrices(block_program, model, view, projection) # set the uniform variables for the main shader program (model, view, projection matrices)
        uniforms.set_scene(block_program, atlas_id, settings.lights, settings.lighting, camera.pos) # set other uniform variables (e.g. textures, lights)
        uniforms.set_translucent(block_program, 0)

        block_vao, block_vertex_count = world.get_mesh() # get the vertex array object and vertex count for rendering the blocks in the scene; this will be updated dynamically based on the chunks that are loaded and the blocks they contain, allowing for efficient rendering of only the visible blocks with the appropriate texture coordinates from the atlas

        if block_vao is not None: # if the block vertex array object has been generated (i.e. there are blocks to render)
             glBindVertexArray(block_vao) # bind the block VAO for rendering
             glDrawArrays(GL_TRIANGLES, 0, block_vertex_count) # draw the blocks as triangles using the vertex count for rendering

        # translucent blocks (glass, water, ...) come last: they are blended with what is already drawn behind them
        # they don't write to the depth buffer (so faces behind them still get drawn), which is why world.get_translucent_mesh sorts them from far to near
        translucent_vao, translucent_vertex_count = world.get_translucent_mesh(camera.pos)

        if translucent_vao is not None:
            uniforms.set_translucent(block_program, 1)
            glEnable(GL_BLEND)
            glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ZERO, GL_ONE) # blend the colors, but keep the alpha of the frame as it is (otherwise screenshots get see-through spots)
            glDepthMask(GL_FALSE)

            glBindVertexArray(translucent_vao)
            glDrawArrays(GL_TRIANGLES, 0, translucent_vertex_count)

            glDepthMask(GL_TRUE)
            glDisable(GL_BLEND)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL) # post-processing quad is always solid

        # Post-processing pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        post_program = post_programs[post_index]

        glUseProgram(post_program)
        glDisable(GL_DEPTH_TEST) # disable depth testing for post-processing effects

        # Bind the FBO texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, fbo_texture)
        uniforms.set_post(post_program, 0, (width, height))

        # Draw the fullscreen quad
        glBindVertexArray(post_vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glEnable(GL_DEPTH_TEST) # re-enable depth testing

        pygame.display.flip() # update the display with the rendered frame

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='r')
    parser.add_argument('map', nargs='?', default='1', help='map file in maps/, with or without .json; it also holds this map\'s settings (default: 1)')
    args = parser.parse_args()

    main(args.map)
