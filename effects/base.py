import re

# the menu of full-screen effects (see fx.py for how they are stacked and used)
# an effect is a piece of GLSL, written once, with settings (parameters) that reach the shader as uniforms: changing a setting never needs a new shader, only the first use of an effect compiles it
# in the GLSL of an effect, `fx(vec4 c, vec2 uv)` gets the color c of the pixel (of the image so far) and returns the new color; a few helpers (luma, noise, hsv, blend modes, PX = one pixel at 1080 high) are in the PRELUDE below
# sizes that are measured in pixels are measured on a window 1080 high and grow and shrink with the window, so an effect looks the same at every resolution

CATEGORIES = ['color', 'retro', 'blur', 'edges', 'distort', 'overlay']

CATEGORY_DOCS = {
    'color': 'colors and tone: brightness, hue, palettes, tints',
    'retro': 'dithering, pixel looks, old screens and tapes',
    'blur': 'blur, sharpen and glow',
    'edges': 'edges, outlines and drawn looks',
    'distort': 'bending, waving and moving the picture',
    'overlay': 'things drawn over the picture: vignette, grain, crosshair, weather',
}

BLEND_MODES = ['normal', 'multiply', 'screen', 'overlay', 'softlight', 'hardlight', 'add', 'subtract', 'difference', 'dodge', 'burn']

EDGE_MODES = ['clamp', 'mirror', 'repeat', 'black'] # what an effect that moves the picture shows where it reaches past the edge (the order is prev_edge in the PRELUDE)


class Param:
    # kind: float, int, bool, choice, color (r, g, b from 0 to 1), point (x, y from 0 to 1 over the screen, 0 0 is the bottom left)
    def __init__(self, name, kind, default, low=None, high=None, choices=None, doc=''):
        self.name = name
        self.kind = kind
        self.default = default
        self.low = low
        self.high = high
        self.choices = choices
        self.doc = doc

        if kind == 'choice':
            assert default in choices, (name, default, choices)
        if kind in ('float', 'int'):
            assert low <= default <= high, (name, default, low, high)


def F(name, default, low, high, doc=''):
    return Param(name, 'float', float(default), float(low), float(high), doc=doc)


def I(name, default, low, high, doc=''):
    return Param(name, 'int', int(default), int(low), int(high), doc=doc)


def B(name, default, doc=''):
    return Param(name, 'bool', bool(default), doc=doc)


def C(name, default, choices, doc=''):
    return Param(name, 'choice', default, choices=list(choices), doc=doc)


def RGB(name, default, doc=''):
    return Param(name, 'color', tuple(float(v) for v in default), doc=doc)


def PT(name, default, doc=''):
    return Param(name, 'point', tuple(float(v) for v in default), doc=doc)


def EDGE(default='mirror'):
    return C('edge', default, EDGE_MODES, 'what to show where the picture is moved away from the edge of the screen')


def BLEND(default='normal'):
    return C('blend', default, BLEND_MODES, 'how it goes over the picture')


class Effect:
    def __init__(self, name, category, doc, params, passes, animated=False, seeded=False):
        self.name = name
        self.category = category
        self.doc = doc
        self.own = list(params) # the settings that belong to this effect
        self.passes = list(passes) # GLSL of every pass (a blur has 2: sideways, then up and down)
        self.animated = animated # it changes with time: gets a speed setting
        self.seeded = seeded # it uses random numbers: gets a seed setting

        extra = [F('mix', 1.0, 0.0, 1.0, 'how much of the effect is used: 0 is none, 1 is all of it')]

        if animated:
            extra.append(F('speed', 1.0, -20.0, 20.0, 'how fast it moves (0 stops it, negative runs it backwards)'))
        if seeded:
            extra.append(I('seed', 0, 0, 9999, 'a different number gives a different random pattern'))

        self.params = self.own + extra
        self.by_name = {p.name: p for p in self.params}

        names = [p.name for p in self.params]
        assert len(set(names)) == len(names), name


REGISTRY = {} # name -> Effect, in the order of the menu


def add(name, category, doc, params, glsl=None, passes=None, animated=False, seeded=False):
    assert name not in REGISTRY, name
    assert category in CATEGORIES, category
    REGISTRY[name] = Effect(name, category, doc, params, passes or [glsl], animated, seeded)

    return REGISTRY[name]


def alias(new_name, old_name, doc, **defaults):
    # the same effect with other starting values (an outline is an edge drawn over the picture)
    old = REGISTRY[old_name]
    params = []

    for p in old.own:
        q = Param(p.name, p.kind, defaults.get(p.name, p.default), p.low, p.high, p.choices, p.doc)
        params.append(q)

    return add(new_name, old.category, doc, params, passes=old.passes, animated=old.animated, seeded=old.seeded)


# ------ what every effect can use

