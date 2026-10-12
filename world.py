from array import array
import numpy as np
from OpenGL.GL import *
import random

# ./
import buffers

# format: "BLOCK_NAME": {"top": (col, row), "side": (col, row), "bottom": (col, row)} or {"all": (col, row)} (if all faces of the block use the same texture)
# a (col, row) can also be a list of them; one of the list is picked at random for every face
# "AIR" is typically used in map files to represent empty space and is not included here since it doesn't correspond to an actual block type that needs vertex data
#       it is treated the same way an invalid block type would be (ignored and not added to the vertex array)
BLOCK_TYPES = {
    "STONE": {"all": (0, 0)},
    "STONE_SOLID": {"all": (1, 0)},
    "STONE_BRICK": {"all": (2, 0)},
    "STONE_LIGHT": {"all": (0, 1)},
    "STONE_SOLID_LIGHT": {"all": (1, 1)},
    "STONE_BRICK_LIGHT": {"all": (2, 1)},
    "STONE_BOLD": {"all": (0, 2)},
    "STONE_SOLID_BOLD": {"all": (1, 2)},
    "STONE_BRICK_BOLD": {"all": (2, 2)},
    "STONE_DARK": {"all": (0, 3)},
    "STONE_SOLID_DARK": {"all": (1, 3)},
    "STONE_BRICK_DARK": {"all": (2, 3)},
    "SAND": {"all": [(15, 15), (14, 15), (13, 15), (12, 15)]},
    "DIRT": {"all": [(15, 14), (14, 14), (13, 14), (12, 14)]},
    "GRASS": {"all": [(15, 13), (14, 13), (13, 13), (12, 13)]},
    "LOG_MAPLE": {"top": (0, 6), "side": (0, 5), "bottom": (0, 6)},
    "LOG_MAPLE_FULL": {"all": (0, 5)},
    "LOG_MAPLE_NAKED": {"all": (0, 8)},
    "LOG_PINE": {"top": (1, 6), "side": (1, 5), "bottom": (1, 6)},
    "LOG_PINE_FULL": {"all": (1, 5)},
    "LOG_PINE_NAKED": {"all": (1, 8)},
    "LOG_WINDSWEPT": {"top": (2, 6), "side": (2, 5), "bottom": (2, 6)},
    "LOG_WINDSWEPT_FULL": {"all": (2, 5)},
    "LOG_WINDSWEPT_NAKED": {"all": (2, 8)},
    "LOG_REDWOOD": {"top": (3, 6), "side": (3, 5), "bottom": (3, 6)},
    "LOG_REDWOOD_FULL": {"all": (3, 5)},
    "LOG_REDWOOD_NAKED": {"all": (3, 8)},
    "LEAF_MAPLE": {"all": (0, 7)},
    "LEAF_PINE": {"all": (1, 7)},
    "LEAF_WINDSWEPT": {"all": (2, 7)},
    "LEAF_REDWOOD": {"all": (3, 7)},
    "STONE_DEBUG": {"top": (6, 0), "side": (0, 0), "bottom": (0, 0)},
}

