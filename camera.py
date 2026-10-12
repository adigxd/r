import math
import pygame


class Camera:
    def __init__(self, fly, jump_speed, gravity, width, height, pos, speed, sensitivity, rot=None, world=None):
        self.fly = fly # True: fly around with no physics; False: gravity and collisions
        self.jump_speed = jump_speed
        self.gravity = gravity
        self.pos = pos
        self.width = width # player width
        self.height = height # player height
        self.speed = speed
        self.sensitivity = sensitivity
        self.rot = rot if rot is not None else [0, 0] # [pitch, yaw] in degrees
        self.world = world
        self.vel_y = 0.0
        self.grounded = False

    def set_speed(self, speed):
        self.speed = speed

    def set_pos(self, pos):
        self.vel_y = 0.0
        self.grounded = False
        self.pos = pos

    def push_out(self, axis):
        # moves the player out of any block it overlaps along one axis (0 = x, 1 = y, 2 = z)
        if not self.world:
            return

        r = self.width / 2 # collision half-extent (box is r * 2 wide)

        px, py, pz = self.pos

        min_x = int(math.floor(px - r))
        max_x = int(math.ceil(px + r))
        min_y = int(math.floor(py - self.height)) # height
        max_y = int(math.ceil(py + r))
        min_z = int(math.floor(pz - r))
        max_z = int(math.ceil(pz + r))

        for bx in range(min_x, max_x + 1):
            for by in range(min_y, max_y + 1):
                for bz in range(min_z, max_z + 1):
                    if (bx, by, bz) not in self.world.blocks:
                        continue

                    # "minimum of upper range minus the maximum of lower range" gives the amount of overlap
                    ox = min(self.pos[0] + r, bx + 1) - max(self.pos[0] - r, bx)
                    oy = min(self.pos[1] + r, by + 1) - max(self.pos[1] - self.height, by)
                    oz = min(self.pos[2] + r, bz + 1) - max(self.pos[2] - r, bz)

                    if ox <= 0 or oy <= 0 or oz <= 0:
                        continue

                    if axis == 0:
                        self.pos[0] += ox if self.pos[0] > bx + 0.5 else -ox
                    elif axis == 1:
                        self.pos[1] += oy if self.pos[1] > by + 0.5 else -oy
                    else:
                        self.pos[2] += oz if self.pos[2] > bz + 0.5 else -oz

    def update(self, keys, mouse_rel, dt=1.0):
        # MOUSE LOOK
        self.rot[0] -= mouse_rel[1] * self.sensitivity # PITCH
        self.rot[1] += mouse_rel[0] * self.sensitivity # YAW

        # CLAMP PITCH
        self.rot[0] = max(-89, min(89, self.rot[0]))

        # FORWARD AND RIGHT VECTORS
        yaw = math.radians(self.rot[1])

        forward = [
            math.sin(yaw),
            0,
            -math.cos(yaw)
        ]

        right = [
            math.cos(yaw),
            0,
            math.sin(yaw)
        ]

        diagonal_scale = 1

        # DIAGONAL MOVEMENT FIX
        if (keys[pygame.K_w] and keys[pygame.K_a]) or \
           (keys[pygame.K_w] and keys[pygame.K_d]) or \
           (keys[pygame.K_s] and keys[pygame.K_a]) or \
           (keys[pygame.K_s] and keys[pygame.K_d]):
            diagonal_scale = 0.7071 # 1/sqrt(2) to maintain consistent speed when moving diagonally

        move = [0.0, 0.0, 0.0]

        if keys[pygame.K_w]: # FORWARD
            move[0] += forward[0] * self.speed * diagonal_scale * dt
            move[2] += forward[2] * self.speed * diagonal_scale * dt
        if keys[pygame.K_s]: # BACKWARD
            move[0] -= forward[0] * self.speed * diagonal_scale * dt
            move[2] -= forward[2] * self.speed * diagonal_scale * dt
        if keys[pygame.K_a]: # LEFT
            move[0] -= right[0] * self.speed * diagonal_scale * dt
            move[2] -= right[2] * self.speed * diagonal_scale * dt
        if keys[pygame.K_d]: # RIGHT
            move[0] += right[0] * self.speed * diagonal_scale * dt
            move[2] += right[2] * self.speed * diagonal_scale * dt

        if self.fly: # DEBUG (FLY)
            if keys[pygame.K_SPACE]: # FLY UP
                move[1] += self.speed * diagonal_scale * dt
            if keys[pygame.K_LSHIFT]: # FLY DOWN
                move[1] -= self.speed * diagonal_scale * dt
        else: # NORMAL
            self.vel_y -= self.gravity * dt # gravity
            if keys[pygame.K_SPACE] and self.grounded: # JUMP
                self.vel_y = self.jump_speed
            move[1] += self.vel_y * dt

        self.pos[0] += move[0]
        self.push_out(0)

        self.pos[2] += move[2]
        self.push_out(2)

        self.pos[1] += move[1]
        pos_y_before = self.pos[1]
        self.push_out(1)
        if not self.fly:
            if self.vel_y <= 0 and self.pos[1] > pos_y_before: # floor hit
                self.vel_y = 0.0
                self.grounded = True
            elif self.vel_y > 0 and self.pos[1] < pos_y_before: # ceiling hit
                self.vel_y = 0.0
                self.grounded = False
            else:
                self.grounded = False
