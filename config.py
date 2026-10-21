import json
import os
from types import SimpleNamespace

from dotenv import dotenv_values

# ./
import log
import rend

# directory the map files live in
MAPS_DIR = './maps'

# settings that are the same for every map; later files override earlier ones (.env.pre is the tracked default, .env is optional and only yours)
ENV_FILES = ['./.env.pre', './.env']

# the size of the window when it isn't fullscreen is kept between these (fullscreen ignores them: it uses the size of the screen)
WINDOW_MIN = (1280, 720)
WINDOW_MAX = (3840, 2160)

# ------

def vec3(val):
    vec = tuple(map(float, val))

    if len(vec) != 3:
        raise ValueError('needs exactly 3 numbers')

    return vec

def flag(val):
    if not isinstance(val, bool):
        raise ValueError('needs true or false')

    return val

def positive(val):
    val = float(val)

    if val <= 0:
        raise ValueError('needs a number above 0')

    return val

def positive_int(val):
    val = int(val)

    if val <= 0:
        raise ValueError('needs a whole number above 0')

    return val

def unit(val):
    val = float(val)

    if not 0 <= val <= 1:
        raise ValueError('needs a number from 0 to 1')

    return val

def non_negative(val):
    val = float(val)

    if val < 0:
        raise ValueError('needs a number of 0 or more')

    return val

def at_least_one(val):
    val = float(val)

    if val < 1:
        raise ValueError('needs a number of 1 or more')

    return val

def half_or_less(val):
    val = float(val)

    if not 0 <= val <= 0.5:
        raise ValueError('needs a number from 0 to 0.5')

    return val

def fraction(val):
    val = float(val)

    if not 0 < val <= 1:
        raise ValueError('needs a number above 0, up to 1')

    return val

def power_of_two(val):
    val = int(val)

    if val < 4 or val & (val - 1):
        raise ValueError('needs a power of 2 (4, 8, 16, 32, ...)')

    return val

def optional_text(val):
    if val is None: # "music": null is the same as no "music"
        return None

    if not isinstance(val, str):
        raise ValueError('needs text')

    return val

def env_flag(val):
    word = str(val).strip().lower()

    if word in ('true', '1', 'yes', 'on'):
        return True
    if word in ('false', '0', 'no', 'off'):
        return False

    raise ValueError('needs true or false')

def env_path_list(val):
    paths = [path.strip() for path in str(val).split(',') if path.strip()]

    if not paths:
        raise ValueError('needs at least one path')

    return paths

FALLOFFS = {'linear': 0, 'inverse_square': 1} # how a light fades with distance; the number is what the shader gets

def falloff(val):
    if val not in FALLOFFS:
        raise ValueError('needs "linear" or "inverse_square"')

    return FALLOFFS[val]

def parse(raw, required, optional, where, errors):
    # casts the values of the dict raw; required is {key: cast}, optional is {key: (cast, default)}
    # anything wrong is added to errors as text instead of raising, so everything wrong gets reported at once
    values = {}

    for key, cast in required.items():
        if key not in raw:
            errors.append(f'{where}{key} (missing)')

            continue

        try:
            values[key] = cast(raw[key])
        except (TypeError, ValueError) as e:
            errors.append(f'{where}{key} ({e})')

    for key, (cast, default) in optional.items():
        if key not in raw:
            values[key] = cast(default) # defaults go through the same cast, so e.g. 'linear' becomes the number the shader wants

            continue

        try:
            values[key] = cast(raw[key])
        except (TypeError, ValueError) as e:
            errors.append(f'{where}{key} ({e})')

    for key in raw:
        if key not in required and key not in optional:
            errors.append(f'{where}{key} (unknown setting)')

    return values

# ------

