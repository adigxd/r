import math
from OpenGL.GL import *
import pygame

# ./
import dbg
# from kin import __KIN__ # TODO: IMPLEMENT

from dotenv import load_dotenv
load_dotenv()

class __CAM__:
    def __init__(self, pos, spd, sen, rot=[0, 0], map=None):
        self.pos = pos
        self.spd = spd
        self.sen = sen
        self.rot = rot
        self.map = map
    
    def _SPD_SET(self, spd):
        self.spd = spd
    
    def _SEN_SET(self, sen):
        self.sen = sen
    
    def _MAP_SET(self, map):
        self.map = map

    def _POS_FIX(self):
        if not self.map:
            return

        r = 0.5  # collision radius

        px, py, pz = self.pos

        min_x = int(math.floor(px - r))
        max_x = int(math.ceil(px + r))
        min_y = int(math.floor(py - r))
        max_y = int(math.ceil(py + r))
        min_z = int(math.floor(pz - r))
        max_z = int(math.ceil(pz + r))

        for bx in range(min_x, max_x + 1):
            for by in range(min_y, max_y + 1):
                for bz in range(min_z, max_z + 1):
                    if (bx, by, bz) not in self.map.blc_arr:
                        continue

                    # find closest point on block AABB to camera
                    cx = max(bx, min(self.pos[0], bx + 1))
                    cy = max(by, min(self.pos[1], by + 1))
                    cz = max(bz, min(self.pos[2], bz + 1))

                    dx = self.pos[0] - cx
                    dy = self.pos[1] - cy
                    dz = self.pos[2] - cz

                    dist = math.sqrt(dx*dx + dy*dy + dz*dz)

                    if 0 < dist < r:
                        # push camera out along the penetration normal
                        scale = (r - dist) / dist
                        self.pos[0] += dx * scale
                        self.pos[1] += dy * scale
                        self.pos[2] += dz * scale
                    elif dist == 0:
                        # dead center inside block, push up as fallback
                        self.pos[1] += r

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
        
        self._POS_FIX()
    
    def _CAM_GET(self):
        return self.pos, self.rot

    def _CAM_RDR(self): # RENDER CAMERA TRANSFORMATIONS
        # Clear transformation matrix
        glLoadIdentity()
        
        # Apply rotations first, then translation
        glRotatef(-self.rot[0], 1, 0, 0)
        glRotatef(-self.rot[1], 0, 1, 0)
        glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])