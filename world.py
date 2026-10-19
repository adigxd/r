from array import array
import numpy as np
from OpenGL.GL import *
import random

# ./
from atlas import OPAQUE, TRANSLUCENT
import buffers
from chunks import ChunkBoxes, chunk_of

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

def unpack_scale(scale, name='scale'):
    # scale / size can be one number (used for x, y and z) or [x, y, z]
    try:
        values = tuple(scale)
    except TypeError:
        values = (scale, scale, scale)

    if len(values) != 3 or any(v <= 0 for v in values):
        raise ValueError(f'"{name}" needs a number above 0 or 3 of them, got {scale}')

    return values

class GlassChunk:
    # the translucent faces of one chunk: they get a small buffer of their own, because blending only comes out right when the faces are drawn from far to near, so their order changes with the camera
    def __init__(self, vertices, centers):
        self.faces = np.frombuffer(vertices, dtype=np.float32).reshape(-1, 48) # one row per face: its 6 vertices of 8 floats
        self.centers = np.frombuffer(centers, dtype=np.float32).reshape(-1, 3) # the middle of every face
        self.vao, self.vbo = buffers.make_block_mesh(self.faces.reshape(-1), dynamic=True)
        self.vertex_count = len(self.faces) * 6
        self.sorted_for = None # where the camera was when the faces were last sorted

    def sort(self, camera_pos, min_move=0.5):
        # redone whenever the camera has moved min_move blocks or more since the last time (GLASS_SORT_DISTANCE in .env.pre)
        if self.sorted_for is not None and sum((a - b) ** 2 for a, b in zip(camera_pos, self.sorted_for)) < min_move * min_move:
            return

        distance = ((self.centers - np.array(camera_pos, dtype=np.float32)) ** 2).sum(axis=1)
        order = np.argsort(-distance, kind='stable') # biggest distance first
        buffers.update_block_mesh(self.vbo, np.ascontiguousarray(self.faces[order]).reshape(-1))
        self.sorted_for = tuple(camera_pos)

    def free(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])