# settings from .env.pre / .env (the names there are uppercase; in the code they are settings.<lowercase>), explained in .env.pre
ENV_SETTINGS = {
    'WIDTH': int,
    'HEIGHT': int,
    'FULLSCREEN': env_flag,
    'MAX_FPS': int,
    'TICK_RATE': positive_int,
    'MAX_FRAME_TIME': positive,
    'COLLISION_STEP': fraction,
    'MAX_LIGHTS': positive_int,
    'LIGHT_FADE_TIME': non_negative,
    'LIGHT_FADE_SHARE': half_or_less,
    'LIGHT_STICKINESS': at_least_one,
    'LIGHT_CELL_SIZE': positive_int,
    'REND_MAX_BLOCKS': positive_int,
    'REND_UNDO_BLOCKS': positive_int,
    'CHAT_FONT': str,
    'CHAT_FONT_SIZE': positive_int,
    'CHAT_LINES': positive_int,
    'CHAT_HISTORY': positive_int,
    'CHAT_FADE_TIME': positive,
    'CHAT_WIDTH': fraction,
    'CHUNK_SIZE': power_of_two,
    'GLASS_SORT_DISTANCE': positive,
    'LOADING_BAR_FPS': positive_int,
    'LOADING_BAR_WIDTH': fraction,
    'FOV': float,
    'NEAR_CLIP': float,
    'FAR_CLIP': float,
    'MOUSE_SENSITIVITY': float,
    'LINE_WIDTH': float,

    'ATLAS_PATH': str,
    'TILE_SIZE': int,
    'ATLAS_SIZE': int,
    'MIPMAPS': env_flag,

    'BLOCK_VERTEX_SHADER': str,
    'BLOCK_FRAGMENT_SHADER': str,
    'POST_VERTEX_SHADER': str,
    'UI_VERTEX_SHADER': str,
    'UI_FRAGMENT_SHADER': str,
    'LINE_VERTEX_SHADER': str,
    'LINE_FRAGMENT_SHADER': str,
    'POST_FRAGMENT_SHADERS': env_path_list,

    'SCREENSHOT_DIR': str,
    'MUSIC_DIR': str,

    'MIXER_FREQUENCY': int,
    'MIXER_SIZE': int,
    'MIXER_CHANNELS': int,
    'MIXER_BUFFER': int,
    'MUSIC_VOLUME': float,
}

# settings a map file's "config" has to define
MAP_SETTINGS = {
    'seed': int, # seed for map generation
    'start_pos': vec3, # initial position
    'background_color': vec3, # background color
    'fly': flag, # true: fly around with no physics (Space / Left Shift for up / down); false: gravity and collisions
    'gravity': float, # downward acceleration
    'jump_speed': float, # upward speed at the start of a jump
    'speed': float, # speed
    'sprint_multiplier': float, # speed multiplier when sprinting
    'player_width': float, # player width
    'player_height': float, # player height
}

# settings a map file's "config" can define
MAP_OPTIONAL_SETTINGS = {
    'music': (optional_text, None), # music file in MUSIC_DIR (e.g. "1.mp3"); no "music" means the map has no music
}

# a map file's "lights" is a list of any number of these (every frame the game picks the ones that can light something visible, see lights.py)
LIGHT_REQUIRED = {
    'radius': positive, # radius of light; nothing past it is lit
}
LIGHT_OPTIONAL = {
    'pos': (vec3, (0.0, 0.0, 0.0)), # position of light (with "follow_player" it is the offset from the player instead)
    'follow_player': (flag, False), # true: the light moves with the player
    'intensity': (float, 1.0), # intensity of light
    'color': (vec3, (1.0, 1.0, 1.0)), # color of light
    'falloff': (falloff, 'linear'), # "linear" or "inverse_square" (dies off faster the further away it is)
    'falloff_scale': (positive, 1.0), # how hard "inverse_square" falls off (higher is faster)
    'snap': (flag, True), # true: the light sits in the middle of its block
    'diffuse': (unit, 1.0), # 0: surface angle doesn't matter, 1: surfaces facing away from the light get no light
}

# a map file's "lighting" (everything in the scene that isn't one light), all optional
FACE_SHADE_OPTIONAL = { # brightness of each side of a block, which gives blocks their depth
    'top': (float, 1.0),
    'bottom': (float, 0.75),
    'front': (float, 0.916),
    'back': (float, 0.916),
    'left': (float, 0.833),
    'right': (float, 0.833),
}
LIGHTING_OPTIONAL = {
    'ambient': (float, 0.0625), # light every surface gets so nothing is fully black
    'ambient_color': (vec3, (1.0, 1.0, 1.0)), # color of the ambient light
    'brightness': (float, 0.5), # multiplier for all light color
    'per_block': (flag, True), # true: every block is lit as a whole (from its middle); false: every pixel is lit separately
}

MAP_KEYS = ['name', 'description', 'config', 'lights', 'lighting', 'world', 'edits'] # (edits are made and saved by rend, see rend.py)

# ------

