from .base import add, F, I, B, C, RGB, PT

# dithering, pixel looks, old screens and tapes

add('dither', 'retro', 'only a few colors, with the steps between them drawn as a pattern or as noise (many kinds of patterns)', [
    C('type', 'bayer8', ['bayer2', 'bayer4', 'bayer8', 'bayer16', 'cluster', 'dots', 'lines', 'checker', 'ign', 'r2', 'noise'], 'the pattern: bayer2/4/8/16 are the classic square patterns (bigger is finer), cluster/dots/lines are like print, checker is a chessboard, ign and r2 are smooth blue-noise-like patterns, noise is random like film grain'),
    I('levels', 2, 2, 32, 'how many steps of brightness (2 is only dark and light)'),
    F('size', 2.0, 1, 32, 'the size of one dither pixel (measured on a screen 1080 high)'),
    C('mode', 'mono', ['mono', 'color'], 'mono works on the brightness and uses the dark and light colors, color dithers every color channel on its own'),
    RGB('dark', (0.0, 0.0, 0.0), 'the color of the dark (and of the first step in color mode)'),
    RGB('light', (1.0, 1.0, 1.0), 'the color of the light'),
    F('contrast', 1.0, 0.1, 4, 'below 1 brightens the dark parts so more of a dark picture survives (1 is no change)'),
    F('black', 0.0, 0, 0.99, 'anything darker than this is plain dark, so an empty background does not speckle'),
    C('luma', 'rec601', ['rec601', 'rec709', 'average', 'max', 'red', 'green', 'blue'], 'how the brightness is worked out in mono mode'),
    F('spread', 1.0, 0, 2, 'how strong the pattern is: 0 is a plain cut in the middle, 1 the whole pattern, above 1 more noisy'),
    F('scale', 8.0, 2, 64, 'the size of one repeat of the pattern, in dither pixels (cluster, dots, lines and checker)'),
    F('angle', 45.0, -180, 180, 'turns the pattern (cluster, dots, lines and checker)'),
    F('flicker', 0.0, 0, 120, 'how many times a second the pattern changes (0 keeps it still)'),
], """
float dither_pattern(ivec2 cell, vec2 cuv) {
    int frame = int(floor(u_time * u_flicker)) + u_seed;
    ivec2 pc = cell + ivec2(frame * 3, frame * 5);
    vec2 q = rot2(radians(u_angle)) * (vec2(pc) + 0.5);
    vec2 f = fract(q / u_scale) - 0.5;
    float p = 0.5;

    if (u_type == TYPE_BAYER2) p = bayer(pc, 1);
    else if (u_type == TYPE_BAYER4) p = bayer(pc, 2);
    else if (u_type == TYPE_BAYER8) p = bayer(pc, 3);
    else if (u_type == TYPE_BAYER16) p = bayer(pc, 4);
    else if (u_type == TYPE_CLUSTER) p = 1.0 - ((cos(TAU * f.x) + cos(TAU * f.y)) * 0.25 + 0.5);
    else if (u_type == TYPE_DOTS) p = length(f) * 1.41421356;
    else if (u_type == TYPE_LINES) p = abs(f.y) * 2.0;
    else if (u_type == TYPE_CHECKER) p = 0.25 + 0.5 * mod(floor(q.x / u_scale) + floor(q.y / u_scale), 2.0);
    else if (u_type == TYPE_IGN) p = fract(52.9829189 * fract(dot(vec2(pc) + 0.5, vec2(0.06711056, 0.00583715))));
    else if (u_type == TYPE_R2) p = fract(dot(vec2(pc) + 0.5, vec2(0.7548776662, 0.5698402910)));
    else p = rand_classic(cuv * u_resolution + vec2(float(frame) * 91.7, float(frame) * 53.3));

    return clamp(p, 0.0005, 0.9995);
}

float dither_luma(vec3 c) {
    if (u_luma == LUMA_REC709) return dot(c, vec3(0.2126, 0.7152, 0.0722));
    if (u_luma == LUMA_AVERAGE) return dot(c, vec3(0.333, 0.333, 0.333));
    if (u_luma == LUMA_MAX) return max(max(c.r, c.g), c.b);
    if (u_luma == LUMA_RED) return c.r;
    if (u_luma == LUMA_GREEN) return c.g;
    if (u_luma == LUMA_BLUE) return c.b;
    return dot(c, vec3(0.299, 0.587, 0.114));
}

vec3 dither_tone(vec3 v) {
    return pow(max(v - u_black, 0.0) / (1.0 - u_black), vec3(u_contrast));
}

vec4 fx(vec4 c, vec2 uv) {
    int s = max(1, int(floor(u_size * PX + 0.5)));
    ivec2 cell = ivec2(gl_FragCoord.xy) / s;
    vec2 cuv = (s == 1) ? uv : (vec2(cell * s) + 0.5 * float(s)) / u_resolution; // (with single pixels the place of the pixel itself, so the noise is the same as it always was)
    vec3 color = prev(cuv).rgb;
    float thr = mix(0.5, dither_pattern(cell, cuv), u_spread);
    float n = float(u_levels - 1);

    if (u_mode == MODE_MONO) {
        float v = clamp(dither_tone(vec3(dither_luma(color))).x, 0.0, 1.0);
        float sc = v * n;
        float lo = floor(sc);
        float level = lo + ((sc - lo > thr) ? 1.0 : 0.0);
        return vec4(mix(u_dark, u_light, min(level, n) / n), 1.0);
    }

    vec3 sc = clamp(dither_tone(color), 0.0, 1.0) * n;
    vec3 lo = floor(sc);
    vec3 level = lo + vec3(greaterThan(sc - lo, vec3(thr)));
    return vec4(mix(u_dark, u_light, min(level, vec3(n)) / n), 1.0);
}
""", animated=True, seeded=True)

