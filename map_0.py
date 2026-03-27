import numpy as np
from OpenGL.GL import *
import os

# ./
import buf
import dbg

from dotenv import load_dotenv
load_dotenv()

# map*.py
_SED               = int(os.getenv('SED'))
_BLC_SIZ           = int(os.getenv('BLC_SIZ'))
_TEX_SIZ           = int(os.getenv('TEX_SIZ'))

# format: "BLK_TYP": {"top": (col, row), "sid": (col, row), "btm": (col, row)} or {"all": (col, row)} (if all faces of the block use the same texture)
_BLC_TYP_ARR = {
    "STONE": {"all": (0, 0)},
    "STONE_SOLID": {"all": (1, 0)},
    "STONE_BRICK": {"all": (2, 0)},
    "STONE_DEBUG": {"top": (2, 0), "sid": (0, 0), "btm": (0, 0)},
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

        return self.get_block(x, y, z) is not None
    
    def _TEX_LOC(self, col, row):
        # get texture coordinates for a block located at (col, row) in the texture atlas
        u0 = (col * _BLC_SIZ) / _TEX_SIZ
        v0 = (row * _BLC_SIZ) / _TEX_SIZ
        u1 = ((col + 1) * _BLC_SIZ) / _TEX_SIZ
        v1 = ((row + 1) * _BLC_SIZ) / _TEX_SIZ
        
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    
    def _VTX_ARR_ADD(self, x, y, z, blc_typ):
        # generate vertex data for a block at (x, y, z) of type blc_typ
        if blc_typ not in _BLC_TYP_ARR:
            dbg.__DBG(dbg._TAG_ERR, ["block type"], ['...'])

            return []
        
        blc_map = _BLC_TYP_ARR[blc_typ]
        blc = {
            "FNT": blc_map.get("all", blc_map.get("sid")),
            "BAC": blc_map.get("all", blc_map.get("sid")),
            "LFT": blc_map.get("all", blc_map.get("sid")),
            "RGT": blc_map.get("all", blc_map.get("sid")),
            "TOP": blc_map.get("all", blc_map.get("top")),
            "BTM": blc_map.get("all", blc_map.get("btm"))
        }

        vtx_arr = []

        blc_pos_fnt = [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
        blc_pos_bac = [(x + 1, y, z), (x, y, z), (x, y + 1, z), (x + 1, y + 1, z)]
        blc_pos_lft = [(x, y, z), (x, y, z + 1), (x, y + 1, z + 1), (x, y + 1, z)]
        blc_pos_rgt = [(x + 1, y, z + 1), (x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1)]
        blc_pos_top = [(x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z), (x, y + 1, z)]
        blc_pos_btm = [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]

        blc_tex_loc_fnt = self._TEX_LOC(*blc["FNT"])
        blc_tex_loc_bac = self._TEX_LOC(*blc["BAC"])
        blc_tex_loc_lft = self._TEX_LOC(*blc["LFT"])
        blc_tex_loc_rgt = self._TEX_LOC(*blc["RGT"])
        blc_tex_loc_top = self._TEX_LOC(*blc["TOP"])
        blc_tex_loc_btm = self._TEX_LOC(*blc["BTM"])

        blc_fnt_nml = (0, 0, 1)
        blc_bac_nml = (0, 0, -1)
        blc_lft_nml = (-1, 0, 0)
        blc_rgt_nml = (1, 0, 0)
        blc_top_nml = (0, 1, 0)
        blc_btm_nml = (0, -1, 0)

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
        add_fac(blc_pos_btm, blc_tex_loc_btm, blc_btm_nml)
        
        return vtx_arr
    
    def _VTX_ARR_NEW(self):
        # generate vertex data for the entire map
        vtx_arr = []

        for (x, y, z), blc_typ in self.blc_arr.items():
            vtx_arr.extend(self._VTX_ARR_ADD(x, y, z, blc_typ))

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
    
    def _DBG_MAP_SET(self):
        for x in range(-25, 125):
            for y in range(0, 100):
                self._BLC_SET(x, y, -50, "STONE_BRICK")

        for x in range(-25, 125):
            for y in range(0, 75):
                self._BLC_SET(x, y, 50, "STONE_BRICK")

        for x in range(-25, 225):
            for z in range(-50, 50):
                self._BLC_SET(x, 0, z, "STONE_SOLID")

        for x in range(-25, 125):
            for z in range(-50, 50):
                self._BLC_SET(x, 100, z, "STONE_SOLID")

        self._VTX_ARR_NEW()
    
    def _MAP_GET(self):
        if self.new:
            self._VTX_ARR_NEW()
        
        return self.vao_blc, self.vtx_cnt_blc