def load_env(errors):
    if not os.path.exists(ENV_FILES[0]):
        errors.append(f'{ENV_FILES[0]} (file is missing, it holds the default for every setting)')

        return {}

    values = {}

    for path in ENV_FILES:
        if os.path.exists(path):
            values.update({key: val for key, val in dotenv_values(path).items() if val is not None})

    settings = {key.lower(): val for key, val in parse(values, ENV_SETTINGS, {}, '', errors).items()}

    if 'width' in settings and 'height' in settings:
        size = (settings['width'], settings['height'])
        settings['width'] = max(WINDOW_MIN[0], min(WINDOW_MAX[0], size[0]))
        settings['height'] = max(WINDOW_MIN[1], min(WINDOW_MAX[1], size[1]))

        if size != (settings['width'], settings['height']):
            log.debug('Window size was outside the allowed range', asked=f'{size[0]}x{size[1]}', using=f"{settings['width']}x{settings['height']}", allowed=f'{WINDOW_MIN[0]}x{WINDOW_MIN[1]} to {WINDOW_MAX[0]}x{WINDOW_MAX[1]}')

    return settings

def load_map(map_path, errors):
    # returns (map settings, world data) of a map file
    try:
        with open(map_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
    except FileNotFoundError:
        errors.append(f'{map_path} (map file is missing)')

        return {}, {}
    except json.JSONDecodeError as e:
        errors.append(f'{map_path} (not valid JSON: {e})')

        return {}, {}
    except Exception as e:
        errors.append(f'{map_path} (could not be loaded: {e})')

        return {}, {}

    if not isinstance(map_data, dict) or not isinstance(map_data.get('config'), dict):
        errors.append(f'{map_path} (needs a "config" object)')

        return {}, {}

    for key in map_data:
        if key not in MAP_KEYS:
            errors.append(f'{key} (unknown section of the map file, use {", ".join(MAP_KEYS)})')

    settings = parse(map_data['config'], MAP_SETTINGS, MAP_OPTIONAL_SETTINGS, 'config.', errors)

    # lights
    lights_raw = map_data.get('lights')

    if not isinstance(lights_raw, list):
        errors.append('lights (needs a list, it can be empty)')
        lights_raw = []

    lights = []

    for i, light_raw in enumerate(lights_raw):
        where = f'lights[{i}].'

        if not isinstance(light_raw, dict):
            errors.append(f'lights[{i}] (needs an object)')

            continue

        light = parse(light_raw, LIGHT_REQUIRED, LIGHT_OPTIONAL, where, errors)

        if not light.get('follow_player') and 'pos' not in light_raw:
            errors.append(f'{where}pos (missing, a light needs it unless it has "follow_player": true)')

        lights.append(SimpleNamespace(**light))

    settings['lights'] = lights

    # lighting
    lighting_raw = map_data.get('lighting', {})

    if not isinstance(lighting_raw, dict):
        errors.append('lighting (needs an object)')
        lighting_raw = {}

    face_shade_raw = lighting_raw.get('face_shade', {})

    if not isinstance(face_shade_raw, dict):
        errors.append('lighting.face_shade (needs an object)')
        face_shade_raw = {}

    lighting = parse({key: val for key, val in lighting_raw.items() if key != 'face_shade'}, {}, LIGHTING_OPTIONAL, 'lighting.', errors)
    face_shade = parse(face_shade_raw, {}, FACE_SHADE_OPTIONAL, 'lighting.face_shade.', errors)

    lighting['face_shade'] = [face_shade[side] for side in ('top', 'bottom', 'front', 'back', 'left', 'right')] # the order the shader expects
    settings['lighting'] = SimpleNamespace(**lighting)

    # edits (made in the game with rend and saved with .save): checked here, played by World.build
    from world import BLOCK_TYPES

    edits = map_data.get('edits', [])
    problems = rend.validate_edits(edits, set(BLOCK_TYPES) | {rend.AIR})
    errors.extend(problems)
    settings['edits'] = [] if problems else edits

    return settings, map_data.get('world', {})

def load(map_name):
    # returns (settings, world_data): the settings of .env.pre / .env and of the map file (as an object with one attribute per setting) and the map's "world" (its blocks)
    # prints everything that is wrong and returns (None, None) if the settings can't be used
    map_name = map_name if map_name.lower().endswith('.json') else f'{map_name}.json'
    map_path = os.path.join(MAPS_DIR, map_name)

    errors = []
    settings = load_env(errors)
    map_settings, world_data = load_map(map_path, errors)

    if errors:
        log.error('Settings are wrong', map=map_path, **{f'problem {i + 1}': problem for i, problem in enumerate(errors)})

        return None, None

    settings.update(map_settings)
    settings['map_path'] = map_path # where rend saves the edits

    return SimpleNamespace(**settings), world_data