add('pixelate', 'retro', 'big pixels (squares, hexagons or bricks), with an optional gap between them like an LED screen', [
    F('size', 8.0, 1, 256, 'the size of one pixel (measured on a screen 1080 high)'),
    C('shape', 'square', ['square', 'hex', 'brick'], 'the shape of the pixels'),
    F('gap', 0.0, 0, 0.9, 'how much of every pixel is gap (0 is none)'),
    RGB('gap_color', (0.0, 0.0, 0.0), 'the color of the gap'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float s = max(1.0, floor(u_size * PX + 0.5));
    vec2 f = gl_FragCoord.xy;
    vec2 center;
    float inside = 0.0; // 0 in the middle of a pixel, 1 at its edge

    if (u_shape == SHAPE_SQUARE) {
        center = (floor(f / s) + 0.5) * s;
        vec2 l = abs(f - center) / (0.5 * s);
        inside = max(l.x, l.y);
    } else if (u_shape == SHAPE_BRICK) {
        float row = floor(f.y / s);
        float off = mod(row, 2.0) * s;
        float col = floor((f.x + off) / (2.0 * s));
        center = vec2((col + 0.5) * 2.0 * s - off, (row + 0.5) * s);
        vec2 l = abs(f - center) / vec2(s, 0.5 * s);
        inside = max(l.x, l.y);
    } else {
        vec2 p = f / s;
        vec2 r = vec2(1.0, 1.7320508);
        vec2 h = r * 0.5;
        vec2 a = mod(p, r) - h;
        vec2 b = mod(p - h, r) - h;
        vec2 gv = dot(a, a) < dot(b, b) ? a : b;
        center = (p - gv) * s;
        inside = length(gv) * 2.0;
    }

    vec3 col = prev(center / u_resolution).rgb;
    if (u_gap > 0.0 && inside > 1.0 - u_gap) col = u_gap_color;
    return vec4(col, 1.0);
}
""")

add('lowres', 'retro', 'looks like a low resolution picture with few colors (big pixels, steps of color, a little dither)', [
    F('height', 180.0, 16, 1080, 'how many pixels the screen is high'),
    I('levels', 6, 2, 32, 'how many steps of every color channel'),
    F('dither', 0.6, 0, 1, 'a little pattern that hides the steps between colors'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float s = max(1.0, floor(1080.0 / u_height * PX + 0.5));
    vec2 cell = floor(gl_FragCoord.xy / s);
    vec3 col = clamp(prev((cell + 0.5) * s / u_resolution).rgb, 0.0, 1.0);
    float n = float(u_levels - 1);
    float t = (bayer(ivec2(cell), 2) - 0.5) * u_dither;
    return vec4(clamp(floor(col * n + 0.5 + t) / n, 0.0, 1.0), 1.0);
}
""")

add('ascii', 'retro', 'draws the picture with letters, brighter parts get fuller ones (. : * o & 8 @ #)', [
    F('size', 8.0, 4, 48, 'the size of one letter (measured on a screen 1080 high)'),
    C('mode', 'color', ['color', 'mono', 'tint'], 'color uses the color of the picture, mono is grey, tint is one color'),
    RGB('tint', (0.2, 1.0, 0.4), 'the color of the letters in tint mode'),
    F('gain', 1.3, 0.25, 4, 'makes the picture look brighter to the letters (more full ones)'),
    F('background', 0.3, 0, 1, 'how much of the picture shows behind the letters'),
    B('invert', False, 'dark letters on a light picture'),
], """
float character(int n, vec2 p) {
    p = floor(p * vec2(-4.0, 4.0) + 2.5);
    if (p.x >= 0.0 && p.x <= 4.0 && p.y >= 0.0 && p.y <= 4.0) {
        int a = int(p.x + 5.0 * p.y + 0.5);
        if (((n >> a) & 1) == 1) return 1.0;
    }
    return 0.0;
}

vec4 fx(vec4 c, vec2 uv) {
    float s = max(4.0, floor(u_size * PX + 0.5));
    vec2 cell = floor(gl_FragCoord.xy / s);
    vec3 col = prev((cell + 0.5) * s / u_resolution).rgb;
    float gray = clamp((col.r + col.g + col.b) / 3.0 * u_gain, 0.0, 1.0);

    int n = 4096;
    if (gray > 0.2) n = 65600;
    if (gray > 0.3) n = 332772;
    if (gray > 0.4) n = 15255086;
    if (gray > 0.5) n = 23385164;
    if (gray > 0.6) n = 15252014;
    if (gray > 0.7) n = 13199452;
    if (gray > 0.8) n = 11512810;

    float ch = character(n, fract(gl_FragCoord.xy / s) * 2.0 - 1.0);
    if (u_invert == 1) ch = 1.0 - ch;

    vec3 ink = clamp(col * u_gain, 0.0, 1.0);
    if (u_mode == MODE_MONO) ink = vec3(gray);
    if (u_mode == MODE_TINT) ink = u_tint * gray;

    return vec4(ink * ch + col * u_background * (1.0 - ch), 1.0);
}
""")

add('scanlines', 'retro', 'dark lines across the picture, like a tube screen', [
    F('strength', 0.35, 0, 1, 'how dark the lines are'),
    F('spacing', 3.0, 1, 32, 'the distance from one line to the next (measured on a screen 1080 high)'),
    F('thickness', 0.5, 0.05, 0.95, 'how much of the space between the lines is dark'),
    F('softness', 0.3, 0, 1, 'how soft the edges of the lines are'),
    RGB('color', (0.0, 0.0, 0.0), 'the color of the lines'),
    C('direction', 'horizontal', ['horizontal', 'vertical'], 'which way the lines run'),
    F('scroll', 0.0, -500, 500, 'how fast the lines crawl (pixels a second, 0 keeps them still)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float period = max(1.0, u_spacing * PX);
    float coord = (u_direction == DIRECTION_HORIZONTAL ? gl_FragCoord.y : gl_FragCoord.x) + u_scroll * PX * u_time;
    float ph = fract(coord / period);
    float edge = 0.5 * u_softness * min(u_thickness, 1.0 - u_thickness) + 0.0001;
    float dark = 1.0 - smoothstep(u_thickness - edge, u_thickness + edge, ph);
    return vec4(mix(c.rgb, u_color, u_strength * dark), 1.0);
}
""", animated=True)

add('shadowmask', 'retro', 'the red, green and blue dots or stripes of a tube screen', [
    F('size', 6.0, 2, 24, 'the width of one red-green-blue group (measured on a screen 1080 high)'),
    C('type', 'aperture', ['aperture', 'dots', 'slot'], 'aperture is vertical stripes, dots is staggered dots, slot has gaps between the rows'),
    F('strength', 0.6, 0, 1, 'how much of the mask is used'),
    F('boost', 1.15, 0.5, 3, 'makes the picture brighter again (the mask darkens it)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float w = max(3.0, u_size * PX);
    vec2 f = gl_FragCoord.xy;
    float rh = w * 1.5;
    float row = floor(f.y / rh);
    float x = f.x;
    if (u_type == TYPE_DOTS) x += mod(row, 2.0) * w * 0.5;

    int idx = int(mod(floor(x / (w / 3.0)), 3.0));
    vec3 m = vec3(idx == 0 ? 1.0 : 0.0, idx == 1 ? 1.0 : 0.0, idx == 2 ? 1.0 : 0.0);

    float ly = fract(f.y / rh);
    float gap = smoothstep(0.0, 0.2, ly) * (1.0 - smoothstep(0.8, 1.0, ly));
    if (u_type == TYPE_APERTURE) gap = 1.0;
    if (u_type == TYPE_SLOT && mod(floor(x / w) + row, 2.0) != 0.0) gap = 1.0;

    vec3 mask = (vec3(0.4) + m * 1.8) * gap;
    return vec4(mix(c.rgb, c.rgb * mask * u_boost, u_strength), 1.0);
}
""")

add('curvature', 'retro', 'bends the picture like the glass of a tube screen, with dark corners', [
    F('amount', 0.3, 0, 1, 'how much the screen bulges'),
    F('corner', 0.05, 0, 0.5, 'how round the corners of the screen are'),
    RGB('border', (0.0, 0.0, 0.0), 'the color outside the screen'),
    F('zoom', 1.0, 0.5, 2, 'above 1 zooms in (hides the dark corners)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 cc = (uv * 2.0 - 1.0) / u_zoom;
    vec2 cc2 = cc * (1.0 + u_amount * dot(cc, cc)) / (1.0 + u_amount);
    vec2 uv2 = cc2 * 0.5 + 0.5;

    vec2 half_size = vec2(ASPECT, 1.0);
    vec2 p = abs(cc2) * half_size;
    float r = u_corner * 2.0;
    float sdf = length(max(p - (half_size - r), 0.0)) - r;
    float mask = 1.0 - smoothstep(-0.004, 0.004, sdf);
    return vec4(mix(u_border, prev(clamp(uv2, 0.0, 1.0)).rgb, mask), 1.0);
}
""")

add('interlace', 'retro', 'every other line is dark or shifted, and which lines they are flips all the time', [
    F('strength', 0.5, 0, 1, 'how dark the lines of the other field are'),
    F('spacing', 1.0, 1, 8, 'the height of one line (measured on a screen 1080 high)'),
    F('comb', 3.0, 0, 30, 'how far the other lines are shifted sideways (pixels)'),
    F('rate', 30.0, 0, 240, 'how many times a second the lines flip'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float row = floor(gl_FragCoord.y / max(1.0, u_spacing * PX));
    float field = mod(floor(u_time * u_rate), 2.0);
    if (mod(row, 2.0) != field) return c;

    vec3 shifted = prev(uv + vec2(u_comb * PX / u_resolution.x, 0.0)).rgb;
    return vec4(shifted * (1.0 - u_strength), 1.0);
}
""", animated=True)

add('vhs', 'retro', 'an old video tape: wobbling lines, a rolling bar, smeared colors, noise', [
    F('jitter', 0.6, 0, 2, 'how much every line wobbles sideways'),
    F('tracking', 0.6, 0, 2, 'how much the bar that rolls up the screen (and the bottom of the picture) is torn'),
    F('bleed', 2.0, 0, 8, 'how much the colors smear sideways'),
    F('noise', 0.5, 0, 2, 'how much static'),
    F('fade', 0.3, 0, 1, 'how washed out and dim it is'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = u_time;
    float row = floor(gl_FragCoord.y / max(1.0, PX));
    float frame = floor(t * 25.0) + float(u_seed);

    float j = (hash12(vec2(row, frame)) - 0.5) * 2.0 * u_jitter * 0.004 + sin(uv.y * 40.0 + t * 3.0) * u_jitter * 0.0015;
    float bar_y = fract(t * 0.08);
    float band = exp(-abs(uv.y - bar_y) * 20.0);
    float bottom = smoothstep(0.05, 0.0, uv.y);
    j += (band * 0.03 + bottom * 0.06) * u_tracking * (hash12(vec2(row, frame + 17.0)) - 0.3);

    vec2 p = vec2(uv.x + j, uv.y);
    vec3 s0 = prev(p).rgb;
    float dx = u_bleed * 2.0 * PX / u_resolution.x;
    vec3 chroma = vec3(0.0);
    for (int i = -4; i <= 4; i++) {
        vec3 s = prev(p + vec2(float(i) * dx, 0.0)).rgb;
        chroma += s - vec3(luma(s));
    }
    chroma /= 9.0;
    vec3 col = vec3(luma(s0)) + chroma;

    float n = hash12(gl_FragCoord.xy + frame * 37.0);
    col += (n - 0.5) * u_noise * 0.4;
    float streak = step(0.996, hash12(vec2(row, frame))) * hash12(vec2(floor(gl_FragCoord.x / (8.0 * PX)), row));
    col += streak * u_noise * 0.6;

    col = mix(col, vec3(luma(col)), u_fade * 0.5) * (1.0 - 0.1 * u_fade);
    return vec4(col, 1.0);
}
""", animated=True, seeded=True)

add('glitch', 'retro', 'a broken digital picture: blocks jump sideways, colors split, parts flip', [
    F('amount', 0.3, 0, 1, 'how much of the picture is broken'),
    F('blocks', 32.0, 4, 200, 'how many rows the picture is cut into'),
    F('split', 6.0, 0, 40, 'how far the red and blue are shifted apart in the broken parts (pixels)'),
    F('rate', 12.0, 0, 60, 'how many times a second the glitch changes'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float slot = floor(u_time * u_rate) + float(u_seed);
    float row = floor(uv.y * u_blocks);
    float h = hash12(vec2(row, slot));
    float hit = step(1.0 - u_amount, h);
    float h2 = hash12(vec2(floor(uv.y * u_blocks * 0.25), slot + 11.0));
    float hit2 = step(1.0 - u_amount * 0.5, h2);

    float shift = (hash12(vec2(row, slot + 3.0)) - 0.5) * 0.3 * hit + (hash12(vec2(row, slot + 5.0)) - 0.5) * 0.2 * hit2;
    vec2 p = vec2(uv.x + shift, uv.y);
    float split = u_split * PX / u_resolution.x * (0.25 + 3.0 * max(hit, hit2));
    vec3 col = vec3(prev(p + vec2(split, 0.0)).r, prev(p).g, prev(p - vec2(split, 0.0)).b);

    float flip = step(1.0 - u_amount * 0.15, hash12(vec2(row, slot + 7.0)));
    col = mix(col, 1.0 - col, flip);
    return vec4(col, 1.0);
}
""", animated=True, seeded=True)

add('chromatic', 'retro', 'the colors of the picture are pulled apart, like a cheap lens (stronger towards the edges)', [
    F('amount', 2.0, 0, 10, 'how far apart (as a percent of the screen)'),
    C('mode', 'radial', ['radial', 'linear'], 'radial grows away from the center, linear shifts in one direction'),
    PT('center', (0.5, 0.5), 'the middle of the lens (radial)'),
    F('angle', 0.0, -180, 180, 'the direction of the shift (linear)'),
    I('samples', 6, 3, 16, 'how many steps between red and blue (3 is red, green and blue only)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 d = (u_mode == MODE_RADIAL) ? (uv - u_center) : vec2(cos(radians(u_angle)), sin(radians(u_angle))) * 0.5;
    float amt = u_amount * 0.01;
    vec3 sum = vec3(0.0);
    vec3 wsum = vec3(0.0);

    for (int i = 0; i < 16; i++) {
        if (i >= u_samples) break;
        float t = float(i) / float(u_samples - 1);
        vec3 w = vec3(clamp(1.0 - 2.0 * t, 0.0, 1.0), 1.0 - abs(2.0 * t - 1.0), clamp(2.0 * t - 1.0, 0.0, 1.0));
        sum += prev(uv + d * amt * (2.0 * t - 1.0)).rgb * w;
        wsum += w;
    }

    return vec4(sum / max(wsum, vec3(0.0001)), 1.0);
}
""")

add('rgbsplit', 'retro', 'the red and blue copies of the picture are shifted apart (an anaglyph or 3D glasses look)', [
    F('distance', 6.0, 0, 100, 'how far apart (pixels, measured on a screen 1080 high)'),
    F('angle', 0.0, -180, 180, 'the direction of the shift'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 off = vec2(cos(radians(u_angle)), sin(radians(u_angle))) * u_distance * PX / u_resolution;
    return vec4(prev(uv + off).r, c.g, prev(uv - off).b, 1.0);
}
""")
