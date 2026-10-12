import json
import os
from types import SimpleNamespace

# ./
import log

# directory the map files live in; every map file carries its own settings ("config") next to its blocks ("world")
MAPS_DIR = './maps'

def vec3(val):
    vec = tuple(map(float, val))

    if len(vec) != 3:
        raise ValueError('needs exactly 3 numbers')

    return vec

def flag(val):
    if not isinstance(val, bool):
        raise ValueError('needs true or false')

    return val

# every setting a map file's "config" has to define, and the type it is cast to
SETTINGS = {
    # light
    'light_pos': vec3, # position of light
    'light_radius': float, # radius of light
    'light_intensity': float, # intensity of light
    'light_color': vec3, # color of light

    # world.py
    'seed': int, # seed for map generation
    'tile_size': int, # size of each block texture (tile) in the texture atlas
    'atlas_size': int, # size of the texture atlas

    # r.py
    'threads': int, # thread count for chunks
    'width': int, # resolution width
    'height': int, # resolution height
    'max_fps': int, # frame rate cap
    'fov': float, # field of view
    'near_clip': float, # minimum view distance
    'far_clip': float, # maximum view distance
    'mouse_sensitivity': float, # mouse sensitivity
    'line_width': float, # glLineWidth
    'background_color': vec3, # background color
    'start_pos': vec3, # initial position
    'speed': float, # speed
    'sprint_multiplier': float, # speed multiplier when sprinting
    'player_width': float, # player width
    'player_height': float, # player height
    'gravity': float, # downward acceleration
    'jump_speed': float, # upward speed at the start of a jump

    # r.py / texture paths
    'atlas_path': str, # texture atlas for blocks

    # r.py / shader paths
    'block_vertex_shader': str, # vertex shader
    'block_fragment_shader': str, # fragment shader (with lighting)
    'post_vertex_shader': str, # post-processing vertex shader
    'post_default_shader': str, # post-processing fragment shader (default)
    'post_edge_shader': str, # post-processing fragment shader (edge detect)
    'post_dither_shader': str, # post-processing fragment shader (dither)

    # r.py / general paths
    'screenshot_dir': str, # screenshots

    # r.py / music
    'music_path': str, # music file (has to be a file, not a folder)
    'mixer_frequency': int, # sample rate for audio playback
    'mixer_size': int, # sample size in bits (negative means signed samples)
    'mixer_channels': int, # stereo playback
    'mixer_buffer': int, # mixer buffer size in samples
    'music_volume': float, # master music volume (0.0 to 1.0)

    # r.py / debug
    'fly': flag, # true: fly around with no physics (Space / Left Shift for up / down); false: gravity and collisions
}

def load(map_name):
    # loads a map file from MAPS_DIR and returns (settings, world_data): its settings ("config", as an object with one attribute per key above) and its blocks ("world")
    # prints what went wrong and returns (None, None) if the file can't be used
    map_name = map_name if map_name.lower().endswith('.json') else f'{map_name}.json'
    map_path = os.path.join(MAPS_DIR, map_name)

    try:
        with open(map_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
    except FileNotFoundError:
        log.error('Map file missing', path=map_path)

        return None, None
    except json.JSONDecodeError as e:
        log.error('Map file is not valid JSON', path=map_path, error=e)

        return None, None
    except Exception as e:
        log.error('Map file could not be loaded', path=map_path, error=e)

        return None, None

    if not isinstance(map_data, dict) or not isinstance(map_data.get('config'), dict):
        log.error('Map file has no "config" object', path=map_path)

        return None, None

    config_data = map_data['config']
    settings = {}
    missing = [] # keys the map file doesn't define
    invalid = [] # keys whose value can't be cast

    for key, cast in SETTINGS.items():
        if key not in config_data:
            missing.append(key)

            continue

        try:
            settings[key] = cast(config_data[key])
        except (TypeError, ValueError) as e:
            invalid.append(f'{key} ({e})')

    if missing or invalid:
        if missing:
            log.error('Map file is missing settings', path=map_path, keys=', '.join(missing))
        if invalid:
            log.error('Map file has invalid settings', path=map_path, keys=', '.join(invalid))

        return None, None

    return SimpleNamespace(**settings), map_data.get('world', {})
