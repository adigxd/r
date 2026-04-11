import numpy as np
from OpenGL.GL import *
import os
import json
import random

# ./
import buf
import dbg

from dotenv import load_dotenv
load_dotenv()

# map*.py
_SED               = int(os.getenv('SED'))
_BLC_SIZ           = int(os.getenv('BLC_SIZ'))
_TEX_SIZ           = int(os.getenv('TEX_SIZ'))
_DIR_MAP           = os.getenv('DIR_MAP')
_MAP               = os.getenv('MAP')

# format: "BLK_TYP": {"top": (col, row), "sid": (col, row), "bot": (col, row)} or {"all": (col, row)} (if all faces of the block use the same texture)
# "AIR" is typically used in map files to represent empty space and is not included here since it doesn't correspond to an actual block type that needs vertex data
#       it is treated the same way an invalid block type would be (ignored and not added to the vertex array)
_BLC_TYP_ARR = {
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
    "LOG_MAPLE": {"top": (0, 6), "sid": (0, 5), "bot": (0, 6)},
    "LOG_MAPLE_FULL": {"all": (0, 5)},
    "LOG_MAPLE_NAKED": {"all": (0, 8)},
    "LOG_PINE": {"top": (1, 6), "sid": (1, 5), "bot": (1, 6)},
    "LOG_PINE_FULL": {"all": (1, 5)},
    "LOG_PINE_NAKED": {"all": (1, 8)},
    "LOG_WINDSWEPT": {"top": (2, 6), "sid": (2, 5), "bot": (2, 6)},
    "LOG_WINDSWEPT_FULL": {"all": (2, 5)},
    "LOG_WINDSWEPT_NAKED": {"all": (2, 8)},
    "LOG_REDWOOD": {"top": (3, 6), "sid": (3, 5), "bot": (3, 6)},
    "LOG_REDWOOD_FULL": {"all": (3, 5)},
    "LOG_REDWOOD_NAKED": {"all": (3, 8)},
    "LEAF_MAPLE": {"all": (0, 7)},
    "LEAF_PINE": {"all": (1, 7)},
    "LEAF_WINDSWEPT": {"all": (2, 7)},
    "LEAF_REDWOOD": {"all": (3, 7)},
    "STONE_DEBUG": {"top": (6, 0), "sid": (0, 0), "bot": (0, 0)},
}