PRELUDE = """
in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture; // the image the effect works on
uniform sampler2D u_prev; // the result of the previous pass of the effect (in the first pass it is the same as u_texture)
uniform vec2 u_resolution;
uniform float u_time; // seconds, times the speed of the effect
uniform float u_mix;
uniform int u_seed;

const float PI = 3.14159265359;
const float TAU = 6.28318530718;
#define PX (u_resolution.y / 1080.0)
#define ASPECT (u_resolution.x / u_resolution.y)
#define TEXEL (1.0 / u_resolution)

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

float rand_classic(vec2 co) { return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453); }

float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash12(i);
    float b = hash12(i + vec2(1.0, 0.0));
    float c = hash12(i + vec2(0.0, 1.0));
    float d = hash12(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p, int octaves) {
    float sum = 0.0;
    float amp = 0.5;
    for (int i = 0; i < octaves; i++) {
        sum += amp * vnoise(p);
        p = p * 2.02 + 7.3;
        amp *= 0.5;
    }
    return sum;
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

mat2 rot2(float a) { float s = sin(a); float c = cos(a); return mat2(c, -s, s, c); }

// the threshold (0 to 1) of the ordered pattern of Bayer, a square of 2^bits pixels on a side (bits 3 is the 8x8 pattern)
float bayer(ivec2 p, int bits) {
    int v = 0;
    for (int i = 0; i < bits; i++) {
        int xb = (p.x >> i) & 1;
        int yb = (p.y >> i) & 1;
        v = (v << 2) | ((xb ^ yb) << 1) | yb;
    }
    return (float(v) + 0.5) / float(1 << (2 * bits));
}

vec4 src(vec2 uv) { return texture(u_texture, uv); }
vec4 prev(vec2 uv) { return texture(u_prev, uv); }

// the picture at a place that may be off the screen: 0 clamp, 1 mirror, 2 repeat, 3 black (EDGE_MODES in base.py)
vec3 prev_edge(vec2 p, int mode) {
    if (mode == 1) p = 1.0 - abs(mod(p, 2.0) - 1.0);
    else if (mode == 2) p = fract(p);
    else if (mode == 3 && (p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0)) return vec3(0.0);
    return texture(u_prev, clamp(p, 0.0, 1.0)).rgb;
}

// the place on the screen as x, y with 0 0 in the middle and y from -0.5 to 0.5 (so a circle is round), and back
vec2 centered(vec2 uv) { return (uv - 0.5) * vec2(ASPECT, 1.0); }
vec2 uncentered(vec2 p) { return p / vec2(ASPECT, 1.0) + 0.5; }

// how a color on top is put over the color below it (the order is BLEND_MODES in base.py)
vec3 blend_mode(int mode, vec3 base, vec3 top) {
    if (mode == 1) return base * top;
    if (mode == 2) return 1.0 - (1.0 - base) * (1.0 - top);
    if (mode == 3) return mix(2.0 * base * top, 1.0 - 2.0 * (1.0 - base) * (1.0 - top), step(0.5, base));
    if (mode == 4) return mix(2.0 * base * top + base * base * (1.0 - 2.0 * top), sqrt(base) * (2.0 * top - 1.0) + 2.0 * base * (1.0 - top), step(0.5, top));
    if (mode == 5) return mix(2.0 * base * top, 1.0 - 2.0 * (1.0 - base) * (1.0 - top), step(0.5, top));
    if (mode == 6) return base + top;
    if (mode == 7) return base - top;
    if (mode == 8) return abs(base - top);
    if (mode == 9) return base / max(1.0 - top, 0.001);
    if (mode == 10) return 1.0 - (1.0 - base) / max(top, 0.001);
    return top;
}
"""


def constant_name(text):
    return re.sub(r'[^A-Za-z0-9]+', '_', text).upper()


def uniform_name(param):
    return 'u_' + param.name


def declarations(effect):
    # the uniforms of the settings, and a constant for every choice (TYPE_BAYER8 for the choice bayer8 of the setting type)
    lines = []

    for p in effect.own:
        glsl_type = {'float': 'float', 'int': 'int', 'bool': 'int', 'choice': 'int', 'color': 'vec3', 'point': 'vec2'}[p.kind]
        lines.append(f'uniform {glsl_type} {uniform_name(p)};')

        if p.kind == 'choice':
            for i, choice in enumerate(p.choices):
                lines.append(f'#define {constant_name(p.name)}_{constant_name(choice)} {i}')

    return '\n'.join(lines)


def fragment_source(effect, index):
    # the whole fragment shader of one pass of an effect; the last pass blends its result with the image the effect started from
    final = index == len(effect.passes) - 1
    head = '#version 330 core\n' + PRELUDE + '\n' + declarations(effect) + '\n#line 1\n'

    if final:
        main = """
void main() {
    vec4 result = fx(texture(u_prev, v_uv), v_uv);
    if (any(isnan(result.rgb))) result.rgb = vec3(0.0);
    vec4 base = texture(u_texture, v_uv);
    frag_color = vec4(mix(base.rgb, result.rgb, u_mix), 1.0);
}
"""
    else:
        main = """
void main() {
    vec4 result = fx(texture(u_prev, v_uv), v_uv);
    if (any(isnan(result.rgb))) result.rgb = vec3(0.0);
    frag_color = vec4(result.rgb, 1.0);
}
"""

    return head + effect.passes[index] + '\n' + main
