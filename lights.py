import math
import numpy as np

CELL_SIZE = 64 # the lights of a map are sorted into cubes of this size, so a frame only has to look at the lights of the cubes that can be seen

def light_position(light, player_pos):
    # where a light is in the world
    if light.follow_player:
        pos = [player_pos[i] + light.pos[i] for i in range(3)] # light.pos is the offset from the player
    else:
        pos = list(light.pos)

    if light.snap:
        pos = [math.floor(v) + 0.5 for v in pos] # middle of the block the light is in

    return pos

class LightSet:
    # all the lights of a map; a map can have any number, but the shader can only take a few at a time (see select)
    def __init__(self, lights):
        self.lights = lights
        self.follow = [i for i, light in enumerate(lights) if light.follow_player] # these are always where the player is, so always relevant

        fixed = [i for i, light in enumerate(lights) if not light.follow_player]
        self.fixed = np.array(fixed, dtype=np.int64)
        self.pos = np.array([light_position(lights[i], None) for i in fixed], dtype=np.float64).reshape(-1, 3)
        self.radius = np.array([lights[i].radius for i in fixed], dtype=np.float64)
        self.strength = np.array([abs(lights[i].intensity) for i in fixed], dtype=np.float64)
        self.relevant = len(self.follow) # how many lights could light something visible in the last select, before the limit was applied

        # the fixed lights sorted into cubes: cell_of says which cube each light is in, and every cube has a middle and a reach
        self.cell_of = np.zeros(0, dtype=np.int64)
        self.cell_centers = np.zeros((0, 3))
        self.cell_reach = np.zeros(0) # the biggest radius of any light in the cube: the cube counts as that much bigger

        if len(fixed):
            cells, cell_of = np.unique(np.floor(self.pos / CELL_SIZE).astype(np.int64), axis=0, return_inverse=True)
            self.cell_of = cell_of.ravel()
            self.cell_centers = (cells + 0.5) * CELL_SIZE
            self.cell_reach = np.zeros(len(cells))
            np.maximum.at(self.cell_reach, self.cell_of, self.radius)

    def select(self, planes, camera_pos, view_distance, limit):
        # the lights worth sending to the shader this frame, at most limit of them
        # 1. a light matters if its sphere (its position and radius) touches what the camera can see: it can be behind the camera and still light things in front of it, so being outside the view isn't enough, the whole sphere has to be
        # 2. and it doesn't matter if even the nearest point of that sphere is further away than view_distance, since nothing there is drawn
        # 3. if still more than limit lights matter, the ones that probably light the most of the screen win: bright, big and close to the camera
        chosen = self.follow[:limit]
        self.relevant = len(self.follow)

        if len(self.fixed) and limit > len(chosen):
            camera = np.asarray(camera_pos, dtype=np.float64)
            normals = planes[:, :3]

            # first the cubes (a few hundred instead of all the lights): the same tests, with the cube made as much bigger as its biggest light
            # if the sphere of a light touches the view then so does its cube made bigger by that radius, so no light that matters is lost here
            half = CELL_SIZE / 2
            margin = self.cell_centers @ normals.T + planes[:, 3] + half * np.abs(normals).sum(axis=1) + self.cell_reach[:, None]
            cells = (margin >= 0).all(axis=1)

            if view_distance is not None:
                gap = np.maximum(np.abs(self.cell_centers - camera) - half, 0.0)
                cells &= np.sqrt((gap * gap).sum(axis=1)) - self.cell_reach <= view_distance

            ids = np.nonzero(cells[self.cell_of])[0] # the lights in the cubes that can be seen

            if len(ids):
                # now the exact test for those lights
                pos = self.pos[ids]
                radius = self.radius[ids]

                # how far in front of each of the 6 planes of the view the middle of each light is (negative = behind it); the sphere is outside if it is behind one by more than its radius
                inside = (pos @ normals.T + planes[:, 3] >= -radius[:, None]).all(axis=1)
                ids, pos, radius = ids[inside], pos[inside], radius[inside]

                distance = np.sqrt(((pos - camera) ** 2).sum(axis=1))

                if view_distance is not None:
                    inside = distance - radius <= view_distance
                    ids, radius, distance = ids[inside], radius[inside], distance[inside]

                self.relevant += len(ids)
                room = limit - len(chosen)

                if len(ids) > room:
                    score = self.strength[ids] * radius / (distance + radius)
                    ids = ids[np.argpartition(-score, room - 1)[:room]]

                chosen = chosen + [int(i) for i in self.fixed[np.sort(ids)]]

        return [self.lights[i] for i in chosen]
