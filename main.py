import math
import numpy as np
from multiprocessing import Process, Queue, Manager, freeze_support, set_start_method
from OpenGL.GL import *
from OpenGL.GLU import *
import os
import pygame
from pygame.locals import *
import random
import time

# ./
import buf
from cam import __CAM__
import dbg
from kin import _ACC_D
import mat
from map_ import __MAP__
import sha
import uni

from dotenv import load_dotenv

load_dotenv()

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # hide pygame support prompt

# light
_LIT_POS           = tuple(map(float, os.getenv('LIT_POS').split(',')))
_LIT_RAD           = float(os.getenv('LIT_RAD'))
_LIT_INT           = float(os.getenv('LIT_INT'))
_LIT_COL           = tuple(map(float, os.getenv('LIT_COL').split(',')))

# main.py
_THD_CNT           = int(os.getenv('THD_CNT'))
_RES_X             = int(os.getenv('RES_X'))
_RES_Y             = int(os.getenv('RES_Y'))
_TIC               = int(os.getenv('TIC'))
_FOV               = float(os.getenv('FOV'))
_SEE_MIN           = float(os.getenv('SEE_MIN'))
_SEE_MAX           = float(os.getenv('SEE_MAX'))
_SEN               = float(os.getenv('SEN'))
_LIN_WID           = float(os.getenv('LIN_WID'))
_COL_BKG           = tuple(map(float, os.getenv('COL_BKG').split(',')))
_POS               = tuple(map(float, os.getenv('POS').split(',')))
_SPD               = float(os.getenv('SPD'))
_SPD_MAG           = float(os.getenv('SPD_MAG'))
_HIT               = float(os.getenv('HIT'))
_JMP_MAG           = float(os.getenv('JMP_MAG'))
_ACC_D             = float(os.getenv('ACC_D'))

# main.py / texture paths
_PTH_TEX           = os.getenv('PTH_TEX')

# main.py / shader paths
_PTH_SHA_V         = os.getenv('PTH_SHA_V')
_PTH_SHA_F         = os.getenv('PTH_SHA_F')
_PTH_SHA_V_PST     = os.getenv('PTH_SHA_V_PST')
_PTH_SHA_F_PST_DEF = os.getenv('PTH_SHA_F_PST_DEF')
_PTH_SHA_F_PST_0   = os.getenv('PTH_SHA_F_PST_0')
_PTH_SHA_F_PST_1   = os.getenv('PTH_SHA_F_PST_1')

# main.py / general paths
_PTH_SSM_DIR       = os.getenv('PTH_SSM_DIR')

# main.py / debug
_DBG_KIN=1               # debug kinematics mode (0: debug fly, 1: physics)

dbg._DBG(dbg._TAG_CFG, ['THD_CNT'], [_THD_CNT])

# ------

def _TEX_GET(pth):
    # this function loads an image file as a texture and returns the texture ID, width, and height; it uses pygame to load the image and convert it to a format suitable for OpenGL, then creates an OpenGL texture object and uploads the image data to it
    try:
        img = pygame.image.load(pth) # load the image file as a pygame surface
        img_dat = pygame.image.tostring(img, 'RGBA', True) # convert the surface to a string of pixel data in RGBA format (the True argument flips the image vertically to match OpenGL's coordinate system)
        wid, hei = img.get_size() # get the width and height of the surface

        tex = glGenTextures(1) # generate a new texture object and get its ID
        glBindTexture(GL_TEXTURE_2D, tex) # bind the texture object to the GL_TEXTURE_2D target, making it the current texture for subsequent texture operations
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, wid, hei, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_dat) # specify the texture image data for the currently bound texture object (the img_dat string contains the pixel data for the image)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR) # set the texture minifying function to use linear filtering with mipmaps (this determines how the texture is sampled when it needs to be shrunk down)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # set the texture magnification function to use linear filtering (this determines how the texture is sampled when it needs to be enlarged)
        glGenerateMipmap(GL_TEXTURE_2D) # generate mipmaps for the currently bound texture object (this creates smaller versions of the texture for use when the texture is viewed at a distance or at a small size)

        return tex, wid, hei
    except Exception as E:
        dbg._DBG(dbg._TAG_ERR, ['_TEX_GET', pth], ['...'])

        return None, None, None

