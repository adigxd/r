import numpy as np
import pygame

# how see-through a tile of the texture atlas is, worked out from the alpha channel of atlas.png
OPAQUE = 0 # every pixel is solid
CUTOUT = 1 # every pixel is either solid or completely gone (leaves, fences, ...), drawn like opaque with the gone pixels cut out
TRANSLUCENT = 2 # some pixels are partly see-through (glass, water, ...), drawn in a separate pass that blends them with what is behind

def tile_opacities(path, tile_size, atlas_size):
    # returns {(col, row): OPAQUE / CUTOUT / TRANSLUCENT} for every tile of the atlas; a tile that isn't in it is opaque
    img = pygame.image.load(path)

    if not img.get_flags() & pygame.SRCALPHA: # an image without an alpha channel is solid everywhere
        return {}

    alpha = pygame.surfarray.array_alpha(img) # [x][y], y = 0 is the top of the png
    count = atlas_size // tile_size
    opacities = {}

    for row in range(count):
        for col in range(count):
            # the atlas is uploaded upside down (see load_texture in r.py), so row 0 is the bottom row of the png
            y = (count - 1 - row) * tile_size
            tile = alpha[col * tile_size:(col + 1) * tile_size, y:y + tile_size]

            if tile.min() == 255:
                continue # opaque, the default

            if np.isin(tile, (0, 255)).all():
                opacities[(col, row)] = CUTOUT
            else:
                opacities[(col, row)] = TRANSLUCENT

    return opacities
