from .base import add, F, I, C, RGB

# colors and tone

add('tint', 'color', 'colors the whole picture', [
    RGB('color', (1.0, 0.75, 0.5), 'the color'),
    F('strength', 0.6, 0, 1, 'how much of the tint is used'),
    C('mode', 'multiply', ['multiply', 'add', 'screen'], 'how the color goes over the picture'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 t = c.rgb * u_color;
    if (u_mode == MODE_ADD) t = c.rgb + u_color * 0.5;
    if (u_mode == MODE_SCREEN) t = 1.0 - (1.0 - c.rgb) * (1.0 - u_color);
    return vec4(mix(c.rgb, t, u_strength), 1.0);
}
""")

add('brightness', 'color', 'makes everything lighter or darker', [
    F('amount', 0.2, -1, 1, 'how much to add (negative darkens)'),
], """
vec4 fx(vec4 c, vec2 uv) { return vec4(c.rgb + u_amount, 1.0); }
""")

add('contrast', 'color', 'pushes the colors away from (or towards) the middle grey', [
    F('amount', 1.4, 0, 4, 'above 1 more contrast, below 1 less'),
    F('pivot', 0.5, 0, 1, 'the brightness that stays as it is'),
], """
vec4 fx(vec4 c, vec2 uv) { return vec4((c.rgb - u_pivot) * u_amount + u_pivot, 1.0); }
""")

add('exposure', 'color', 'like the exposure of a camera: every stop doubles the light', [
    F('stops', 0.7, -5, 5, 'how many stops lighter (negative: darker)'),
], """
vec4 fx(vec4 c, vec2 uv) { return vec4(c.rgb * exp2(u_stops), 1.0); }
""")

add('gamma', 'color', 'brightens or darkens the middle tones and leaves black and white alone', [
    F('value', 1.5, 0.1, 5, 'above 1 lighter middle tones, below 1 darker'),
], """
vec4 fx(vec4 c, vec2 uv) { return vec4(pow(max(c.rgb, 0.0), vec3(1.0 / u_value)), 1.0); }
""")

add('levels', 'color', 'sets which brightness is black and which is white', [
    F('black', 0.1, 0, 1, 'everything at or below this becomes black'),
    F('white', 0.9, 0, 1, 'everything at or above this becomes white'),
    F('gamma', 1.0, 0.1, 5, 'the middle tones'),
    F('out_black', 0.0, 0, 1, 'the darkest the result can be'),
    F('out_white', 1.0, 0, 1, 'the lightest the result can be'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 v = clamp((c.rgb - u_black) / max(u_white - u_black, 0.001), 0.0, 1.0);
    v = pow(v, vec3(1.0 / u_gamma));
    return vec4(mix(vec3(u_out_black), vec3(u_out_white), v), 1.0);
}
""")

add('saturation', 'color', 'makes the colors stronger or weaker', [
    F('amount', 1.6, 0, 4, '0 is grey, 1 is as it was, above 1 stronger'),
], """
vec4 fx(vec4 c, vec2 uv) { return vec4(mix(vec3(luma(c.rgb)), c.rgb, u_amount), 1.0); }
""")

add('vibrance', 'color', 'like saturation, but mostly for the colors that are weak', [
    F('amount', 0.8, -1, 2, 'how much'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float strength = max(max(c.r, c.g), c.b) - min(min(c.r, c.g), c.b);
    return vec4(mix(vec3(luma(c.rgb)), c.rgb, 1.0 + u_amount * (1.0 - strength)), 1.0);
}
""")

add('hue', 'color', 'turns all the colors around the color wheel (let it cycle for a rainbow shift)', [
    F('shift', 60, -180, 180, 'degrees to turn the colors'),
    F('cycle', 0, -360, 360, 'degrees per second the colors keep turning'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 hsv = rgb2hsv(clamp(c.rgb, 0.0, 1.0));
    hsv.x = fract(hsv.x + (u_shift + u_cycle * u_time) / 360.0);
    return vec4(hsv2rgb(hsv), 1.0);
}
""", animated=True)

add('temperature', 'color', 'warm (orange) or cool (blue), and green or magenta', [
    F('warmth', 0.4, -1, 1, 'positive warmer, negative cooler'),
    F('tint', 0.0, -1, 1, 'positive towards magenta, negative towards green'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 k = vec3(1.0 + 0.3 * u_warmth + 0.1 * u_tint, 1.0 - 0.2 * u_tint, 1.0 - 0.3 * u_warmth + 0.1 * u_tint);
    return vec4(c.rgb * k, 1.0);
}
""")

add('grayscale', 'color', 'takes the color out', [
    C('mode', 'luma', ['luma', 'average', 'lightness', 'red', 'green', 'blue', 'desaturate'], 'how the grey is worked out (red, green, blue: that channel only)'),
    F('strength', 1.0, 0, 1, 'how much'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float g = luma(c.rgb);
    if (u_mode == MODE_AVERAGE) g = (c.r + c.g + c.b) / 3.0;
    if (u_mode == MODE_LIGHTNESS) g = 0.5 * (max(max(c.r, c.g), c.b) + min(min(c.r, c.g), c.b));
    if (u_mode == MODE_RED) g = c.r;
    if (u_mode == MODE_GREEN) g = c.g;
    if (u_mode == MODE_BLUE) g = c.b;
    if (u_mode == MODE_DESATURATE) g = max(max(c.r, c.g), c.b);
    return vec4(mix(c.rgb, vec3(g), u_strength), 1.0);
}
""")

add('sepia', 'color', 'the brown tint of old photographs', [
    F('strength', 1.0, 0, 1, 'how much'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 s = vec3(dot(c.rgb, vec3(0.393, 0.769, 0.189)), dot(c.rgb, vec3(0.349, 0.686, 0.168)), dot(c.rgb, vec3(0.272, 0.534, 0.131)));
    return vec4(mix(c.rgb, s, u_strength), 1.0);
}
""")

add('invert', 'color', 'turns the colors into their opposites', [
    C('mode', 'all', ['all', 'red', 'green', 'blue', 'brightness'], 'which colors (brightness: only light and dark swap, the hue stays)'),
    F('strength', 1.0, 0, 1, 'how much'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 r = 1.0 - c.rgb;
    if (u_mode == MODE_RED) r = vec3(1.0 - c.r, c.g, c.b);
    if (u_mode == MODE_GREEN) r = vec3(c.r, 1.0 - c.g, c.b);
    if (u_mode == MODE_BLUE) r = vec3(c.r, c.g, 1.0 - c.b);
    if (u_mode == MODE_BRIGHTNESS) {
        vec3 hsv = rgb2hsv(clamp(c.rgb, 0.0, 1.0));
        hsv.z = 1.0 - hsv.z;
        r = hsv2rgb(hsv);
    }
    return vec4(mix(c.rgb, r, u_strength), 1.0);
}
""")

add('duotone', 'color', 'only two colors: one for the dark, one for the light, and the tones between', [
    RGB('dark', (0.05, 0.0, 0.25), 'the color of the dark'),
    RGB('light', (1.0, 0.8, 0.4), 'the color of the light'),
    F('bias', 0.0, -1, 1, 'moves the middle towards the dark (negative) or the light (positive)'),
    F('contrast', 1.0, 0.1, 4, 'how sharply dark turns to light'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = clamp((luma(c.rgb) - 0.5) * u_contrast + 0.5 + u_bias * 0.5, 0.0, 1.0);
    return vec4(mix(u_dark, u_light, t), 1.0);
}
""")

add('gradientmap', 'color', 'colors the picture by brightness with a gradient of up to 5 colors', [
    RGB('color1', (0.0, 0.0, 0.1), 'the darkest color'),
    RGB('color2', (0.5, 0.0, 0.5), 'the second color'),
    RGB('color3', (1.0, 0.3, 0.2), 'the third color'),
    RGB('color4', (1.0, 0.9, 0.4), 'the fourth color'),
    RGB('color5', (1.0, 1.0, 1.0), 'the lightest color'),
    I('count', 4, 2, 5, 'how many of the colors are used (they are spread evenly over the brightness)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 cols[5] = vec3[5](u_color1, u_color2, u_color3, u_color4, u_color5);
    float t = clamp(luma(c.rgb), 0.0, 1.0) * float(u_count - 1);
    int i = min(int(floor(t)), u_count - 2);
    return vec4(mix(cols[i], cols[i + 1], t - float(i)), 1.0);
}
""")

add('posterize', 'color', 'only a few steps of color or brightness', [
    I('levels', 5, 2, 32, 'how many steps'),
    C('mode', 'rgb', ['rgb', 'brightness'], 'every color channel on its own, or only the brightness'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float n = float(u_levels - 1);
    if (u_mode == MODE_BRIGHTNESS) {
        float l = max(luma(c.rgb), 0.0001);
        return vec4(c.rgb * (floor(l * n + 0.5) / n) / l, 1.0);
    }
    return vec4(floor(clamp(c.rgb, 0.0, 1.0) * n + 0.5) / n, 1.0);
}
""")

add('threshold', 'color', 'every pixel becomes one of two colors: light or dark', [
    F('level', 0.5, 0, 1, 'the brightness where it turns from dark to light'),
    RGB('dark', (0.0, 0.0, 0.0), 'the color of the dark'),
    RGB('light', (1.0, 1.0, 1.0), 'the color of the light'),
    F('softness', 0.0, 0, 0.5, 'how soft the edge between them is'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = smoothstep(u_level - u_softness - 0.0001, u_level + u_softness + 0.0001, luma(c.rgb));
    return vec4(mix(u_dark, u_light, t), 1.0);
}
""")

add('mixer', 'color', 'mixes the red, green and blue channels into each other (a channel mixer)', [
    F('red_r', 1.0, -2, 2, 'how much of the red goes into the new red'),
    F('red_g', 0.0, -2, 2, 'how much of the green goes into the new red'),
    F('red_b', 0.0, -2, 2, 'how much of the blue goes into the new red'),
    F('green_r', 0.0, -2, 2, 'red into the new green'),
    F('green_g', 1.0, -2, 2, 'green into the new green'),
    F('green_b', 0.0, -2, 2, 'blue into the new green'),
    F('blue_r', 0.0, -2, 2, 'red into the new blue'),
    F('blue_g', 0.0, -2, 2, 'green into the new blue'),
    F('blue_b', 1.0, -2, 2, 'blue into the new blue'),
], """
vec4 fx(vec4 c, vec2 uv) {
    return vec4(dot(c.rgb, vec3(u_red_r, u_red_g, u_red_b)), dot(c.rgb, vec3(u_green_r, u_green_g, u_green_b)), dot(c.rgb, vec3(u_blue_r, u_blue_g, u_blue_b)), 1.0);
}
""")

add('swap', 'color', 'swaps the color channels around', [
    C('order', 'bgr', ['rgb', 'rbg', 'grb', 'gbr', 'brg', 'bgr'], 'which channel goes where (bgr: red and blue change places)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 r = c.rgb;
    if (u_order == ORDER_RBG) r = c.rbg;
    if (u_order == ORDER_GRB) r = c.grb;
    if (u_order == ORDER_GBR) r = c.gbr;
    if (u_order == ORDER_BRG) r = c.brg;
    if (u_order == ORDER_BGR) r = c.bgr;
    return vec4(r, 1.0);
}
""")

add('balance', 'color', 'tints the dark, middle and light parts of the picture separately (grey 0.5 changes nothing)', [
    RGB('shadows', (0.4, 0.5, 0.65), 'the tint of the dark parts'),
    RGB('midtones', (0.5, 0.5, 0.5), 'the tint of the middle'),
    RGB('highlights', (0.6, 0.5, 0.4), 'the tint of the light parts'),
    F('amount', 2.0, 0, 3, 'how strong'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float l = clamp(luma(c.rgb), 0.0, 1.0);
    float ws = (1.0 - l) * (1.0 - l);
    float wh = l * l;
    float wm = max(1.0 - ws - wh, 0.0);
    vec3 shift = ((u_shadows - 0.5) * ws + (u_midtones - 0.5) * wm + (u_highlights - 0.5) * wh) * u_amount;
    return vec4(c.rgb + shift, 1.0);
}
""")

add('splittone', 'color', 'one color into the dark and another into the light, like in film grading', [
    RGB('shadow', (0.1, 0.25, 0.55), 'the color of the dark'),
    RGB('highlight', (1.0, 0.75, 0.4), 'the color of the light'),
    F('balance', 0.0, -1, 1, 'moves the middle towards the shadows (negative) or the highlights (positive)'),
    F('strength', 0.7, 0, 1, 'how strong'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float l = clamp(luma(c.rgb), 0.0, 1.0);
    float t = smoothstep(0.0, 1.0, clamp(l + u_balance * 0.5, 0.0, 1.0));
    vec3 tone = mix(u_shadow, u_highlight, t);
    return vec4(mix(c.rgb, blend_mode(4, c.rgb, tone), u_strength), 1.0);
}
""")

add('matte', 'color', 'lifts the black to a color, for a faded film look', [
    RGB('color', (0.15, 0.1, 0.3), 'the color black becomes'),
    F('amount', 0.45, 0, 1, 'how much'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 lifted = mix(u_color, vec3(1.0), clamp(c.rgb, 0.0, 1.0));
    return vec4(mix(c.rgb, lifted, u_amount), 1.0);
}
""")

add('selectivecolor', 'color', 'keeps one color and takes the color out of everything else', [
    F('hue', 0, 0, 360, 'the color to keep, in degrees on the color wheel (0 red, 120 green, 240 blue)'),
    F('range', 45, 1, 180, 'how far from that hue is kept'),
    F('softness', 25, 0, 90, 'how soft the edge is'),
    F('strength', 1.0, 0, 1, 'how much of the other colors is taken out'),
    F('boost', 1.0, 0, 3, 'how strong the kept color is made'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 hsv = rgb2hsv(clamp(c.rgb, 0.0, 1.0));
    float d = abs(fract(hsv.x - u_hue / 360.0 + 0.5) - 0.5) * 360.0;
    float keep = 1.0 - smoothstep(u_range, u_range + max(u_softness, 0.001), d);
    vec3 kept = mix(vec3(luma(c.rgb)), c.rgb, u_boost);
    vec3 grey = vec3(luma(c.rgb));
    return vec4(mix(mix(c.rgb, grey, u_strength), kept, keep), 1.0);
}
""")


def palette_effect():
    palettes = {
        'gameboy': '0f380f 306230 8bac0f 9bbc0f',
        'cga1': '000000 55ffff ff55ff ffffff',
        'cga0': '000000 55ff55 ff5555 ffff55',
        'ega': '000000 0000aa 00aa00 00aaaa aa0000 aa00aa aa5500 aaaaaa 555555 5555ff 55ff55 55ffff ff5555 ff55ff ffff55 ffffff',
        'c64': '000000 ffffff 880000 aaffee cc44cc 00cc55 0000aa eeee77 dd8855 664400 ff7777 333333 777777 aaff66 0088ff bbbbbb',
        'pico8': '000000 1d2b53 7e2553 008751 ab5236 5f574f c2c3c7 fff1e8 ff004d ffa300 ffec27 00e436 29adff 83769c ff77a8 ffccaa',
        'sepia4': '2b1d0e 6e4a26 b08a58 f0deb4',
        'vaporwave': '0b0033 3b1a7a ff4fb4 5ad8ff ffd6f6 fff6a8',
        'solarized': '002b36 586e75 93a1a1 fdf6e3 b58900 dc322f 268bd2 859900',
        'green': '001a00 004d00 00b300 33ff33',
        'amber': '1a0d00 663300 cc7a00 ffbf33',
        '1bit': '000000 ffffff',
        'blueprint': '0a2a5e 1f5fae 6fa8e8 e8f2ff',
        'sunset': '1a0a3a 5c1a6a b8337a ff6a5a ffb25a fff0c0',
    }
    colors, starts, counts = [], [], []

    for hexes in palettes.values():
        starts.append(len(colors))
        items = hexes.split()
        counts.append(len(items))
        colors += [tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) for h in items]

    vec3s = ', '.join(f'vec3({r:.4f}, {g:.4f}, {b:.4f})' for r, g, b in colors)
    glsl = f"""
const vec3 PAL[{len(colors)}] = vec3[{len(colors)}]({vec3s});
const int PAL_START[{len(starts)}] = int[{len(starts)}]({', '.join(map(str, starts))});
const int PAL_COUNT[{len(counts)}] = int[{len(counts)}]({', '.join(map(str, counts))});

vec4 fx(vec4 c, vec2 uv) {{
    float t = bayer(ivec2(gl_FragCoord.xy / max(1.0, floor(PX + 0.5))), 2) - 0.5;
    vec3 col = clamp(c.rgb, 0.0, 1.0) + t * u_dither * 0.5;
    int start = PAL_START[u_palette];
    int count = PAL_COUNT[u_palette];
    float best = 1.0e9;
    vec3 chosen = PAL[start];
    for (int i = 0; i < count; i++) {{
        vec3 d = col - PAL[start + i];
        float dist = (u_match == MATCH_RGB) ? dot(d, d) : dot(d * d, vec3(0.299, 0.587, 0.114));
        if (dist < best) {{ best = dist; chosen = PAL[start + i]; }}
    }}
    return vec4(mix(c.rgb, chosen, u_strength), 1.0);
}}
"""
    add('palette', 'color', 'only the colors of an old computer or console: every pixel becomes the nearest color of a fixed palette', [
        C('palette', 'gameboy', list(palettes), 'which palette'),
        F('strength', 1.0, 0, 1, 'how much'),
        C('match', 'rgb', ['rgb', 'perceptual'], 'how the nearest color is found'),
        F('dither', 0.35, 0, 1, 'a little pattern that hides the steps between colors'),
    ], glsl)


palette_effect()
