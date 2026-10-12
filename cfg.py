import json
import os
from types import SimpleNamespace

# ./
import dbg

# directory the map files live in; every map file carries its own settings ("CONFIG") next to its blocks ("MAP")
_DIR_MAP = './DIR-Maps'

def _VEC3(val):
    vec = tuple(map(float, val))

    if len(vec) != 3:
        raise ValueError('needs exactly 3 numbers')

    return vec

# every setting a map file's "CONFIG" has to define, and the type it is cast to
_CFG_TYP_ARR = {
    # light
    'LIT_POS': _VEC3, # position of light
    'LIT_RAD': float, # radius of light
    'LIT_INT': float, # intensity of light
    'LIT_COL': _VEC3, # color of light

    # map_.py
    'SED': int, # seed for map generation
    'BLC_SIZ': int, # size of each block texture in the texture atlas
    'TEX_SIZ': int, # size of the texture atlas

    # r.py
    'THD_CNT': int, # thread count for chunks
    'RES_X': int, # resolution width
    'RES_Y': int, # resolution height
    'TIC': int, # ticks per second
    'FOV': float, # field of view
    'SEE_MIN': float, # minimum view distance
    'SEE_MAX': float, # maximum view distance
    'SEN': float, # mouse sensitivity
    'LIN_WID': float, # glLineWidth
    'COL_BKG': _VEC3, # background color
    'POS': _VEC3, # initial position
    'SPD': float, # speed
    'SPD_MAG': float, # speed multiplier when sprinting
    'WID': float, # player width
    'HIT': float, # player height
    'ACC_D': float, # deceleration
    'JMP_MAG': float, # jump magnitude

    # r.py / texture paths
    'PTH_TEX': str, # texture atlas for blocks

    # r.py / shader paths
    'PTH_SHA_V': str, # vertex shader
    'PTH_SHA_F': str, # fragment shader (with lighting)
    'PTH_SHA_V_PST': str, # post-processing vertex shader
    'PTH_SHA_F_PST_DEF': str, # post-processing fragment shader (default)
    'PTH_SHA_F_PST_0': str, # post-processing fragment shader (edge detect)
    'PTH_SHA_F_PST_1': str, # post-processing fragment shader (dither)

    # r.py / general paths
    'DIR_SSM': str, # screenshots

    # r.py / music
    'PTH_MSC': str, # music file (has to be a file, not a folder)
    'MIX_FRQ': int, # sample rate for audio playback
    'MIX_SIZ': int, # sample size in bits (negative means signed samples)
    'MIX_CNL_CNT': int, # stereo playback
    'MIX_BUF': int, # mixer buffer size in samples
    'MIX_VOL': float, # master music volume (0.0 to 1.0)

    # r.py / debug
    'DBG_KIN': int, # debug kinematics mode (0: fly, no physics, 1: normal)
}

def _CFG_LOAD(map_nam):
    # loads a map file from _DIR_MAP and returns (cfg_dat, map_obj): its settings ("CONFIG", as an object with one attribute per key above) and its blocks ("MAP")
    # prints what went wrong and returns (None, None) if the file can't be used
    map_nam = map_nam if map_nam.lower().endswith('.json') else f'{map_nam}.json'
    map_pth = os.path.join(_DIR_MAP, map_nam)

    try:
        with open(map_pth, 'r', encoding='utf-8') as f:
            map_dat = json.load(f)
    except FileNotFoundError:
        dbg._DBG(dbg._TAG_ERR, ['Map Error File Missing', 'Path'], ['...', map_pth])

        return None, None
    except json.JSONDecodeError as E:
        dbg._DBG(dbg._TAG_ERR, ['Map Error JSON Invalid', 'Path', 'Error'], ['...', map_pth, E])

        return None, None
    except Exception as E:
        dbg._DBG(dbg._TAG_ERR, ['Map Error Load Error', 'Path', 'Error'], ['...', map_pth, E])

        return None, None

    if not isinstance(map_dat, dict) or not isinstance(map_dat.get('CONFIG'), dict):
        dbg._DBG(dbg._TAG_ERR, ['Map Error CONFIG Missing', 'Path'], ['...', map_pth])

        return None, None

    cfg_obj = map_dat['CONFIG']
    cfg_dat = {}
    key_mis_arr = [] # keys the map file doesn't define
    key_bad_arr = [] # keys whose value can't be cast

    for key, cst in _CFG_TYP_ARR.items():
        if key not in cfg_obj:
            key_mis_arr.append(key)

            continue

        try:
            cfg_dat[key] = cst(cfg_obj[key])
        except (TypeError, ValueError) as E:
            key_bad_arr.append(f'{key} ({E})')

    if key_mis_arr or key_bad_arr:
        if key_mis_arr:
            dbg._DBG(dbg._TAG_ERR, ['Map Error CONFIG Keys Missing', 'Path', 'Keys'], ['...', map_pth, ', '.join(key_mis_arr)])
        if key_bad_arr:
            dbg._DBG(dbg._TAG_ERR, ['Map Error CONFIG Values Invalid', 'Path', 'Keys'], ['...', map_pth, ', '.join(key_bad_arr)])

        return None, None

    return SimpleNamespace(**cfg_dat), map_dat.get('MAP', {})
