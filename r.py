import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import argparse
import ctypes
import numpy as np
from OpenGL.GL import *
import pygame
from pygame.locals import *
import sys
import time

# ./
import atlas
import buffers
from camera import Camera
import chunks
import config
import glsl
from lights import LightSet
from loading import LoadingBar, Cancelled
import log
import matrices
from ticks import Ticker
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

def enable_dpi_awareness():
    # on a screen with display scaling above 100% (laptops, 4K monitors) Windows tells programs the screen is smaller than it is and then stretches what they draw, which makes it blurry
    # this tells Windows the game works with real pixels; it has to happen before the window is made
    if sys.platform != 'win32':
        return

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        log.error('Could not turn on DPI awareness (the game may look blurry on a scaled screen)', error=e)

# ------

def main(map_name):
    # all settings come from .env.pre / .env and the map file, so they have to load before anything else starts
    settings, world_data = config.load(map_name)

    if settings is None: # the reason has already been printed
        exit(1)

    chunks.set_chunk_size(settings.chunk_size) # before the world is built

    wireframe = False # debug wireframe mode toggle

    def wants_exit(event):
        # closing the window or Right Shift (losing focus, for example by alt-tabbing, doesn't exit: the game keeps running and lets go of the mouse)
        return event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT)

    # pygame setup
    enable_dpi_awareness()
    pygame.init()
    pygame.mixer.init(frequency=settings.mixer_frequency, size=settings.mixer_size, channels=settings.mixer_channels, buffer=settings.mixer_buffer)
    pygame.mixer.set_num_channels(2)

    # the window is never bigger than the screen (this only matters on a screen smaller than WIDTH x HEIGHT; fullscreen doesn't use these two at all)
    window_size = (settings.width, settings.height)
    desktop_sizes = pygame.display.get_desktop_sizes()

    if desktop_sizes:
        window_size = (min(window_size[0], desktop_sizes[0][0]), min(window_size[1], desktop_sizes[0][1]))

        if window_size != (settings.width, settings.height):
            log.debug('Window is bigger than the screen', asked=f'{settings.width}x{settings.height}', using=f'{window_size[0]}x{window_size[1]}')

    # the window is made hidden and only shown once it has its final size and place (below), so with fullscreen a windowed one never flashes up before the switch
    # (if this version of pygame can't hide a window, it is just shown right away)
    try:
        from pygame._sdl2.video import Window
        can_hide = hasattr(pygame, 'HIDDEN') and hasattr(Window, 'from_display_module') and hasattr(Window, 'show')
    except ImportError:
        can_hide = False

    pygame.display.set_mode(window_size, DOUBLEBUF | OPENGL | (pygame.HIDDEN if can_hide else 0))
    window = Window.from_display_module() if can_hide else None # kept for the whole run, the window it stands for is not meant to outlive it
    pygame.display.set_caption('r')
    pygame.display.set_icon(pygame.image.load('./resources/icon.png'))

    # fullscreen is a borderless window as big as the screen, at the screen's own resolution: the monitor never switches video mode, so there is no black flicker (the window starts windowed and switches, the same way F11 does)
    if settings.fullscreen:
        pygame.display.toggle_fullscreen()

    # now the window is shown, straight at its final size and place (a hidden window only goes fullscreen when it is shown), with a loading bar in it until the game is ready
    pygame.mouse.set_visible(False)

    if window is not None:
        window.show()
        window.focus()

    pygame.event.pump()
    loading = LoadingBar(wants_exit, settings.loading_bar_fps, settings.loading_bar_width)
    loading.draw(0)

    width, height = pygame.display.get_window_size() # the real size of the window (the size of the screen when it is fullscreen); everything that depends on the size uses these, and the loop below keeps them up to date

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

    # ------

    # frame buffer setup for post-processing
    framebuffer = buffers.make_framebuffer(width, height)

    if framebuffer is None: # the reason has already been printed
        pygame.quit()
        exit()

    fbo, fbo_texture, rbo = framebuffer

    # ------

    # world setup
    world = World(settings.seed, settings.tile_size, settings.atlas_size, atlas.tile_opacities(settings.atlas_path, settings.tile_size, settings.atlas_size), settings.glass_sort_distance)

    try:
        world.build(world_data, loading.update) # build the world from the map file; this will be replaced with dynamic chunk loading and generation based on the player's position in the world, but for now it serves as a simple test case to ensure that the rendering pipeline is working correctly with the block vertex data and texture coordinates from the atlas
    except Cancelled: # the player closed the game while the map was building
        pygame.mixer.music.stop()
        buffers.delete_framebuffer(fbo, fbo_texture, rbo)
        pygame.quit()

        return

    glClearColor(*settings.background_color, 1) # set background color (the loading bar used its own)

    # ------

    # camera and mouse setup
    camera = Camera(settings.fly, settings.jump_speed, settings.gravity, settings.player_width, settings.player_height, list(settings.start_pos), settings.speed, settings.mouse_sensitivity, world=world, collision_step=settings.collision_step)
    pygame.event.set_grab(True)
    pygame.mouse.get_rel() # the mouse moved while loading; that is not a turn of the camera

    # ------

    # texture setup
    atlas_id = load_texture(settings.atlas_path, settings.mipmaps, settings.tile_size)

    if atlas_id is None: # the reason has already been printed
        pygame.quit()
        exit()

    # ------

    # lights: a map can have any number, but the shader takes a fixed number at a time; every frame the ones that can light something visible are picked (see lights.py)
    # how many it can take depends on the graphics card, so a card that can't take MAX_LIGHTS gets fewer instead of failing
    max_lights = min(settings.max_lights, uniforms.light_capacity())

    if max_lights < settings.max_lights:
        log.debug('This graphics card can take fewer lights at once than MAX_LIGHTS', asked=settings.max_lights, using=max_lights)

    light_set = LightSet(settings.lights, settings.light_cell_size, settings.light_fade_time, settings.light_fade_share, settings.light_stickiness)

    # shader setup
    block_vertex_source = glsl.read_source(settings.block_vertex_shader)
    block_fragment_source = glsl.with_defines(glsl.read_source(settings.block_fragment_shader), {'MAX_LIGHTS': max_lights})

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
    # while tick rate is how many times the game updates its physics per second;
    # they are separate: the physics always runs at TICK_RATE (so it plays the same on every computer), and frames in between are drawn smoothly blended between two ticks
    clock = pygame.time.Clock() # clock for controlling frame rate
    ticker = Ticker(settings.tick_rate, settings.max_frame_time)
    lights_warned = False
    had_focus = True # the mouse was just grabbed; the loop notices if the window doesn't actually have the focus

    while True:
        for event in pygame.event.get():
            if wants_exit(event):
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
                # switch between fullscreen and windowed; the window changes size, which the loop below notices and handles
                # (OpenGL objects like textures, shaders and buffers survive the switch, only the frame buffer and the projection depend on the size)
                pygame.display.toggle_fullscreen()

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

            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE): # back to the spawn of the map
                camera.set_pos(list(settings.start_pos))

        # the window changed size (fullscreen on / off, or anything else the system does to it): everything that has the size of the window has to be made again
        # asking every frame instead of waiting for an event works the same on every platform, and a window reporting 0 (minimized) is left alone
        size = pygame.display.get_window_size()

        if size != (width, height) and size[0] > 0 and size[1] > 0:
            width, height = size

            buffers.delete_framebuffer(fbo, fbo_texture, rbo)
            framebuffer = buffers.make_framebuffer(width, height)

            if framebuffer is None: # the reason has already been printed
                pygame.quit()
                exit()

            fbo, fbo_texture, rbo = framebuffer
            glViewport(0, 0, width, height)
            projection = matrices.projection_matrix(settings.fov, width / height, settings.near_clip, settings.far_clip)

        frame_time = clock.tick(settings.max_fps) / 1000.0

        # alt-tabbing away (or anything else taking the focus) doesn't stop anything: the game keeps running, it just lets go of the mouse until the window has the focus again
        has_focus = pygame.key.get_focused()

        if has_focus != had_focus:
            had_focus = has_focus
            pygame.event.set_grab(has_focus)
            pygame.mouse.set_visible(not has_focus)
            pygame.mouse.get_rel() # throw away the movement in between
            camera.set_speed(settings.speed) # letting go of the right mouse button in another window never reaches the game, so sprinting would stay on

        mouse_rel = pygame.mouse.get_rel() # get the relative movement of the mouse since the last call to this function

        if not has_focus:
            mouse_rel = (0, 0) # the mouse moving over the window while another window has the focus is not looking around

        keys = pygame.key.get_pressed() # get the current state of all keyboard buttons

        camera.look(mouse_rel) # turning happens every frame, so it follows the mouse right away

        for _ in range(ticker.advance(frame_time)): # the physics happens in ticks of the same length, as many as the time since the last frame needs (none, one or several)
            camera.tick(keys, ticker.dt)

        render_pos = camera.render_pos(ticker.alpha) # the camera is drawn between where the last two ticks put it

        glBindFramebuffer(GL_FRAMEBUFFER, fbo) # bind the frame buffer object for off-screen rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # clear the color and depth buffers for the new frame

        # wireframe only applies to the scene; it has to be set before the scene is drawn (and undone before the post-processing quad, or the quad itself gets drawn as lines)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL) # wireframe makes blocks look like lines, which is useful for debugging; toggle with Right Ctrl

        glUseProgram(block_program) # use the main shader program for rendering the scene

        view = matrices.view_matrix(render_pos, camera.rot) # generate the view matrix based on the camera's position and rotation
        planes = matrices.frustum_planes(projection @ view) # the 6 planes around what the camera can see; chunks outside them are skipped

        uniforms.set_matrices(block_program, model, view, projection) # set the uniform variables for the main shader program (model, view, projection matrices)
        lights = light_set.select(planes, render_pos, settings.far_clip, max_lights, frame_time) # the lights that can light something visible this frame (the ones that win or lose a place fade in or out over a short time instead of popping)

        if light_set.relevant > max_lights and not lights_warned: # said once, so the author of a map knows lights get left out (and a light can pop on or off when the choice changes)
            lights_warned = True
            log.debug('More lights can light the screen than fit at once, so the brightest, biggest and closest are used', can_light=light_set.relevant, fit_at_once=max_lights, to_fit_more='raise MAX_LIGHTS in .env')
        uniforms.set_scene(block_program, atlas_id, lights, settings.lighting, render_pos, light_set.weights) # set other uniform variables (e.g. textures, lights)
        uniforms.set_translucent(block_program, 0)

        # only the chunks in view, and no further away than FAR_CLIP from the camera, are drawn
        world.draw_opaque(planes, render_pos, settings.far_clip)

        # translucent blocks (glass, water, ...) come last: they are blended with what is already drawn behind them
        # they don't write to the depth buffer (so faces behind them still get drawn), which is why they are drawn from far to near
        if world.has_glass:
            uniforms.set_translucent(block_program, 1)
            glEnable(GL_BLEND)
            glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ZERO, GL_ONE) # blend the colors, but keep the alpha of the frame as it is (otherwise screenshots get see-through spots)
            glDepthMask(GL_FALSE)

            world.draw_translucent(planes, render_pos, settings.far_clip)

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
    parser.add_argument('map', nargs='?', default='parkour', help='map file in maps/, with or without .json; it also holds this map\'s settings (default: parkour)')
    args = parser.parse_args()

    main(args.map)
