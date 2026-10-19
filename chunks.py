import numpy as np

# the world is cut into cubes of CHUNK_SIZE x CHUNK_SIZE x CHUNK_SIZE blocks; each one is drawn (or skipped) as a whole
CHUNK_SIZE = 16
CHUNK_SHIFT = 4 # CHUNK_SIZE = 1 << CHUNK_SHIFT

def set_chunk_size(size):
    # size: a power of 2 (CHUNK_SIZE in .env.pre); has to be called before the world is built
    global CHUNK_SIZE, CHUNK_SHIFT
    CHUNK_SIZE = size
    CHUNK_SHIFT = size.bit_length() - 1

def chunk_of(x, y, z):
    # which chunk the block at (x, y, z) is in; a chunk is named by the position of its corner divided by CHUNK_SIZE (>> rounds down, also for negative positions)
    return (x >> CHUNK_SHIFT, y >> CHUNK_SHIFT, z >> CHUNK_SHIFT)

class ChunkBoxes:
    # the boxes of a group of chunks, and a way to find out which of them are worth drawing from where the camera is
    def __init__(self, keys):
        cells = np.array(keys, dtype=np.float64).reshape(-1, 3)
        self.centers = (cells + 0.5) * CHUNK_SIZE # the middle of each chunk

    def visible(self, planes, camera_pos, view_distance):
        # one True / False per chunk: True if some part of it can be seen
        # planes: the 6 planes of the view (matrices.frustum_planes); a chunk entirely outside any one of them is out of view
        # view_distance: chunks further away than this (from the closest point of the chunk to the camera, so a sphere around the camera) are skipped
        half = CHUNK_SIZE / 2
        normals = planes[:, :3]
        offsets = planes[:, 3]

        # how far the middle of each chunk is in front of (positive) or behind (negative) each plane
        # the chunk reaches half * (|nx| + |ny| + |nz|) further along the normal of a plane than its middle does (that is how far the corner that sticks out most is); if even that is behind the plane, the whole chunk is
        reach = half * np.abs(normals).sum(axis=1)
        inside = ((self.centers @ normals.T + offsets + reach) >= 0).all(axis=1)

        if view_distance is not None:
            # the distance from the camera to the closest point of each box (0 on that axis if the camera is between its sides)
            gap = np.maximum(np.abs(self.centers - np.asarray(camera_pos, dtype=np.float64)) - half, 0.0)
            inside &= (gap * gap).sum(axis=1) <= view_distance * view_distance

        return inside
