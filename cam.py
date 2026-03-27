import math
from OpenGL.GL import *
import pygame

# ./
import dbg
# from kin import __KIN__ # TODO: IMPLEMENT

from dotenv import load_dotenv
load_dotenv()

class __CAM__:
    def __init__(self, pos, spd, sen, rot=[0, 0]):
        self.pos = pos
        self.spd = spd
        self.sen = sen
        self.rot = rot

    def _CAM_SET(self, key_arr, mos_rel, kin):
        # MOUSE LOOK
        self.rot[0] -= mos_rel[1] * self.sen # PITCH
        self.rot[1] += mos_rel[0] * self.sen # YAW

        # CLAMP PITCH
        self.rot[0] = max(-89, min(89, self.rot[0]))

        # FORWARD AND RIGHT VECTORS
        pit = math.radians(self.rot[0])
        yaw = math.radians(self.rot[1])

        fwd = [
            math.sin(yaw),
            0,
            -math.cos(yaw)
        ]

        rit = [
            math.cos(yaw),
            0,
            math.sin(yaw)
        ]

        spd_fix = 1

        # DIAGONAL MOVEMENT FIX
        if (key_arr[pygame.K_w] and key_arr[pygame.K_a]) or \
           (key_arr[pygame.K_w] and key_arr[pygame.K_d]) or \
           (key_arr[pygame.K_s] and key_arr[pygame.K_a]) or \
           (key_arr[pygame.K_s] and key_arr[pygame.K_d]):
            spd_fix = 0.7071
        
        if key_arr[pygame.K_w]: # FORWARD
            self.pos[0] += fwd[0] * self.spd * spd_fix
            self.pos[1] += fwd[1] * self.spd * spd_fix
            self.pos[2] += fwd[2] * self.spd * spd_fix
        if key_arr[pygame.K_s]: # BACKWARD
            self.pos[0] -= fwd[0] * self.spd * spd_fix
            self.pos[1] -= fwd[1] * self.spd * spd_fix
            self.pos[2] -= fwd[2] * self.spd * spd_fix
        if key_arr[pygame.K_a]: # LEFT
            self.pos[0] -= rit[0] * self.spd * spd_fix
            self.pos[1] -= rit[1] * self.spd * spd_fix
            self.pos[2] -= rit[2] * self.spd * spd_fix
        if key_arr[pygame.K_d]: # RIGHT
            self.pos[0] += rit[0] * self.spd * spd_fix
            self.pos[1] += rit[1] * self.spd * spd_fix
            self.pos[2] += rit[2] * self.spd * spd_fix
        if key_arr[pygame.K_SPACE]: # FLY UP
            self.pos[1] += self.spd * spd_fix
        if key_arr[pygame.K_LSHIFT]: # FLY DOWN
            self.pos[1] -= self.spd * spd_fix
    
    def _CAM_GET(self):
        return self.pos, self.rot

    def _CAM_RDR(self): # RENDER CAMERA TRANSFORMATIONS
        # Clear transformation matrix
        glLoadIdentity()
        
        # Apply rotations first, then translation
        glRotatef(-self.rot[0], 1, 0, 0)
        glRotatef(-self.rot[1], 0, 1, 0)
        glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])