class __MAP__:
    def __init__(self, sed=_SED, blc_siz=_BLC_SIZ, tex_siz=_TEX_SIZ):
        self.sed = sed
        self.blc_siz = blc_siz
        self.tex_siz = tex_siz
        self.blc_arr = {} # (x, y, z) : blc_typ
        self.new = True # if the map is dirty (has been modified since last render)
        self.vao_blc = None
        self.vbo_blc = None
        self.vtx_cnt_blc = 0
    
    def _BLC_SET(self, x, y, z, blc_typ):
        self.blc_arr[(x, y, z)] = blc_typ
        self.new = True # mark the map as dirty since we've modified it
    
    def _BLC_GET(self, x, y, z):
        return self.blc_arr.get((x, y, z), None)
    
    def _BLC_SEE_YES(self, x, y, z):
        # check if a block has any exposed faces (not surrounded)
        # for now, all blocks are visible (no occlusion culling)

        return self._BLC_GET(x, y, z) is not None
    
    def _TEX_RND(self, loc):
        # val can be a single (col, row) tuple or a list of tuples for random selection
        if isinstance(loc, list):
            return self._TEX_LOC(*random.choice(loc))
        return self._TEX_LOC(*loc)

    def _TEX_LOC(self, col, row):
        # get texture coordinates for a block located at (col, row) in the texture atlas
        u0 = (col * _BLC_SIZ) / _TEX_SIZ
        v0 = (row * _BLC_SIZ) / _TEX_SIZ
        u1 = ((col + 1) * _BLC_SIZ) / _TEX_SIZ
        v1 = ((row + 1) * _BLC_SIZ) / _TEX_SIZ
        
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    
    def _VTX_ARR_ADD(self, x, y, z, blc_typ):
        # generate vertex data for a block at (x, y, z) of type blc_typ
        if blc_typ == 'AIR' or blc_typ not in _BLC_TYP_ARR:
            return []
        
        blc_map = _BLC_TYP_ARR[blc_typ]
        blc = {
            "FNT": blc_map.get("all", blc_map.get("sid")),
            "BAC": blc_map.get("all", blc_map.get("sid")),
            "LFT": blc_map.get("all", blc_map.get("sid")),
            "RGT": blc_map.get("all", blc_map.get("sid")),
            "TOP": blc_map.get("all", blc_map.get("top")),
            "bot": blc_map.get("all", blc_map.get("bot"))
        }

        vtx_arr = []

        blc_pos_fnt = [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
        blc_pos_bac = [(x + 1, y, z), (x, y, z), (x, y + 1, z), (x + 1, y + 1, z)]
        blc_pos_lft = [(x, y, z), (x, y, z + 1), (x, y + 1, z + 1), (x, y + 1, z)]
        blc_pos_rgt = [(x + 1, y, z + 1), (x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1)]
        blc_pos_top = [(x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z), (x, y + 1, z)]
        blc_pos_bot = [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]

        blc_tex_loc_fnt = self._TEX_RND(blc["FNT"])
        blc_tex_loc_bac = self._TEX_RND(blc["BAC"])
        blc_tex_loc_lft = self._TEX_RND(blc["LFT"])
        blc_tex_loc_rgt = self._TEX_RND(blc["RGT"])
        blc_tex_loc_top = self._TEX_RND(blc["TOP"])
        blc_tex_loc_bot = self._TEX_RND(blc["bot"])

        blc_fnt_nml = (0, 0, 1)
        blc_bac_nml = (0, 0, -1)
        blc_lft_nml = (-1, 0, 0)
        blc_rgt_nml = (1, 0, 0)
        blc_top_nml = (0, 1, 0)
        blc_bot_nml = (0, -1, 0)

        def add_fac(pos, tex_loc, nml):
            # add a face to the vertex array (two triangles)
            for i in [0, 1, 2]:
                vtx_arr.extend([*pos[i], *nml, *tex_loc[i]])
            for i in [0, 2, 3]:
                vtx_arr.extend([*pos[i], *nml, *tex_loc[i]])

        add_fac(blc_pos_fnt, blc_tex_loc_fnt, blc_fnt_nml)
        add_fac(blc_pos_bac, blc_tex_loc_bac, blc_bac_nml)
        add_fac(blc_pos_lft, blc_tex_loc_lft, blc_lft_nml)
        add_fac(blc_pos_rgt, blc_tex_loc_rgt, blc_rgt_nml)
        add_fac(blc_pos_top, blc_tex_loc_top, blc_top_nml)
        add_fac(blc_pos_bot, blc_tex_loc_bot, blc_bot_nml)
        
        return vtx_arr
    
    def _VTX_ARR_NEW(self):
        # generate vertex data for the entire map
        vtx_arr = []
        vtx_del_arr = []

        for (x, y, z), blc_typ in self.blc_arr.items():
            result = self._VTX_ARR_ADD(x, y, z, blc_typ)
            if result:
                vtx_arr.extend(result)
            else:
                vtx_del_arr.append((x, y, z))

        for key in vtx_del_arr:
            del self.blc_arr[key]

        # don't try to draw if there's nothing to draw
        if not vtx_arr:
            self.vao_blc = None
            self.vbo_blc = None
            self.vtx_cnt_blc = 0

            return

        vtx_dat = np.array(vtx_arr, dtype=np.float32)
        self.vao_blc, self.vbo_blc = buf._BUF_BLC(vtx_dat)
        self.vtx_cnt_blc = len(vtx_arr) // 8 # 8 floats per vertex (position, normal, texcoord)
        self.new = False # mark the map as clean since we've just updated the vertex data
    
    def _BLC_TYP_RND(self, blc_typ_arr):
        # blc_typ_arr can be a list (equal chance) or a dict {"TYPE": weight} for weighted selection
        if isinstance(blc_typ_arr, dict):
            return random.choices(list(blc_typ_arr.keys()), weights=list(blc_typ_arr.values()), k=1)[0]

        return random.choice(blc_typ_arr)

    def _MAP_VoxelFunction(self, x, y, z, blc_typ_arr):
        self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))
    
    def _MAP_CubeFunction(self, x_min, x_max, y_min, y_max, z_min, z_max, blc_typ_arr):
        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                for z in range(z_min, z_max):
                    self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))
    
    def _MAP_CubeFunctionSimple(self, cx, cy, cz, r, blc_typ_arr):
        r_haf = r // 2
        self._MAP_CubeFunction(cx - r_haf, cx + r_haf, cy - r_haf, cy + r_haf, cz - r_haf, cz + r_haf, blc_typ_arr)

    def _MAP_SphereFunction(self, cx, cy, cz, r, blc_typ_arr):
        r_sqr = r * r

        for x in range(int(cx - r), int(cx + r)):
            for y in range(int(cy - r), int(cy + r)):
                for z in range(int(cz - r), int(cz + r)):
                    dx = x - cx
                    dy = y - cy
                    dz = z - cz
                    if dx * dx + dy * dy + dz * dz < r_sqr:
                        self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))

    def _MAP_CylinderFunction(self, cx, cy, cz, r, h, axs, blc_typ_arr):
        # axs: 0 = vertical, 1 = horizontal along x, 2 = horizontal along z

        r_sqr = r * r

        if axs == 0: # vertical
            for x in range(int(cx - r), int(cx + r)):
                for y in range(int(cy), int(cy + h)):
                    for z in range(int(cz - r), int(cz + r)):
                        dx = x - cx
                        dz = z - cz
                        if dx * dx + dz * dz < r_sqr:
                            self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))
        elif axs == 1: # horizontal along x
            for x in range(int(cx), int(cx + h)):
                for y in range(int(cy - r), int(cy + r)):
                    for z in range(int(cz - r), int(cz + r)):
                        dy = y - cy
                        dz = z - cz
                        if dy * dy + dz * dz < r_sqr:
                            self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))
        elif axs == 2: # horizontal along z
            for x in range(int(cx - r), int(cx + r)):
                for y in range(int(cy - r), int(cy + r)):
                    for z in range(int(cz), int(cz + h)):
                        dx = x - cx
                        dy = y - cy
                        if dx * dx + dy * dy < r_sqr:
                            self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))

    def _MAP_ConeFunction(self, cx, cy, cz, r, h, axs, flp, blc_typ_arr):
        # axs: 0 = vertical, 1 = horizontal along x, 2 = horizontal along z
        # flp: 0 or 1; whether the cone is flipped (pointing down/left/back instead of up/right/front)

        r_sqr = r * r

        if axs == 0: # vertical
            for x in range(int(cx - r), int(cx + r)):
                for y in range(int(cy), int(cy + h)):
                    for z in range(int(cz - r), int(cz + r)):
                        dy = y - cy
                        dx = x - cx
                        dz = z - cz
                        t = (dy / h) if flp == 1 else 1.0 - (dy / h)
                        if dy >= 0 and dx * dx + dz * dz < r_sqr * t * t:
                            self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))
        elif axs == 1: # horizontal along x
            for x in range(int(cx), int(cx + h)):
                for y in range(int(cy - r), int(cy + r)):
                    for z in range(int(cz - r), int(cz + r)):
                        dx = x - cx
                        dy = y - cy
                        dz = z - cz
                        t = (dx / h) if flp == 1 else 1.0 - (dx / h)
                        if dx >= 0 and dy * dy + dz * dz < r_sqr * t * t:
                            self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))
        elif axs == 2: # horizontal along z
            for x in range(int(cx - r), int(cx + r)):
                for y in range(int(cy - r), int(cy + r)):
                    for z in range(int(cz), int(cz + h)):
                        dz = z - cz
                        dx = x - cx
                        dy = y - cy
                        t = (dz / h) if flp == 1 else 1.0 - (dz / h)
                        if dz >= 0 and dx * dx + dy * dy < r_sqr * t * t:
                            self._BLC_SET(x, y, z, self._BLC_TYP_RND(blc_typ_arr))

    def _MAP_TreeFunction(self, x, y, z, h_pre, typ):
        if typ == "MAPLE":
            h = max(6, h_pre) # minimum maple height of 6
            w = 0.5

            self._MAP_CubeFunctionSimple(x, y + h, z, (h * 3) // 4, {"LEAF_MAPLE": 1, "AIR": 4})
            self._MAP_SphereFunction(x, y + h, z, h // 2, {"LEAF_MAPLE": 1, "AIR": 1})
            self._MAP_CylinderFunction(x, y, z, w, h, 0, ["LOG_MAPLE"]) # trunk
            self._MAP_VoxelFunction(x, y + h, z, ["LOG_MAPLE_FULL"]) # tip
        if typ == "PINE":
            h = max(16, h_pre) # minimum pine height of 16
            w = 0.5

            self._MAP_ConeFunction(x, y + h // 4, z, h // 4, h // 8, 0, 1, {"LEAF_PINE": 1, "AIR": 3})
            self._MAP_ConeFunction(x, y + ((h * 7) // 8), z, h // 8, h // 3, 0, 0, {"LEAF_PINE": 1, "AIR": 1})
            self._MAP_ConeFunction(x, y + ((h * 3) // 4), z, h // 7, h // 3, 0, 0, {"LEAF_PINE": 1, "AIR": 1})
            self._MAP_ConeFunction(x, y + ((h * 5) // 8), z, h // 6, h // 3, 0, 0, {"LEAF_PINE": 1, "AIR": 2})
            self._MAP_ConeFunction(x, y + (h // 2), z, h // 5, h // 3, 0, 0, {"LEAF_PINE": 1, "AIR": 2})
            self._MAP_ConeFunction(x, y + ((h * 3) // 8), z, h // 4, h // 3, 0, 0, {"LEAF_PINE": 1, "AIR": 3})
            self._MAP_CylinderFunction(x, y, z, w, h, 0, ["LOG_PINE"]) # trunk
            self._MAP_VoxelFunction(x, y + h, z, ["LOG_PINE_FULL"]) # tip
        if typ == "REDWOOD":
            h = max(32, h_pre) # minimum redwood height of 32
            w = max(1, (h // 32))

            self._MAP_ConeFunction(x, y + h // 4, z, h // 4, h // 8, 0, 1, {"LEAF_REDWOOD": 1, "AIR": 3})
            self._MAP_ConeFunction(x, y + ((h * 7) // 8), z, h // 8, h // 3, 0, 0, {"LEAF_REDWOOD": 1, "AIR": 1})
            self._MAP_ConeFunction(x, y + ((h * 3) // 4), z, h // 7, h // 3, 0, 0, {"LEAF_REDWOOD": 1, "AIR": 1})
            self._MAP_ConeFunction(x, y + ((h * 5) // 8), z, h // 6, h // 3, 0, 0, {"LEAF_REDWOOD": 1, "AIR": 2})
            self._MAP_ConeFunction(x, y + (h // 2), z, h // 5, h // 3, 0, 0, {"LEAF_REDWOOD": 1, "AIR": 2})
            self._MAP_ConeFunction(x, y + ((h * 3) // 8), z, h // 4, h // 3, 0, 0, {"LEAF_REDWOOD": 1, "AIR": 3})
            self._MAP_CylinderFunction(x, y, z, w, h, 0, ["LOG_REDWOOD"]) # trunk
            self._MAP_CylinderFunction(x, y + h, z, w, 1, 0, ["LOG_REDWOOD_FULL"]) # tip
        else:
            pass


    def _MAP_SET(self):
        random.seed(self.sed)

        self.blc_arr = {}
        self.new = True

        if not _DIR_MAP or not _MAP:
            dbg._DBG(dbg._TAG_ERR, ['Map Error'], ['DIR_MAP and MAP must be set'])
            self._VTX_ARR_NEW()

            return
        
        map_nam = _MAP if _MAP.lower().endswith('.json') else f'{_MAP}.json'
        map_pth = os.path.join(_DIR_MAP, map_nam)

        dbg._DBG(dbg._TAG_CFG, ['Map File'], [map_pth])

        try:
            with open(map_pth, 'r', encoding='utf-8') as f:
                map_dat = json.load(f)
        except FileNotFoundError:
            dbg._DBG(dbg._TAG_ERR, ['Map Error File Missing', 'Path'], ['...', map_pth])
            self._VTX_ARR_NEW()

            return
        except json.JSONDecodeError as E:
            dbg._DBG(dbg._TAG_ERR, ['Map Error JSON Invalid', 'Path', 'Error'], ['...', map_pth, E])
            self._VTX_ARR_NEW()

            return
        except Exception as E:
            dbg._DBG(dbg._TAG_ERR, ['Map Error Load Error', 'Path', 'Error'], ['...', map_pth, E])
            self._VTX_ARR_NEW()

            return

        map_obj = map_dat.get('MAP', {})

        for vxl in map_obj.get('VOXELS', []):
            self._MAP_VoxelFunction(vxl['x'], vxl['y'], vxl['z'], vxl['blc_typ_arr'])

        for cub in map_obj.get('CUBES', []):
            self._MAP_CubeFunction(
                cub['x_min'], cub['x_max'],
                cub['y_min'], cub['y_max'],
                cub['z_min'], cub['z_max'],
                cub['blc_typ_arr']
            )

        for sfr in map_obj.get('SPHERES', []):
            self._MAP_SphereFunction(
                sfr['x'], sfr['y'], sfr['z'], sfr['r'], sfr['blc_typ_arr']
            )

        for cyl in map_obj.get('CYLINDERS', []):
            self._MAP_CylinderFunction(
                cyl['x'], cyl['y'], cyl['z'], cyl['r'], cyl['h'], cyl['axs'], cyl['blc_typ_arr']
            )

        for con in map_obj.get('CONES', []):
            self._MAP_ConeFunction(
                con['x'], con['y'], con['z'], con['r'], con['h'], con['axs'], con['flp'], con['blc_typ_arr']
            )

        for tre in map_obj.get('TREES', []):
            self._MAP_TreeFunction(
                tre['x'], tre['y'], tre['z'], tre['h'], tre['typ']
            )

        self._VTX_ARR_NEW()

    def _DBG_MAP_SET(self):
        self._MAP_SET()
    
    def _MAP_GET(self):
        if self.new:
            self._VTX_ARR_NEW()
        
        return self.vao_blc, self.vtx_cnt_blc