import math
import pygame

EPS = 1e-6 # overlaps smaller than this are rounding errors, not collisions


class Camera:
    def __init__(self, fly, jump_speed, gravity, width, height, pos, speed, sensitivity, rot=None, world=None, collision_step=0.375):
        self.fly = fly # True: fly around with no physics; False: gravity and collisions
        self.jump_speed = jump_speed
        self.gravity = gravity
        self.pos = pos
        self.prev_pos = list(pos) # where the player was before the last tick (see render_pos)
        self.width = width # player width
        self.height = height # player height
        self.speed = speed
        self.sensitivity = sensitivity
        self.rot = rot if rot is not None else [0, 0] # [pitch, yaw] in degrees
        self.world = world
        self.collision_step = collision_step # the most the player is moved at a time when checking for blocks (COLLISION_STEP in .env.pre)
        self.vel_y = 0.0
        self.grounded = False

    def set_speed(self, speed):
        self.speed = speed

    def set_pos(self, pos):
        self.vel_y = 0.0
        self.grounded = False
        self.pos = pos
        self.prev_pos = list(pos) # no blending from where the player was before

    def overlapping(self):
        # the blocks the player's box overlaps right now (an overlap smaller than EPS is rounding, not an overlap)
        # the box reaches half the width to each side of the position, `height` below it (the position is the eye) and half the width above it
        if not self.world:
            return []

        r = self.width / 2
        px, py, pz = self.pos
        found = []

        for bx in range(math.floor(px - r + EPS), math.ceil(px + r - EPS)):
            for by in range(math.floor(py - self.height + EPS), math.ceil(py + r - EPS)):
                for bz in range(math.floor(pz - r + EPS), math.ceil(pz + r - EPS)):
                    if (bx, by, bz) in self.world.blocks:
                        found.append((bx, by, bz))

        return found

    def move_axis(self, axis, delta):
        # moves the player along one axis (0 = x, 1 = y, 2 = z) and stops it flat against the first block in the way; returns True if it hit one
        # a long move is cut into steps of at most collision_step blocks: a step is smaller than the player and than any block, so however fast the player goes, no block can be jumped over
        # and the player is always put back on the side it came from (the side the move was coming from), never "out of the nearest side", which for a fast player was the far side of the block
        if delta == 0.0:
            return False

        steps = max(1, math.ceil(abs(delta) / self.collision_step))
        step = delta / steps
        below = self.height if axis == 1 else self.width / 2 # how far the box reaches below / above the position along this axis
        above = self.width / 2

        for _ in range(steps):
            self.pos[axis] += step
            blocks = self.overlapping()

            if blocks:
                if step > 0:
                    self.pos[axis] = min(block[axis] for block in blocks) - above # the front of the box against the face of the nearest block
                else:
                    self.pos[axis] = max(block[axis] for block in blocks) + 1 + below

                return True

        return False

    def unstick(self):
        # the player is inside blocks (put there by set_pos, or a block was placed on it): move it up out of them
        for _ in range(64):
            blocks = self.overlapping()

            if not blocks:
                return

            self.pos[1] = max(block[1] for block in blocks) + 1 + self.height

    def look(self, mouse_rel):
        # MOUSE LOOK, once per frame (not per tick) so that turning follows the mouse right away
        self.rot[0] -= mouse_rel[1] * self.sensitivity # PITCH
        self.rot[1] += mouse_rel[0] * self.sensitivity # YAW

        # CLAMP PITCH
        self.rot[0] = max(-89, min(89, self.rot[0]))

    def tick(self, keys, dt):
        # one physics step of dt seconds (always the same length, see ticks.py): movement, gravity, jumping and collisions
        self.prev_pos = list(self.pos)

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
            if keys[pygame.K_SPACE] and self.grounded: # JUMP
                self.vel_y = self.jump_speed
            move[1] += self.vel_y * dt - 0.5 * self.gravity * dt * dt # the exact distance fallen / risen under constant gravity, so a jump is the same height at any tick rate
            self.vel_y -= self.gravity * dt # gravity

        self.unstick()
        self.move_axis(0, move[0])
        self.move_axis(2, move[2])
        hit = self.move_axis(1, move[1])

        if not self.fly:
            if hit and move[1] < 0: # landed on something
                self.vel_y = 0.0
                self.grounded = True
            elif hit and move[1] > 0: # bumped the head
                self.vel_y = 0.0
                self.grounded = False
            else:
                self.grounded = False

    def render_pos(self, alpha):
        # where to draw the player: alpha (0 to 1, see ticks.py) of the way from where the last tick started to where it ended
        # the physics only moves the player once per tick, so drawing at pos directly would make motion jerk whenever frames and ticks don't line up
        return [prev + (now - prev) * alpha for prev, now in zip(self.prev_pos, self.pos)]
