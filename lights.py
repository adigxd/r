import math
import numpy as np

CELL_SIZE = 64 # the lights of a map are sorted into cubes of this size, so a frame only has to look at the lights of the cubes that can be seen
FADE_TIME = 0.25 # seconds a light takes to fade in or out when the choice of which lights to use changes (see LightSet.select)

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
        self.weights = [] # how much of its intensity each light of the last select gets (see select)
        self.fade = {} # light -> weight, of the lights that were sent last frame (only used when a time step is given to select)
        self.matter_before = set() # the lights that could light something visible last frame, sent or not

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

    def select(self, planes, camera_pos, view_distance, limit, dt=None):
        # the lights worth sending to the shader this frame, at most limit of them; self.weights says how much of its intensity each one gets
        # 1. a light matters if its sphere (its position and radius) touches what the camera can see: it can be behind the camera and still light things in front of it, so being outside the view isn't enough, the whole sphere has to be
        # 2. and it doesn't matter if even the nearest point of that sphere is further away than view_distance, since nothing there is drawn
        # 3. if still more than limit lights matter, the ones that probably light the most of the screen win: bright, big and close to the camera
        # dt (the time of the frame, in seconds): with it, a light that wins or loses a place in 3 doesn't switch on or off but fades over FADE_TIME (and a light that is already in has to be a bit worse than a newcomer to lose its place),
        # otherwise lights flicker when the camera moves and the ranking changes; without it every light that is picked has its whole intensity
        chosen = self.follow[:limit]
        weights = [1.0] * len(chosen)
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
                over = len(ids) > room
                score = self.strength[ids] * radius / (distance + radius) if over else None

                if dt is None:
                    if over:
                        ids = ids[np.argpartition(-score, room - 1)[:room]]

                    picked = [int(i) for i in self.fixed[np.sort(ids)]]
                    picked_weights = [1.0] * len(picked)
                    self.fade = {}
                    self.matter_before = set()
                else:
                    picked, picked_weights = self.fade_in_out([int(i) for i in self.fixed[ids]], score, room, dt)

                chosen = chosen + picked
                weights = weights + picked_weights
            else:
                self.fade = {}
                self.matter_before = set()
        else:
            self.fade = {}
            self.matter_before = set()

        self.weights = weights

        return [self.lights[i] for i in chosen]

    def fade_in_out(self, lights, score, room, dt):
        # lights: the fixed lights that matter (their indices); score: how much each of them matters, only given if there are more than room of them
        # returns the lights to send and their weights: the best ones, those that stay get to full weight, newcomers fade in, those that lost their place fade out for a while in a few places kept free for that
        # only that many lights may lose their place at a time (the places kept free for fading out): if the ranking changes more than that in one frame, the best of the rest keep their place for now and the newcomers that would have taken it wait, so a light never switches off in one frame
        step = dt / FADE_TIME
        first = not self.fade # nothing was sent before (the first frame): no reason to fade in
        new = {}

        if score is None:
            for light in lights:
                if light in self.fade:
                    new[light] = min(1.0, self.fade[light] + step)
                else: # one that has only just started to reach something visible has nothing to show yet, so it is there at once; one that was left out for lack of room fades in
                    new[light] = 1.0 if (first or light not in self.matter_before) else step
        else:
            reserve = room // 8 if room >= 8 else 0 # these places are for lights that are fading out
            keep = room - reserve
            bonus = np.array([1.3 if light in self.fade else 1.0 for light in lights])
            rank = dict(zip(lights, score * bonus)) # a light that is already in has to be a bit worse than a newcomer to lose its place
            target = [lights[int(i)] for i in np.argpartition(-(score * bonus), keep - 1)[:keep]]

            if not first and reserve:
                leaving = [light for light in self.fade if light in rank and light not in target]
                too_many = len(leaving) - reserve

                if too_many > 0:
                    stay = sorted(leaving, key=rank.get, reverse=True)[:too_many]
                    waiting = sorted((light for light in target if light not in self.fade), key=rank.get)[:too_many] # the worst newcomers
                    target = [light for light in target if light not in waiting] + stay

            for light in target:
                new[light] = 1.0 if first else min(1.0, self.fade.get(light, 0.0) + step)

            for light, w in self.fade.items():
                if light not in new and light in rank and w - step > 0:
                    new[light] = w - step

        self.fade = new
        self.matter_before = set(lights)
        order = sorted(new)

        return order, [new[light] for light in order]