# ------

def main():
    dbg_see = False # debug see-through mode toggle

    # pygame setup
    res = (_RES_X, _RES_Y)
    pygame.init()
    pygame.display.set_mode(res, DOUBLEBUF | OPENGL)
    pygame.display.set_caption('r')
    pygame.display.set_icon(pygame.image.load('./DIR-Resources/IMG-WIN.png'))

    # opengl setup
    glEnable(GL_DEPTH_TEST)
    # glEnable(GL_BLEND)
    # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # https://www.khronos.org/opengl/wiki/Blending
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)
    glClearColor(*_COL_BKG, 1) # set background color

    # ------

    # frame buffer setup for post-processing
    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)

    # create texture to render to
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, _RES_X, _RES_Y, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)

    # create renderbuffer for depth and stencil attachments
    rbo = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, _RES_X, _RES_Y)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # check framebuffer status
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        dbg._DBG(dbg._TAG_ERR, ['glCheckFramebufferStatus'], ['FRAMEBUFFER NOT COMPLETE'])
        pygame.quit()
        exit()

    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # ------

    # perspective matrix setup
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(_FOV, _RES_X / _RES_Y, _SEE_MIN, _SEE_MAX)
    glMatrixMode(GL_MODELVIEW)

    # ------

    # map setup
    map = __MAP__()
    map._DBG_MAP_SET() # set up a test map with some blocks for rendering; this will be replaced with dynamic chunk loading and generation based on the player's position in the world, but for now it serves as a simple test case to ensure that the rendering pipeline is working correctly with the block vertex data and texture coordinates from the atlas

    # ------

    # camera and mouse setup
    cam = __CAM__(_DBG_KIN, _JMP_MAG, _ACC_D, _HIT, list(_POS), _SPD, _SEN, map=map)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    # ------

    # lighting setup
    lit_pos = _LIT_POS
    lit_rad = _LIT_RAD
    lit_int = _LIT_INT
    lit_col = _LIT_COL

    # ------

    # texture setup
    tex_id, tex_wid, tex_hei = _TEX_GET(_PTH_TEX)
    dbg._DBG(dbg._TAG_CFG, ['Texture Path', 'Texture ID', 'Width', 'Height'], [_PTH_TEX, tex_id, tex_wid, tex_hei])

    # vao_blc = block vertex array object
    # vtx_cnt_blc = block vertex count for rendering; these will be generated dynamically based on the chunks that are loaded, and will be used to render the blocks in the scene with the appropriate texture coordinates from the atlas

    vao_blc, vtx_cnt_blc = map._MAP_GET() # get the vertex array object and vertex count for rendering the blocks in the scene; this will be updated dynamically based on the chunks that are loaded and the blocks they contain, allowing for efficient rendering of only the visible blocks with the appropriate texture coordinates from the atlas

    # ------

    # shader setup
    sha_src_vec = sha._SHA_GEN(_PTH_SHA_V)
    sha_src_frg = sha._SHA_GEN(_PTH_SHA_F)

    if not sha_src_vec or not sha_src_frg:
        pygame.quit()
        exit()

    pro_sha = sha._SHA_PRO(sha_src_vec, sha_src_frg)

    if not pro_sha:
        pygame.quit()
        exit()

    sha_src_vec_pst = sha._SHA_GEN(_PTH_SHA_V_PST)
    sha_src_frg_pst_dct = {
        'DEFAULT': sha._SHA_GEN(_PTH_SHA_F_PST_DEF),
        'EDGE_DETECT': sha._SHA_GEN(_PTH_SHA_F_PST_0),
        'DITHER': sha._SHA_GEN(_PTH_SHA_F_PST_1)
    }

    if not sha_src_vec_pst or not any(sha_src_frg_pst_dct.values()):
        pygame.quit()
        exit()

    pro_sha_pst_dct = {
        'DEFAULT': sha._SHA_PRO(sha_src_vec_pst, sha_src_frg_pst_dct['DEFAULT']),
        'EDGE_DETECT': sha._SHA_PRO(sha_src_vec_pst, sha_src_frg_pst_dct['EDGE_DETECT']),
        'DITHER': sha._SHA_PRO(sha_src_vec_pst, sha_src_frg_pst_dct['DITHER'])
    }

    if not any(pro_sha_pst_dct.values()):
        pygame.quit()
        exit()

    pro_sha_pst_typ_arr = list(pro_sha_pst_dct.keys())
    pro_sha_pst_typ_idx = 0

    # vao_pst, vbo_pst, ebo_pst = buf._BUF_PST() # post-processing buffer objects for full-screen quad

    glUseProgram(pro_sha)

    # ------

    # matrices setup
    res_rat = _RES_X / _RES_Y # aspect ratio for perspective matrix
    mat_p = mat._GEN_MAT_P(_FOV, res_rat, _SEE_MIN, _SEE_MAX) # perspective projection matrix
    mat_m = mat._GEN_MAT_M() # use defaults for model matrix (no transformations)

    glLineWidth(_LIN_WID) # set line width for wireframe rendering (if used)

    # ------

    # frame rate is how many frames are rendered per second, 
    # while tick rate is how many times the game loop updates per second; 
    # you can have a high tick rate for smooth input and physics, 
    # but a lower frame rate to save resources
    clc = pygame.time.Clock() # clock for controlling frame rate

    pos_pre = (None, None, None) # previous position for movement delta calculations

    cnt = 0

    while True:
        cnt += 1

        for E in pygame.event.get():
            if E.type == pygame.QUIT or (E.type == pygame.KEYDOWN and E.key == pygame.K_RSHIFT):
                # cleanup and exit
                for pro_sha_pst in pro_sha_pst_dct.values():
                    glDeleteProgram(pro_sha_pst)

                glDeleteProgram(pro_sha)
                glDeleteFramebuffers(1, [fbo])
                glDeleteTextures(1, [tex])
                glDeleteRenderbuffers(1, [rbo])
                # glDeleteVertexArrays(1, [vao_pst])
                # glDeleteBuffers(1, [vbo_pst, ebo_pst])

                pygame.quit()

                return

            if E.type == pygame.KEYDOWN and E.key == pygame.K_BACKSLASH:
                # cycle through post-processing shader types
                pro_sha_pst_typ_idx = (pro_sha_pst_typ_idx + 1) % len(pro_sha_pst_typ_arr)

            if E.type == pygame.KEYDOWN and E.key == pygame.K_BACKQUOTE:
                # do it like this to ensure post-processing effects in frame buffer are captured

                # ensures that all rendering commands, such as rendering the scene to the FBO, 
                # applying post-processing shaders, and drawing to the default framebuffer, 
                # are fully executed before you read the pixel data with glReadPixels()

                glFinish() # wait for all OpenGL commands to complete
                pxl_dat = glReadPixels(0, 0, _RES_X, _RES_Y, GL_RGBA, GL_UNSIGNED_BYTE) # read pixel data from the default framebuffer (the screen)
                sfc = pygame.image.frombuffer(pxl_dat, res, 'RGBA') # create a pygame surface from the pixel data (surface is a 2D image that can be drawn on the screen)
                sfc = pygame.transform.flip(sfc, False, True) # flip the surface vertically (OpenGL's origin is bottom-left, while Pygame's is top-left)

                pth_ssm = os.path.join(_PTH_SSM_DIR, f'{int(time.time())}.png') # create a unique file path for the screenshot using the current timestamp
                pygame.image.save(sfc, pth_ssm) # save the surface as a PNG image to the specified file path
                dbg._DBG(dbg._TAG_DBG, ['Screenshot Mode'], ['...'])

            if E.type == pygame.KEYDOWN and E.key == pygame.K_RCTRL:
                # wireframe toggle for debugging
                dbg_see = not dbg_see
            
            if E.type == pygame.MOUSEBUTTONDOWN:
                if E.button == 3:
                    cam._SPD_SET(_SPD * _SPD_MAG)

            if E.type == pygame.MOUSEBUTTONUP:
                if E.button == 3:
                    cam._SPD_SET(_SPD)

            if E.type == pygame.KEYDOWN and E.key == pygame.K_BACKSPACE:
                cam._POS_SET(list(_POS))

        mos_rel = pygame.mouse.get_rel() # get the relative movement of the mouse since the last call to this function
        key_arr = pygame.key.get_pressed() # get the current state of all keyboard buttons

        cam._CAM_SET(key_arr, mos_rel, None) # update camera position and rotation based on input

        # update light position
        lit_pos = cam.pos

        # snap light position
        lit_pos_fix = [
            math.floor(cam.pos[0]) + 0.5,
            math.floor(cam.pos[1]) + 0.5,
            math.floor(cam.pos[2]) + 0.5
        ]

        if cnt % 256 == 0:
            dbg._DBG(dbg._TAG_DBG, ['cam.pos'], [cam.pos])
            dbg._DBG(dbg._TAG_DBG, ['cam.rot'], [cam.rot])

        # cam._CAM_RDR() # look

        # glBindFramebuffer(GL_FRAMEBUFFER, fbo) # bind the frame buffer object for off-screen rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # clear the color and depth buffers for the new frame

        glUseProgram(pro_sha) # use the main shader program for rendering the scene

        mat_v = mat._GEN_MAT_V(cam.pos, cam.rot) # generate the view matrix based on the camera's position and rotation
        
        uni._UNI_MAT(pro_sha, mat_m, mat_v, mat_p) # set the uniform variables for the main shader program (model, view, projection matrices)
        uni._UNI_ETC(pro_sha, tex_id, lit_pos_fix, lit_rad, lit_int, lit_col) # set other uniform variables (e.g. textures)

        vao_blc, vtx_cnt_blc = map._MAP_GET() # get the vertex array object and vertex count for rendering the blocks in the scene; this will be updated dynamically based on the chunks that are loaded and the blocks they contain, allowing for efficient rendering of only the visible blocks with the appropriate texture coordinates from the atlas

        if vao_blc is not None: # if the block vertex array object has been generated (i.e. there are blocks to render)
             glBindVertexArray(vao_blc) # bind the block VAO for rendering
             glDrawArrays(GL_TRIANGLES, 0, vtx_cnt_blc) # draw the blocks as triangles using the vertex count for rendering
             # future: switch to indexed drawing with glDrawElements and an element buffer object (EBO) for better performance and memory efficiency when rendering complex scenes with many blocks
             # switch to glDrawElements when using an EBO: glDrawElements(GL_TRIANGLES, idx_cnt_blc, GL_UNSIGNED_INT, None) where idx_cnt_blc is the count of indices in the EBO for rendering the blocks

        if dbg_see:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE) # this makes blocks look like wireframes, which is useful for debugging; you can toggle this with the DBG_SEE environment variable
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL) # this makes blocks look like they are solid, which is the default rendering mode

        # TEMP: only do normal post-processing shader
        # glBindFramebuffer(GL_FRAMEBUFFER, 0)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # glUseProgram(0)
        # glEnable(GL_TEXTURE_2D)
        # glBindTexture(GL_TEXTURE_2D, tex_id)
        # glDisable(GL_TEXTURE_2D) # unbind the texture to prevent it from being accidentally used in subsequent rendering operations; this is a good practice to avoid unintended side effects, especially if you have multiple textures and shaders in your application; by unbinding the texture, you ensure that only the intended textures are used when rendering with different shaders or for different objects in the scene
        # glDisable(GL_DEPTH_TEST) # disable depth testing for post-processing effects (since we're rendering a full-screen quad, we don't need depth testing; this can improve performance and ensure that the post-processing effects are applied correctly without being affected by depth values from the scene rendering)

        pygame.display.flip() # update the display with the rendered frame
        clc.tick(_TIC) # limit the frame rate to the specified tick rate (this controls how often the game loop updates and renders, which can help with performance and resource management)

if __name__ == '__main__':
    main()