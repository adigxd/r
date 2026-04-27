import math
from OpenGL.GL import *
import os
import pygame

# ./
import dbg

from dotenv import load_dotenv
load_dotenv()

class __CAM__:
    def __init__(self, kin, jmp_mag, acc_d, wid, hit, pos, spd, sen, rot=[0, 0], map=None):
        self.kin = kin
        self.jmp_mag = jmp_mag
        self.acc_d = acc_d
        self.pos = pos
        self.wid = wid
        self.hit = hit
        self.spd = spd
        self.sen = sen
        self.rot = rot
        self.map = map
        self.vel_y = 0.0
        self.grd = False
    
    def _SPD_SET(self, spd):
        self.spd = spd
    
    def _SEN_SET(self, sen):
        self.sen = sen
    
    def _MAP_SET(self, map):
        self.map = map

    def _POS_SET(self, pos):
        self.vel_y = 0.0
        self.grd = False
        self.pos = pos

    def _POS_FIX(self, axs):
        if not self.map:
            return

        r = self.wid / 2 # collision half-extent (box is r * 2 wide)

        px, py, pz = self.pos

        min_x = int(math.floor(px - r))
        max_x = int(math.ceil(px + r))
        min_y = int(math.floor(py - self.hit)) # height
        max_y = int(math.ceil(py + r))
        min_z = int(math.floor(pz - r))
        max_z = int(math.ceil(pz + r))

        for bx in range(min_x, max_x + 1):
            for by in range(min_y, max_y + 1):
                for bz in range(min_z, max_z + 1):
                    if (bx, by, bz) not in self.map.blc_arr:
                        continue

                    # "minimum of upper range minus the maximum of lower range" gives the amount of overlap
                    ox = min(self.pos[0] + r, bx + 1) - max(self.pos[0] - r, bx)
                    oy = min(self.pos[1] + r, by + 1) - max(self.pos[1] - self.hit, by)
                    oz = min(self.pos[2] + r, bz + 1) - max(self.pos[2] - r, bz)

                    if ox <= 0 or oy <= 0 or oz <= 0:
                        continue

                    if axs == 0:
                        self.pos[0] += ox if self.pos[0] > bx + 0.5 else -ox
                    elif axs == 1:
                        self.pos[1] += oy if self.pos[1] > by + 0.5 else -oy
                    else:
                        self.pos[2] += oz if self.pos[2] > bz + 0.5 else -oz

    def _CAM_SET(self, key_arr, mos_rel, dlt=1.0):
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
            spd_fix = 0.7071 # 1/sqrt(2) to maintain consistent speed when moving diagonally

        mov = [0.0, 0.0, 0.0]

        if key_arr[pygame.K_w]: # FORWARD
            mov[0] += fwd[0] * self.spd * spd_fix * dlt
            mov[2] += fwd[2] * self.spd * spd_fix * dlt
        if key_arr[pygame.K_s]: # BACKWARD
            mov[0] -= fwd[0] * self.spd * spd_fix * dlt
            mov[2] -= fwd[2] * self.spd * spd_fix * dlt
        if key_arr[pygame.K_a]: # LEFT
            mov[0] -= rit[0] * self.spd * spd_fix * dlt
            mov[2] -= rit[2] * self.spd * spd_fix * dlt
        if key_arr[pygame.K_d]: # RIGHT
            mov[0] += rit[0] * self.spd * spd_fix * dlt
            mov[2] += rit[2] * self.spd * spd_fix * dlt

        if self.kin == 0: # DEBUG (FLY)
            if key_arr[pygame.K_SPACE]: # FLY UP
                mov[1] += self.spd * spd_fix * dlt
            if key_arr[pygame.K_LSHIFT]: # FLY DOWN
                mov[1] -= self.spd * spd_fix * dlt
        elif self.kin == 1: # NORMAL
            self.vel_y -= self.acc_d * dlt # gravity
            if key_arr[pygame.K_SPACE] and self.grd: # JUMP
                self.vel_y = self.jmp_mag
            mov[1] += self.vel_y * dlt

        self.pos[0] += mov[0]
        self._POS_FIX(0)

        self.pos[2] += mov[2]
        self._POS_FIX(2)

        self.pos[1] += mov[1]
        pos_y_pre = self.pos[1]
        self._POS_FIX(1)
        if self.kin == 1:
            if self.vel_y <= 0 and self.pos[1] > pos_y_pre: # floor hit
                self.vel_y = 0.0
                self.grd = True
            elif self.vel_y > 0 and self.pos[1] < pos_y_pre: # ceiling hit
                self.vel_y = 0.0
                self.grd = False
            else:
                self.grd = False

    def _CAM_GET(self):
        return self.pos, self.rot

    def _CAM_RDR(self): # RENDER CAMERA TRANSFORMATIONS
        # Clear transformation matrix
        glLoadIdentity()
        
        # Apply rotations first, then translation
        glRotatef(-self.rot[0], 1, 0, 0)
        glRotatef(-self.rot[1], 0, 1, 0)
        glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])