class World:
    def __init__(self, seed, tile_size, atlas_size, tile_opacity=None, glass_sort_distance=0.5):
        # tile_opacity: {(col, row): OPAQUE / CUTOUT / TRANSLUCENT} of the tiles of the atlas (see atlas.py); a tile that isn't in it is opaque
        self.seed = seed
        self.glass_sort_distance = glass_sort_distance # see-through faces are sorted again when the camera has moved this far
        self.tile_size = tile_size
        self.atlas_size = atlas_size
        self.blocks = {} # (x, y, z) : block type
        self.dirty = True # if the world has been modified since the mesh was last built
        # the mesh is cut into chunks (see chunks.py): all the solid ones share one buffer, each being a range of it, and every frame only the ones that can be seen are drawn
        self.vao = None
        self.vbo = None
        self.vertex_count = 0 # in the whole buffer
        self.opaque_boxes = None # ChunkBoxes of the chunks in the buffer
        self.opaque_first = None # for each of them the first vertex of its range
        self.opaque_count = None # and how many vertices the range has
        self.drawn_chunks = 0 # how many chunks the last draw_opaque drew

        # how see-through every block type is: the most see-through of its tiles
        tile_opacity = tile_opacity or {}
        self.opacity = {}

        for name, spec in BLOCK_TYPES.items():
            tiles = [tile for tile_spec in spec.values() for tile in (tile_spec if isinstance(tile_spec, list) else [tile_spec])]
            self.opacity[name] = max(tile_opacity.get(tile, OPAQUE) for tile in tiles)

        self.opaque_types = {name for name, opacity in self.opacity.items() if opacity == OPAQUE}
        self.see_through = len(self.opaque_types) != len(self.opacity) # false: every block hides whatever is behind it, which makes building the mesh a lot simpler and faster

        # the translucent blocks are in meshes of their own, one per chunk (see GlassChunk)
        self.glass_chunks = []
        self.glass_boxes = None

    def set_block(self, x, y, z, block_type):
        self.blocks[(x, y, z)] = block_type
        self.dirty = True # mark the mesh as outdated since we've modified the world

    def has_geometry(self, block_type):
        # whether a block type has geometry ("AIR" and unknown types don't)
        return block_type != 'AIR' and block_type in BLOCK_TYPES

    def exposed_faces(self, x, y, z, block_type):
        # which faces of a block are exposed (not covered by a neighbouring block), in the order front, back, left, right, top, bottom
        # only valid once "AIR" / invalid blocks have been purged from self.blocks (see rebuild_mesh)
        blocks = self.blocks

        if not self.see_through:
            return (
                (x, y, z + 1) not in blocks,
                (x, y, z - 1) not in blocks,
                (x - 1, y, z) not in blocks,
                (x + 1, y, z) not in blocks,
                (x, y + 1, z) not in blocks,
                (x, y - 1, z) not in blocks
            )

        # a face is only hidden by a neighbour that is fully opaque, or by the same translucent block (glass next to glass has no wall in between)
        # leaves next to leaves keep their faces: you see through the holes of the first one into the second
        opaque = self.opaque_types
        same_glass = block_type if self.opacity[block_type] == TRANSLUCENT else None

        def open_to(pos):
            other = blocks.get(pos)

            return other is None or (other not in opaque and other != same_glass)

        return (
            open_to((x, y, z + 1)),
            open_to((x, y, z - 1)),
            open_to((x - 1, y, z)),
            open_to((x + 1, y, z)),
            open_to((x, y + 1, z)),
            open_to((x, y - 1, z))
        )

    def free_buffers(self):
        # free the GPU buffers from the previous build
        if self.vao is not None:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo is not None:
            glDeleteBuffers(1, [self.vbo])

        for chunk in self.glass_chunks:
            chunk.free()

        self.vao = None
        self.vbo = None
        self.vertex_count = 0
        self.opaque_boxes = None
        self.opaque_first = None
        self.opaque_count = None
        self.glass_chunks = []
        self.glass_boxes = None

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

    def add_block_faces(self, x, y, z, block_type, vertices, t_vertices, t_centers):
        # append vertex data for the exposed faces of a block at (x, y, z) of type block_type to vertices (or to t_vertices, with the middle of every face in t_centers, if the block is translucent)
        # faces covered by a neighbouring block are skipped (they can never be seen)
        translucent = self.opacity[block_type] == TRANSLUCENT

        if translucent:
            vertices = t_vertices

        spec = BLOCK_TYPES[block_type]
        tiles = {
            "front": spec.get("all", spec.get("side")),
            "back": spec.get("all", spec.get("side")),
            "left": spec.get("all", spec.get("side")),
            "right": spec.get("all", spec.get("side")),
            "top": spec.get("all", spec.get("top")),
            "bottom": spec.get("all", spec.get("bottom"))
        }

        exposed = self.exposed_faces(x, y, z, block_type)

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

            if translucent:
                t_centers.extend([sum(p[0] for p in pos) / 4, sum(p[1] for p in pos) / 4, sum(p[2] for p in pos) / 4])

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

    def rebuild_mesh(self, progress=None):
        # generate vertex data for the entire world, chunk by chunk
        # progress, if given, is called now and then with how far along the face building is (0 to 1)
        builders = {} # chunk -> (vertices, translucent vertices, middles of the translucent faces); compact float32 storage (a plain list of floats would cost several times the memory)

        # purge "AIR" / invalid blocks first so face culling only ever sees real neighbours
        for key in [key for key, block_type in self.blocks.items() if not self.has_geometry(block_type)]:
            del self.blocks[key]

        last_chunk = None
        builder = None
        total = max(1, len(self.blocks))

        for done, ((x, y, z), block_type) in enumerate(self.blocks.items()):
            if progress and done % 8192 == 0:
                progress(done / total)

            chunk = chunk_of(x, y, z)

            if chunk != last_chunk: # blocks next to each other in the dict are mostly in the same chunk
                builder = builders.get(chunk)

                if builder is None:
                    builder = builders[chunk] = (array('f'), array('f'), array('f'))

                last_chunk = chunk

            self.add_block_faces(x, y, z, block_type, *builder)

        self.free_buffers() # free the previous buffers (otherwise they leak on every rebuild)
        self.dirty = False # mark the mesh as up to date since we've just updated the vertex data

        # the solid chunks: one buffer with one chunk after the other
        solid = [chunk for chunk, builder in builders.items() if builder[0]]

        if solid:
            parts = [np.frombuffer(builders[chunk][0], dtype=np.float32) for chunk in solid]
            counts = np.array([len(part) // 8 for part in parts], dtype=np.int32) # 8 floats per vertex (position, normal, texcoord)

            self.opaque_boxes = ChunkBoxes(solid)
            self.opaque_count = counts
            self.opaque_first = np.concatenate(([0], np.cumsum(counts)[:-1])).astype(np.int32)
            self.vertex_count = int(counts.sum())
            self.vao, self.vbo = buffers.make_block_mesh(np.concatenate(parts))

        # the translucent chunks: a small buffer each
        glass = [chunk for chunk, builder in builders.items() if builder[1]]

        if glass:
            self.glass_boxes = ChunkBoxes(glass)
            self.glass_chunks = [GlassChunk(builders[chunk][1], builders[chunk][2]) for chunk in glass]

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
        # a cube given by its middle and its size instead of its 6 edges
        # size can be one number (a cube) or [x, y, z] (a box); a size of n covers exactly n blocks, so 5 is centered on the block (cx, cy, cz) and 4 starts 2 blocks before it
        sx, sy, sz = unpack_scale(size, 'size')
        x_min = cx - int(sx) // 2
        y_min = cy - int(sy) // 2
        z_min = cz - int(sz) // 2
        self.fill_cube(x_min, x_min + int(sx), y_min, y_min + int(sy), z_min, z_min + int(sz), blocks)

    def fill_sphere(self, cx, cy, cz, radius, blocks, scale=1):
        # scale: stretches the sphere along x, y, z; one number for all 3 or [x, y, z] (so [2, 1, 1] is an ellipsoid twice as wide in x)
        sx, sy, sz = unpack_scale(scale)
        r_sqr = radius * radius

        for x in range(int(cx - radius * sx), int(cx + radius * sx)):
            for y in range(int(cy - radius * sy), int(cy + radius * sy)):
                for z in range(int(cz - radius * sz), int(cz + radius * sz)):
                    dx = (x - cx) / sx
                    dy = (y - cy) / sy
                    dz = (z - cz) / sz
                    if dx * dx + dy * dy + dz * dz < r_sqr:
                        self.set_block(x, y, z, self.pick_block_type(blocks))

    def fill_cylinder(self, cx, cy, cz, radius, height, axis, blocks, scale=1):
        # axis: "y" = vertical, "x" = horizontal along x, "z" = horizontal along z
        # scale: stretches the cylinder along x, y, z; one number for all 3 or [x, y, z] (the stretch along the axis makes it longer, the other two make the circle an ellipse)
        sx, sy, sz = unpack_scale(scale)
        r_sqr = radius * radius

        if axis == "y": # vertical
            for x in range(int(cx - radius * sx), int(cx + radius * sx)):
                for y in range(int(cy), int(cy + height * sy)):
                    for z in range(int(cz - radius * sz), int(cz + radius * sz)):
                        dx = (x - cx) / sx
                        dz = (z - cz) / sz
                        if dx * dx + dz * dz < r_sqr:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "x": # horizontal along x
            for x in range(int(cx), int(cx + height * sx)):
                for y in range(int(cy - radius * sy), int(cy + radius * sy)):
                    for z in range(int(cz - radius * sz), int(cz + radius * sz)):
                        dy = (y - cy) / sy
                        dz = (z - cz) / sz
                        if dy * dy + dz * dz < r_sqr:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "z": # horizontal along z
            for x in range(int(cx - radius * sx), int(cx + radius * sx)):
                for y in range(int(cy - radius * sy), int(cy + radius * sy)):
                    for z in range(int(cz), int(cz + height * sz)):
                        dx = (x - cx) / sx
                        dy = (y - cy) / sy
                        if dx * dx + dy * dy < r_sqr:
                            self.set_block(x, y, z, self.pick_block_type(blocks))

    def fill_cone(self, cx, cy, cz, radius, height, axis, flip, blocks, scale=1):
        # axis: "y" = vertical, "x" = horizontal along x, "z" = horizontal along z
        # flip: True or False; whether the cone is flipped (pointing down/left/back instead of up/right/front)
        # scale: stretches the cone along x, y, z; one number for all 3 or [x, y, z] (the stretch along the axis makes it longer, the other two make the circle an ellipse)
        sx, sy, sz = unpack_scale(scale)
        r_sqr = radius * radius

        if axis == "y": # vertical
            length = height * sy
            for x in range(int(cx - radius * sx), int(cx + radius * sx)):
                for y in range(int(cy), int(cy + length)):
                    for z in range(int(cz - radius * sz), int(cz + radius * sz)):
                        dy = y - cy
                        dx = (x - cx) / sx
                        dz = (z - cz) / sz
                        t = (dy / length) if flip else 1.0 - (dy / length)
                        if dy >= 0 and dx * dx + dz * dz < r_sqr * t * t:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "x": # horizontal along x
            length = height * sx
            for x in range(int(cx), int(cx + length)):
                for y in range(int(cy - radius * sy), int(cy + radius * sy)):
                    for z in range(int(cz - radius * sz), int(cz + radius * sz)):
                        dx = x - cx
                        dy = (y - cy) / sy
                        dz = (z - cz) / sz
                        t = (dx / length) if flip else 1.0 - (dx / length)
                        if dx >= 0 and dy * dy + dz * dz < r_sqr * t * t:
                            self.set_block(x, y, z, self.pick_block_type(blocks))
        elif axis == "z": # horizontal along z
            length = height * sz
            for x in range(int(cx - radius * sx), int(cx + radius * sx)):
                for y in range(int(cy - radius * sy), int(cy + radius * sy)):
                    for z in range(int(cz), int(cz + length)):
                        dz = z - cz
                        dx = (x - cx) / sx
                        dy = (y - cy) / sy
                        t = (dz / length) if flip else 1.0 - (dz / length)
                        if dz >= 0 and dx * dx + dy * dy < r_sqr * t * t:
                            self.set_block(x, y, z, self.pick_block_type(blocks))

    def add_tree(self, x, y, z, height, tree_type):
        if tree_type == "MAPLE":
            h = max(6, height) # minimum maple height of 6
            w = 1

            self.fill_cube_centered(x, y + h, z, (h * 3) // 4, {"LEAF_MAPLE": 1, "AIR": 4})
            self.fill_sphere(x, y + h, z, h // 2, {"LEAF_MAPLE": 1, "AIR": 1})
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
        elif tree_type == "WINDSWEPT":
            pass # placeholder: the LOG_WINDSWEPT / LOG_WINDSWEPT_FULL / LOG_WINDSWEPT_NAKED / LEAF_WINDSWEPT blocks exist, the tree itself isn't written yet

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

    def build(self, world_data, progress=None):
        # build the world from the "world" object of a map file (loaded by config.load)
        # progress, if given, is called now and then with how far along the build is (0 to 1), for a loading bar
        random.seed(self.seed)

        self.blocks = {}
        self.dirty = True

        # placing the shapes is about a seventh of the work, building the mesh is the rest (the progress of the mesh is counted in blocks)
        shapes_share = 0.15
        total = max(1, sum(len(world_data.get(name, [])) for name in ('voxels', 'cubes', 'spheres', 'cylinders', 'cones', 'trees', 'forests')))
        done = 0

        def placed():
            nonlocal done
            done += 1

            if progress:
                progress(shapes_share * done / total)

        for voxel in world_data.get('voxels', []):
            self.add_voxel(voxel['x'], voxel['y'], voxel['z'], voxel['blocks'])
            placed()

        # a cube is either its 6 edges (x_min ... z_max) or its middle and size (x, y, z, size)
        for cube in world_data.get('cubes', []):
            if 'size' in cube:
                self.fill_cube_centered(
                    cube['x'], cube['y'], cube['z'], cube['size'], cube['blocks']
                )
            else:
                self.fill_cube(
                    cube['x_min'], cube['x_max'],
                    cube['y_min'], cube['y_max'],
                    cube['z_min'], cube['z_max'],
                    cube['blocks']
                )

            placed()

        # spheres, cylinders and cones can have a "scale" to stretch them
        for sphere in world_data.get('spheres', []):
            self.fill_sphere(
                sphere['x'], sphere['y'], sphere['z'], sphere['radius'], sphere['blocks'], sphere.get('scale', 1)
            )
            placed()

        for cylinder in world_data.get('cylinders', []):
            self.fill_cylinder(
                cylinder['x'], cylinder['y'], cylinder['z'], cylinder['radius'], cylinder['height'], cylinder['axis'], cylinder['blocks'], cylinder.get('scale', 1)
            )
            placed()

        for cone in world_data.get('cones', []):
            self.fill_cone(
                cone['x'], cone['y'], cone['z'], cone['radius'], cone['height'], cone['axis'], cone['flip'], cone['blocks'], cone.get('scale', 1)
            )
            placed()

        for tree in world_data.get('trees', []):
            self.add_tree(
                tree['x'], tree['y'], tree['z'], tree['height'], tree['type']
            )
            placed()

        for forest in world_data.get('forests', []):
            self.add_forest(
                forest['x'], forest['y'], forest['z'], forest['radius'], forest['height_avg'], forest['height_err'], forest['density'], forest['shape'], forest['type']
            )
            placed()

        mesh_progress = (lambda fraction: progress(shapes_share + (1 - shapes_share) * fraction)) if progress else None
        self.rebuild_mesh(mesh_progress)

        if progress:
            progress(1)

    @property
    def has_glass(self):
        return bool(self.glass_chunks)

    def draw_opaque(self, planes, camera_pos, view_distance):
        # draw the solid chunks that can be seen: inside the view (planes, see matrices.frustum_planes) and not further from the camera than view_distance
        # everything else is never sent to the GPU, which saves it the work of processing all those vertices just to throw them away
        if self.dirty:
            self.rebuild_mesh()

        self.drawn_chunks = 0

        if self.vao is None:
            return

        visible = self.opaque_boxes.visible(planes, camera_pos, view_distance)
        firsts = self.opaque_first[visible]
        counts = self.opaque_count[visible]
        self.drawn_chunks = len(firsts)

        if self.drawn_chunks:
            glBindVertexArray(self.vao)
            glMultiDrawArrays(GL_TRIANGLES, firsts, counts, self.drawn_chunks) # all the chunks in one call (one call per chunk would be slow)

    def draw_translucent(self, planes, camera_pos, view_distance):
        # draw the translucent chunks that can be seen, the furthest first (blending needs that); the caller has to turn blending on and depth writing off
        if self.dirty:
            self.rebuild_mesh()

        if not self.glass_chunks:
            return

        visible = np.nonzero(self.glass_boxes.visible(planes, camera_pos, view_distance))[0]
        distance = ((self.glass_boxes.centers[visible] - np.array(camera_pos)) ** 2).sum(axis=1)

        for i in visible[np.argsort(-distance, kind='stable')]:
            chunk = self.glass_chunks[i]
            chunk.sort(camera_pos, self.glass_sort_distance) # the faces inside a chunk, furthest first

            glBindVertexArray(chunk.vao)
            glDrawArrays(GL_TRIANGLES, 0, chunk.vertex_count)