class World:
    def __init__(self, seed, tile_size, atlas_size):
        self.seed = seed
        self.tile_size = tile_size
        self.atlas_size = atlas_size
        self.blocks = {} # (x, y, z) : block type
        self.dirty = True # if the world has been modified since the mesh was last built
        self.vao = None
        self.vbo = None
        self.vertex_count = 0

    def set_block(self, x, y, z, block_type):
        self.blocks[(x, y, z)] = block_type
        self.dirty = True # mark the mesh as outdated since we've modified the world

    def get_block(self, x, y, z):
        return self.blocks.get((x, y, z), None)

    def has_geometry(self, block_type):
        # whether a block type has geometry ("AIR" and unknown types don't)
        return block_type != 'AIR' and block_type in BLOCK_TYPES

    def exposed_faces(self, x, y, z):
        # which faces of a block are exposed (not covered by a neighbouring block), in the order front, back, left, right, top, bottom
        # only valid once "AIR" / invalid blocks have been purged from self.blocks (see rebuild_mesh)
        blocks = self.blocks

        return (
            (x, y, z + 1) not in blocks,
            (x, y, z - 1) not in blocks,
            (x - 1, y, z) not in blocks,
            (x + 1, y, z) not in blocks,
            (x, y + 1, z) not in blocks,
            (x, y - 1, z) not in blocks
        )

    def free_buffers(self):
        # free the GPU buffers from the previous build
        if self.vao is not None:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo is not None:
            glDeleteBuffers(1, [self.vbo])

        self.vao = None
        self.vbo = None
        self.vertex_count = 0

    def pick_uvs(self, tile):
        # tile can be a single (col, row) tuple or a list of tuples for random selection
        if isinstance(tile, list):
            return self.tile_uvs(*random.choice(tile))
        return self.tile_uvs(*tile)

    def tile_uvs(self, col, row):
        # get texture coordinates for a block located at (col, row) in the texture atlas
        u0 = (col * self.tile_size) / self.atlas_size
        v0 = (row * self.tile_size) / self.atlas_size
        u1 = ((col + 1) * self.tile_size) / self.atlas_size
        v1 = ((row + 1) * self.tile_size) / self.atlas_size

        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

    def add_block_faces(self, x, y, z, block_type, vertices):
        # append vertex data for the exposed faces of a block at (x, y, z) of type block_type to vertices
        # faces covered by a neighbouring block are skipped (they can never be seen)
        spec = BLOCK_TYPES[block_type]
        tiles = {
            "front": spec.get("all", spec.get("side")),
            "back": spec.get("all", spec.get("side")),
            "left": spec.get("all", spec.get("side")),
            "right": spec.get("all", spec.get("side")),
            "top": spec.get("all", spec.get("top")),
            "bottom": spec.get("all", spec.get("bottom"))
        }

        exposed = self.exposed_faces(x, y, z)

        pos_front = [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
        pos_back = [(x + 1, y, z), (x, y, z), (x, y + 1, z), (x + 1, y + 1, z)]
        pos_left = [(x, y, z), (x, y, z + 1), (x, y + 1, z + 1), (x, y + 1, z)]
        pos_right = [(x + 1, y, z + 1), (x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1)]
        pos_top = [(x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z), (x, y + 1, z)]
        pos_bottom = [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]

        normal_front = (0, 0, 1)
        normal_back = (0, 0, -1)
        normal_left = (-1, 0, 0)
        normal_right = (1, 0, 0)
        normal_top = (0, 1, 0)
        normal_bottom = (0, -1, 0)

        def add_face(pos, uvs, normal):
            # add a face to the vertex array (two triangles)
            for i in [0, 1, 2]:
                vertices.extend([*pos[i], *normal, *uvs[i]])
            for i in [0, 2, 3]:
                vertices.extend([*pos[i], *normal, *uvs[i]])

        if exposed[0]:
            add_face(pos_front, self.pick_uvs(tiles["front"]), normal_front)
        if exposed[1]:
            add_face(pos_back, self.pick_uvs(tiles["back"]), normal_back)
        if exposed[2]:
            add_face(pos_left, self.pick_uvs(tiles["left"]), normal_left)
        if exposed[3]:
            add_face(pos_right, self.pick_uvs(tiles["right"]), normal_right)
        if exposed[4]:
            add_face(pos_top, self.pick_uvs(tiles["top"]), normal_top)
        if exposed[5]:
            add_face(pos_bottom, self.pick_uvs(tiles["bottom"]), normal_bottom)

    def rebuild_mesh(self):
        # generate vertex data for the entire world
        vertices = array('f') # compact float32 storage (a plain list of floats would cost several times the memory)

        # purge "AIR" / invalid blocks first so face culling only ever sees real neighbours
        for key in [key for key, block_type in self.blocks.items() if not self.has_geometry(block_type)]:
            del self.blocks[key]

        for (x, y, z), block_type in self.blocks.items():
            self.add_block_faces(x, y, z, block_type, vertices)

        self.free_buffers() # free the previous buffers (otherwise they leak on every rebuild)
        self.dirty = False # mark the mesh as up to date since we've just updated the vertex data

        # don't try to draw if there's nothing to draw
        if not vertices:
            return

        vertex_data = np.frombuffer(vertices, dtype=np.float32)
        self.vao, self.vbo = buffers.make_block_mesh(vertex_data)
        self.vertex_count = len(vertices) // 8 # 8 floats per vertex (position, normal, texcoord)

    def pick_block_type(self, choices):
        # choices can be a list (equal chance) or a dict {"TYPE": weight} for weighted selection
        if isinstance(choices, dict):
            return random.choices(list(choices.keys()), weights=list(choices.values()), k=1)[0]

        return random.choice(choices)

    def add_voxel(self, x, y, z, blocks):
        self.set_block(x, y, z, self.pick_block_type(blocks))

    def fill_cube(self, x_min, x_max, y_min, y_max, z_min, z_max, blocks):
        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                for z in range(z_min, z_max):
                    self.set_block(x, y, z, self.pick_block_type(blocks))

    def fill_cube_centered(self, cx, cy, cz, size, blocks):
        half = size // 2
        self.fill_cube(cx - half, cx + half, cy - half, cy + half, cz - half, cz + half, blocks)

    def fill_sphere(self, cx, cy, cz, radius, blocks):
        r_sqr = radius * radius

        for x in range(int(cx - radius), int(cx + radius)):
            for y in range(int(cy - radius), int(cy + radius)):
                for z in range(int(cz - radius), int(cz + radius)):
                    dx = x - cx
                    dy = y - cy
                    dz = z - cz
                    if dx * dx + dy * dy + dz * dz < r_sqr:
                        self.set_block(x, y, z, self.pick_block_type(blocks))

    def fill_cylinder(self, cx, cy, cz, radius, height, axis, blocks):
        # axis: "y" = vertical, "x" = horizontal along x, "z" = horizontal along z

        r_sqr = radius * radius

        if axis == "y": # vertical
            for x in range(int(cx - radius), int(cx + radius)):
                for y in range(int(cy), int(cy + height)):
                    for z in range(int(cz - radius), int(cz + radius)):
                        dx = x - cx
                        dz = z - cz
                        if dx * dx + dz * dz < r_sqr:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "x": # horizontal along x
            for x in range(int(cx), int(cx + height)):
                for y in range(int(cy - radius), int(cy + radius)):
                    for z in range(int(cz - radius), int(cz + radius)):
                        dy = y - cy
                        dz = z - cz
                        if dy * dy + dz * dz < r_sqr:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "z": # horizontal along z
            for x in range(int(cx - radius), int(cx + radius)):
                for y in range(int(cy - radius), int(cy + radius)):
                    for z in range(int(cz), int(cz + height)):
                        dx = x - cx
                        dy = y - cy
                        if dx * dx + dy * dy < r_sqr:
                            self.set_block(x, y, z, self.pick_block_type(blocks))

    def fill_cone(self, cx, cy, cz, radius, height, axis, flip, blocks):
        # axis: "y" = vertical, "x" = horizontal along x, "z" = horizontal along z
        # flip: True or False; whether the cone is flipped (pointing down/left/back instead of up/right/front)

        r_sqr = radius * radius

        if axis == "y": # vertical
            for x in range(int(cx - radius), int(cx + radius)):
                for y in range(int(cy), int(cy + height)):
                    for z in range(int(cz - radius), int(cz + radius)):
                        dy = y - cy
                        dx = x - cx
                        dz = z - cz
                        t = (dy / height) if flip else 1.0 - (dy / height)
                        if dy >= 0 and dx * dx + dz * dz < r_sqr * t * t:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "x": # horizontal along x
            for x in range(int(cx), int(cx + height)):
                for y in range(int(cy - radius), int(cy + radius)):
                    for z in range(int(cz - radius), int(cz + radius)):
                        dx = x - cx
                        dy = y - cy
                        dz = z - cz
                        t = (dx / height) if flip else 1.0 - (dx / height)
                        if dx >= 0 and dy * dy + dz * dz < r_sqr * t * t:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "z": # horizontal along z
            for x in range(int(cx - radius), int(cx + radius)):
                for y in range(int(cy - radius), int(cy + radius)):
                    for z in range(int(cz), int(cz + height)):
                        dz = z - cz
                        dx = x - cx
                        dy = y - cy
                        t = (dz / height) if flip else 1.0 - (dz / height)
                        if dz >= 0 and dx * dx + dy * dy < r_sqr * t * t:
                            self.set_block(x, y, z, self.pick_block_type(blocks))

    def add_tree(self, x, y, z, height, tree_type):
        if tree_type == "MAPLE":
            h = max(6, height) # minimum maple height of 6
            w = 1

            #self.fill_cube_centered(x, y + h, z, (h * 3) // 4, {"LEAF_MAPLE": 1, "AIR": 4})
            #self.fill_sphere(x, y + h, z, h // 2, {"LEAF_MAPLE": 1, "AIR": 1})
            self.fill_cylinder(x, y, z, w, h - 1, "y", ["LOG_MAPLE"]) # trunk h-1 blocks
            self.add_voxel(x, y + h - 1, z, ["LOG_MAPLE_FULL"]) # tip at top, total height h
        elif tree_type == "PINE":
            h = max(16, height) # minimum pine height of 16
            w = 1

            self.fill_cone(x, y + h // 4, z, h // 4, h // 8, "y", True, {"LEAF_PINE": 1, "AIR": 3})
            self.fill_cone(x, y + ((h * 7) // 8), z, h // 8, h // 3, "y", False, {"LEAF_PINE": 1, "AIR": 1})
            self.fill_cone(x, y + ((h * 3) // 4), z, h // 7, h // 3, "y", False, {"LEAF_PINE": 1, "AIR": 1})
            self.fill_cone(x, y + ((h * 5) // 8), z, h // 6, h // 3, "y", False, {"LEAF_PINE": 1, "AIR": 2})
            self.fill_cone(x, y + (h // 2), z, h // 5, h // 3, "y", False, {"LEAF_PINE": 1, "AIR": 2})
            self.fill_cone(x, y + ((h * 3) // 8), z, h // 4, h // 3, "y", False, {"LEAF_PINE": 1, "AIR": 3})
            self.fill_cylinder(x, y, z, w, h - 1, "y", ["LOG_PINE"]) # trunk h-1 blocks
            self.add_voxel(x, y + h - 1, z, ["LOG_PINE_FULL"]) # tip at top, total height h
        elif tree_type == "REDWOOD":
            h = max(32, height) # minimum redwood height of 32
            w = max(1, (h // 32))

            self.fill_cone(x, y + h // 4, z, h // 4, h // 8, "y", True, {"LEAF_REDWOOD": 1, "AIR": 3})
            self.fill_cone(x, y + ((h * 7) // 8), z, h // 8, h // 3, "y", False, {"LEAF_REDWOOD": 1, "AIR": 1})
            self.fill_cone(x, y + ((h * 3) // 4), z, h // 7, h // 3, "y", False, {"LEAF_REDWOOD": 1, "AIR": 1})
            self.fill_cone(x, y + ((h * 5) // 8), z, h // 6, h // 3, "y", False, {"LEAF_REDWOOD": 1, "AIR": 2})
            self.fill_cone(x, y + (h // 2), z, h // 5, h // 3, "y", False, {"LEAF_REDWOOD": 1, "AIR": 2})
            self.fill_cone(x, y + ((h * 3) // 8), z, h // 4, h // 3, "y", False, {"LEAF_REDWOOD": 1, "AIR": 3})
            self.fill_cylinder(x, y, z, w, h - 1, "y", ["LOG_REDWOOD"]) # trunk h-1 blocks
            self.add_voxel(x, y + h - 1, z, ["LOG_REDWOOD_FULL"]) # tip at top, total height h

    def add_forest(self, x, y, z, radius, height_avg, height_err, density, shape, tree_type):
        # example function call: add_forest(0, 0, 0, 16, 20, 4, 0.25, "circle", "PINE")
        # example map file entry: {"x": 0, "y": 0, "z": 0, "radius": 16, "height_avg": 20, "height_err": 4, "density": 0.25, "shape": "circle", "type": "PINE"}
        # x, y, z: center coordinates of the forest area
        # height_avg: average tree height; height_err: maximum random deviation from the average height
        # density: 0 to 1; chance for a tree to spawn at each coordinate location within the radius
        # shape: "circle" = circle of trees, "square" = square
        # tree_type: analogous to tree types

        # circular forest area
        if shape == "circle":
            r_sqr = radius * radius
            for x_off in range(-radius, radius):
                for z_off in range(-radius, radius):
                    if x_off * x_off + z_off * z_off < r_sqr and random.random() < density:
                        height = random.randint(height_avg - height_err, height_avg + height_err)
                        self.add_tree(x + x_off, y, z + z_off, height, tree_type)
        # square forest area
        elif shape == "square":
            for x_off in range(-radius, radius):
                for z_off in range(-radius, radius):
                    if random.random() < density:
                        height = random.randint(height_avg - height_err, height_avg + height_err)
                        self.add_tree(x + x_off, y, z + z_off, height, tree_type)

    def build(self, world_data):
        # build the world from the "world" object of a map file (loaded by config.load)
        random.seed(self.seed)

        self.blocks = {}
        self.dirty = True

        for voxel in world_data.get('voxels', []):
            self.add_voxel(voxel['x'], voxel['y'], voxel['z'], voxel['blocks'])

        for cube in world_data.get('cubes', []):
            self.fill_cube(
                cube['x_min'], cube['x_max'],
                cube['y_min'], cube['y_max'],
                cube['z_min'], cube['z_max'],
                cube['blocks']
            )

        for sphere in world_data.get('spheres', []):
            self.fill_sphere(
                sphere['x'], sphere['y'], sphere['z'], sphere['radius'], sphere['blocks']
            )

        for cylinder in world_data.get('cylinders', []):
            self.fill_cylinder(
                cylinder['x'], cylinder['y'], cylinder['z'], cylinder['radius'], cylinder['height'], cylinder['axis'], cylinder['blocks']
            )

        for cone in world_data.get('cones', []):
            self.fill_cone(
                cone['x'], cone['y'], cone['z'], cone['radius'], cone['height'], cone['axis'], cone['flip'], cone['blocks']
            )

        for tree in world_data.get('trees', []):
            self.add_tree(
                tree['x'], tree['y'], tree['z'], tree['height'], tree['type']
            )

        for forest in world_data.get('forests', []):
            self.add_forest(
                forest['x'], forest['y'], forest['z'], forest['radius'], forest['height_avg'], forest['height_err'], forest['density'], forest['shape'], forest['type']
            )

        self.rebuild_mesh()

    def get_mesh(self):
        if self.dirty:
            self.rebuild_mesh()

        return self.vao, self.vertex_count
