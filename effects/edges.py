from .base import add, alias, F, I, B, C, RGB

# edges, outlines and drawn looks

# how strong the edge is at a place (a sobel filter on the brightness or on every color), stride is the distance to the neighbors in pixels
SOBEL = """
vec3 sobel_sample(vec2 p, bool lum) {
    vec3 s = prev(p).rgb;
    return lum ? vec3(luma(s)) : s;
}

vec3 sobel_rgb(vec2 uv, float stride, bool lum) {
    vec2 t = max(1.0, stride) / u_resolution;
    vec3 ul = sobel_sample(uv + t * vec2(-1.0, 1.0), lum);
    vec3 u = sobel_sample(uv + t * vec2(0.0, 1.0), lum);
    vec3 ur = sobel_sample(uv + t * vec2(1.0, 1.0), lum);
    vec3 l = sobel_sample(uv + t * vec2(-1.0, 0.0), lum);
    vec3 r = sobel_sample(uv + t * vec2(1.0, 0.0), lum);
    vec3 dl = sobel_sample(uv + t * vec2(-1.0, -1.0), lum);
    vec3 d = sobel_sample(uv + t * vec2(0.0, -1.0), lum);
    vec3 dr = sobel_sample(uv + t * vec2(1.0, -1.0), lum);
    vec3 gx = -1.0 * ul + 1.0 * ur + -2.0 * l + 2.0 * r + -1.0 * dl + 1.0 * dr;
    vec3 gy = 1.0 * ul + 2.0 * u + 1.0 * ur + -1.0 * dl - 2.0 * d - 1.0 * dr;
    return sqrt(gx * gx + gy * gy);
}

float sobel_luma(vec2 uv, float stride) { return sobel_rgb(uv, stride, true).x; }
"""

add('edge', 'edges', 'finds the edges in the picture and draws them (the picture itself can stay or go)', [
    C('method', 'sobel', ['sobel', 'prewitt', 'scharr', 'roberts', 'laplacian'], 'how edges are found: sobel is the usual, prewitt is a bit rougher, scharr is exact on diagonals, roberts is thin, laplacian finds lines'),
    C('source', 'luma', ['luma', 'color'], 'luma finds edges of brightness only, color also finds edges between colors of the same brightness'),
    F('strength', 2.0, 0, 20, 'how strong the edges are'),
    F('threshold', 0.0, 0, 1, 'edges weaker than this are not drawn (0 draws all of them, even faint ones)'),
    F('softness', 0.0, 0, 1, 'how soft the cut at the threshold is'),
    RGB('color', (1.0, 1.0, 1.0), 'the color of the edges'),
    RGB('background', (0.0, 0.0, 0.0), 'the color where there is no edge'),
    F('keep', 0.0, 0, 1, 'how much of the picture itself shows where there is no edge (1 draws the edges over the picture)'),
    F('width', 1.0, 0.5, 8, 'how wide the edges are (pixels, measured on a screen 1080 high, never thinner than one pixel)'),
    F('skip_bright', 1.0, 0, 1, 'parts brighter than this are left as they are (1 skips nothing)'),
], """
vec3 edge_sample(vec2 uv, vec2 off) {
    vec3 s = prev(uv + off).rgb;
    return (u_source == SOURCE_LUMA) ? vec3(luma(s)) : s;
}

vec4 fx(vec4 c, vec2 uv) {
    float m = max(max(c.r, c.g), c.b);
    if (m > u_skip_bright) return c;

    vec2 t = max(1.0, u_width * PX) / u_resolution;
    vec3 ul = edge_sample(uv, t * vec2(-1.0, 1.0));
    vec3 u = edge_sample(uv, t * vec2(0.0, 1.0));
    vec3 ur = edge_sample(uv, t * vec2(1.0, 1.0));
    vec3 l = edge_sample(uv, t * vec2(-1.0, 0.0));
    vec3 ce = edge_sample(uv, vec2(0.0));
    vec3 r = edge_sample(uv, t * vec2(1.0, 0.0));
    vec3 dl = edge_sample(uv, t * vec2(-1.0, -1.0));
    vec3 d = edge_sample(uv, t * vec2(0.0, -1.0));
    vec3 dr = edge_sample(uv, t * vec2(1.0, -1.0));
    vec3 gx;
    vec3 gy;

    if (u_method == METHOD_SOBEL) {
        gx = -1.0 * ul + 1.0 * ur + -2.0 * l + 2.0 * r + -1.0 * dl + 1.0 * dr;
        gy = 1.0 * ul + 2.0 * u + 1.0 * ur + -1.0 * dl - 2.0 * d - 1.0 * dr;
    } else if (u_method == METHOD_PREWITT) {
        gx = -ul + ur - l + r - dl + dr;
        gy = ul + u + ur - dl - d - dr;
    } else if (u_method == METHOD_SCHARR) {
        gx = (-3.0 * ul + 3.0 * ur - 10.0 * l + 10.0 * r - 3.0 * dl + 3.0 * dr) * 0.25;
        gy = (3.0 * ul + 10.0 * u + 3.0 * ur - 3.0 * dl - 10.0 * d - 3.0 * dr) * 0.25;
    } else if (u_method == METHOD_ROBERTS) {
        gx = (ce - dr) * 2.0;
        gy = (r - d) * 2.0;
    } else {
        gx = (4.0 * ce - u - d - l - r) * 2.0;
        gy = vec3(0.0);
    }

    vec3 mag = sqrt(gx * gx + gy * gy);
    float e = (u_source == SOURCE_LUMA) ? mag.x : max(mag.r, max(mag.g, mag.b));
    e *= u_strength;
    if (u_threshold > 0.0) e = smoothstep(u_threshold, u_threshold + u_softness + 0.0001, e);

    vec3 base = mix(u_background, c.rgb, u_keep);
    return vec4(mix(base, u_color, clamp(e, 0.0, 1.0)), 1.0);
}
""")

alias('outline', 'edge', 'dark lines drawn over the picture where things end', strength=3.0, threshold=0.3, softness=0.3, color=(0.0, 0.0, 0.0), keep=1.0, width=1.5)

add('toon', 'edges', 'a cartoon look: flat steps of color and black outlines (cel shading)', [
    I('levels', 4, 2, 12, 'how many steps of brightness'),
    F('softness', 0.1, 0, 1, 'how soft the steps are'),
    F('saturation', 1.2, 0, 3, 'makes the colors stronger'),
    F('edge', 3.0, 0, 20, 'how strong the outlines are'),
    F('width', 1.5, 0.5, 8, 'how wide the outlines are (pixels, measured on a screen 1080 high)'),
    RGB('edge_color', (0.0, 0.0, 0.0), 'the color of the outlines'),
], SOBEL + """
vec4 fx(vec4 c, vec2 uv) {
    vec3 hsv = rgb2hsv(clamp(c.rgb, 0.0, 1.0));
    float n = float(u_levels);
    float v = hsv.z * n;
    float band = floor(v);
    float h = 0.5 * u_softness;
    hsv.z = (band + smoothstep(0.5 - h, 0.5 + h + 0.0001, v - band)) / n;
    hsv.y = clamp(hsv.y * u_saturation, 0.0, 1.0);
    vec3 col = hsv2rgb(hsv);

    float line = smoothstep(0.35, 0.8, sobel_luma(uv, u_width * PX) * u_edge);
    return vec4(mix(col, u_edge_color, line), 1.0);
}
""")

add('emboss', 'edges', 'makes the picture look like it is stamped in metal or stone', [
    F('strength', 2.0, 0, 10, 'how deep'),
    F('angle', 135.0, -180, 180, 'the direction the light comes from'),
    F('depth', 1.0, 0.5, 6, 'how thick the relief is (pixels, measured on a screen 1080 high)'),
    C('mode', 'grey', ['grey', 'color'], 'grey is only the relief, color puts the relief on the picture'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 d = vec2(cos(radians(u_angle)), sin(radians(u_angle))) * max(1.0, u_depth * PX) / u_resolution;
    vec3 a = prev(uv + d).rgb;
    vec3 b = prev(uv - d).rgb;
    float diff = (luma(a) - luma(b)) * u_strength;
    if (u_mode == MODE_COLOR) return vec4(c.rgb + diff, 1.0);
    return vec4(vec3(0.5 + diff), 1.0);
}
""")

add('sketch', 'edges', 'a pencil drawing on paper: lines where things end and light hatching in the dark', [
    F('lines', 3.0, 0, 10, 'how strong the lines are'),
    F('hatch', 0.6, 0, 1, 'how much shading (hatching) there is in the dark parts'),
    F('width', 1.0, 0.5, 6, 'how wide the lines are (pixels, measured on a screen 1080 high)'),
    RGB('paper', (0.96, 0.94, 0.88), 'the color of the paper'),
    RGB('ink', (0.12, 0.12, 0.18), 'the color of the pencil'),
    F('color', 0.0, 0, 1, 'how much of the colors of the picture shows through (0 is a pure drawing)'),
], SOBEL + """
vec4 fx(vec4 c, vec2 uv) {
    float line = clamp(sobel_luma(uv, u_width * PX) * u_lines, 0.0, 1.0);
    float dark = 1.0 - luma(c.rgb);
    vec2 f = gl_FragCoord.xy / PX;
    float h1 = abs(fract((f.x + f.y) / 5.0) - 0.5) * 2.0;
    float h2 = abs(fract((f.x - f.y) / 5.0) - 0.5) * 2.0;
    float hatch = max((1.0 - smoothstep(0.0, 0.3, h1)) * smoothstep(0.25, 0.45, dark), (1.0 - smoothstep(0.0, 0.3, h2)) * smoothstep(0.55, 0.75, dark)) * u_hatch;
    float ink = clamp(max(line, hatch), 0.0, 1.0);
    vec3 paper = u_paper * mix(vec3(1.0), c.rgb * 1.2 + 0.1, u_color);
    return vec4(mix(paper, u_ink, ink), 1.0);
}
""")

add('halftone', 'edges', 'dots of different size, like print in a newspaper or a comic (gray ink, 4 inks, or red green blue)', [
    C('type', 'cmyk', ['gray', 'cmyk', 'rgb'], 'gray is one ink, cmyk is the 4 inks of a printer (cyan, magenta, yellow, black), rgb is light dots on black'),
    F('size', 9.0, 3, 40, 'the distance between dots (pixels, measured on a screen 1080 high)'),
    F('angle', 0.0, -90, 90, 'turns all the dot grids'),
    F('softness', 0.2, 0, 1, 'how soft the dots are'),
    RGB('paper', (0.98, 0.97, 0.93), 'the color of the paper (gray and cmyk)'),
    RGB('ink', (0.05, 0.05, 0.1), 'the color of the ink (gray)'),
], """
struct Dot { vec3 col; float dist; };

Dot halftone_dot(vec2 f, float ang, float cs) {
    mat2 m = rot2(ang);
    vec2 p = m * f;
    vec2 center = (floor(p / cs) + 0.5) * cs;
    vec2 sp = transpose(m) * center;
    Dot d;
    d.col = prev(clamp(sp / u_resolution, 0.0, 1.0)).rgb;
    d.dist = length(p - center);
    return d;
}

float dot_mask(float dist, float cs, float amount) {
    float aa = max(0.7, u_softness * cs * 0.5);
    float r = sqrt(clamp(amount, 0.0, 1.0)) * (0.7071 * cs + aa);
    return (1.0 - smoothstep(r - aa, r + aa, dist)) * smoothstep(0.0, 0.04, amount);
}

vec4 fx(vec4 c, vec2 uv) {
    float cs = max(3.0, u_size * PX);
    vec2 f = gl_FragCoord.xy;
    float base = radians(u_angle);

    if (u_type == TYPE_GRAY) {
        Dot d = halftone_dot(f, base + radians(45.0), cs);
        return vec4(mix(u_paper, u_ink, dot_mask(d.dist, cs, 1.0 - luma(d.col))), 1.0);
    }

    if (u_type == TYPE_RGB) {
        vec3 res = vec3(0.0);
        for (int k = 0; k < 3; k++) {
            float ang = k == 0 ? 15.0 : (k == 1 ? 75.0 : 0.0);
            Dot d = halftone_dot(f, base + radians(ang), cs);
            res[k] = dot_mask(d.dist, cs, d.col[k]);
        }
        return vec4(res, 1.0);
    }

    vec3 inks[4] = vec3[4](vec3(0.0, 0.68, 0.94), vec3(0.93, 0.0, 0.55), vec3(1.0, 0.95, 0.0), vec3(0.08, 0.08, 0.1));
    vec3 res = u_paper;
    for (int k = 0; k < 4; k++) {
        float ang = k == 0 ? 15.0 : (k == 1 ? 75.0 : (k == 2 ? 0.0 : 45.0));
        Dot d = halftone_dot(f, base + radians(ang), cs);
        float key = 1.0 - max(d.col.r, max(d.col.g, d.col.b));
        vec3 cmy = (1.0 - d.col - key) / max(1.0 - key, 0.001);
        float amount = (k == 0 ? cmy.x : (k == 1 ? cmy.y : (k == 2 ? cmy.z : key * 0.6))) * 0.9;
        res *= mix(vec3(1.0), inks[k], dot_mask(d.dist, cs, amount));
    }
    return vec4(res, 1.0);
}
""")

add('crosshatch', 'edges', 'a pen drawing: the darker, the more crossing lines', [
    F('spacing', 9.0, 3, 40, 'the distance between lines (pixels, measured on a screen 1080 high)'),
    F('thickness', 0.3, 0.05, 0.9, 'how thick the lines are (a part of the spacing)'),
    I('layers', 4, 1, 4, 'how many directions of lines (every one starts in a darker place)'),
    F('lightness', 0.85, 0, 1, 'the brightness where the first lines start (higher draws lines almost everywhere)'),
    F('angle', 0.0, -90, 90, 'turns all the lines'),
    RGB('paper', (0.96, 0.94, 0.88), 'the color of the paper'),
    RGB('ink', (0.1, 0.1, 0.15), 'the color of the ink'),
    F('color', 0.0, 0, 1, 'how much of the colors of the picture shows through'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float l = clamp(luma(c.rgb), 0.0, 1.0);
    vec2 f = gl_FragCoord.xy / PX;
    float sp = max(2.0, u_spacing);
    float a = radians(u_angle);
    float ink = 0.0;
    float angles[4] = float[4](0.785398, -0.785398, 0.0, 1.570796);

    for (int k = 0; k < 4; k++) {
        if (k >= u_layers) break;
        float ang = a + angles[k];
        float coord = dot(f, vec2(cos(ang), sin(ang))) / sp;
        float line = abs(fract(coord) - 0.5) * 2.0;
        float aa = 1.0 / sp;
        float mask = 1.0 - smoothstep(u_thickness - aa, u_thickness + aa, line);
        float t = u_lightness - float(k) * 0.2;
        ink = max(ink, mask * smoothstep(t, t - 0.1, l));
    }

    vec3 paper = u_paper * mix(vec3(1.0), c.rgb * 1.2 + 0.1, u_color);
    return vec4(mix(paper, u_ink, ink), 1.0);
}
""")

add('stipple', 'edges', 'a drawing made of dots: the darker the part, the bigger and closer the dots', [
    F('size', 8.0, 3, 40, 'the distance between dots (pixels, measured on a screen 1080 high)'),
    F('dot', 0.9, 0.2, 1.5, 'how big the biggest dots are'),
    F('jitter', 0.8, 0, 1, 'how much the dots are moved off a grid (0 is a grid, 1 is random)'),
    RGB('paper', (0.96, 0.94, 0.88), 'the color of the paper'),
    RGB('ink', (0.1, 0.1, 0.15), 'the color of the dots'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float cs = max(3.0, u_size * PX);
    vec2 f = gl_FragCoord.xy;
    vec2 cell = floor(f / cs);
    float cover = 0.0;

    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            vec2 cc = cell + vec2(float(i), float(j));
            vec2 rnd = hash22(cc + float(u_seed) * 7.13);
            vec2 center = (cc + 0.5 + (rnd - 0.5) * u_jitter) * cs;
            vec3 col = prev(clamp(center / u_resolution, 0.0, 1.0)).rgb;
            float dark = 1.0 - clamp(luma(col), 0.0, 1.0);
            float r = u_dot * 0.5 * cs * sqrt(dark);
            float m = 1.0 - smoothstep(r - 0.7, r + 0.7, length(f - center));
            cover = max(cover, m * smoothstep(0.0, 0.05, dark));
        }
    }

    return vec4(mix(u_paper, u_ink, cover), 1.0);
}
""", seeded=True)

add('neon', 'edges', 'the edges of everything glow in the colors of the picture, on a dark picture', [
    F('gain', 3.0, 0, 10, 'how bright the glowing lines are'),
    F('width', 1.5, 0.5, 8, 'how wide the lines are (pixels, measured on a screen 1080 high)'),
    F('glow', 0.8, 0, 2, 'how strong the soft glow around the lines is'),
    F('dim', 0.1, 0, 1, 'how much of the picture itself stays'),
    F('saturation', 1.8, 0, 3, 'how vivid the colors of the lines are'),
], SOBEL + """
vec4 fx(vec4 c, vec2 uv) {
    float st = max(1.0, u_width * PX);
    vec3 e = sobel_rgb(uv, st, false) + sobel_rgb(uv, st * 3.0, false) * u_glow * 0.6;
    e *= u_gain;
    e = mix(vec3(luma(e)), e, u_saturation);
    return vec4(c.rgb * u_dim + e, 1.0);
}
""")

add('thermal', 'edges', 'false colors by brightness, like a heat camera', [
    C('palette', 'iron', ['iron', 'rainbow', 'viridis', 'magma'], 'the colors'),
    F('contrast', 1.2, 0.2, 4, 'how much the brightness is spread out'),
    F('offset', 0.0, -1, 1, 'moves everything towards hot (positive) or cold (negative)'),
    B('invert', False, 'hot is dark and cold is light'),
], """
const vec3 STOPS[18] = vec3[18](
    vec3(0.0, 0.0, 0.0), vec3(0.1, 0.0, 0.4), vec3(0.6, 0.0, 0.5), vec3(0.95, 0.25, 0.1), vec3(1.0, 0.75, 0.0), vec3(1.0, 1.0, 0.9),
    vec3(0.267, 0.005, 0.329), vec3(0.230, 0.322, 0.546), vec3(0.128, 0.567, 0.551), vec3(0.267, 0.749, 0.441), vec3(0.633, 0.848, 0.228), vec3(0.993, 0.906, 0.144),
    vec3(0.001, 0.0, 0.014), vec3(0.232, 0.059, 0.437), vec3(0.550, 0.161, 0.506), vec3(0.868, 0.288, 0.409), vec3(0.987, 0.536, 0.382), vec3(0.987, 0.991, 0.749)
);

vec3 stops(int base, float t) {
    float x = clamp(t, 0.0, 1.0) * 5.0;
    int i = min(int(floor(x)), 4);
    return mix(STOPS[base + i], STOPS[base + i + 1], x - float(i));
}

vec4 fx(vec4 c, vec2 uv) {
    float t = clamp((luma(c.rgb) - 0.5) * u_contrast + 0.5 + u_offset, 0.0, 1.0);
    if (u_invert == 1) t = 1.0 - t;
    vec3 col;
    if (u_palette == PALETTE_IRON) col = stops(0, t);
    else if (u_palette == PALETTE_RAINBOW) col = hsv2rgb(vec3((1.0 - t) * 0.7, 1.0, 1.0));
    else if (u_palette == PALETTE_VIRIDIS) col = stops(6, t);
    else col = stops(12, t);
    return vec4(col, 1.0);
}
""")

add('nightvision', 'edges', 'night vision goggles: everything amplified and green, with noise and dark corners', [
    F('gain', 3.0, 0.2, 10, 'how much the light is amplified'),
    RGB('tint', (0.25, 1.0, 0.35), 'the color of the screen'),
    F('noise', 0.25, 0, 1, 'how much noise'),
    F('vignette', 0.8, 0, 1, 'how dark the corners are (goggles)'),
    F('radius', 0.55, 0.2, 1.2, 'how far from the middle it starts getting dark (a part of the screen height)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = floor(u_time * 30.0) + float(u_seed);
    float l = 1.0 - exp(-luma(c.rgb) * u_gain);
    l += (hash12(gl_FragCoord.xy + t * 17.0) - 0.5) * u_noise;
    vec3 col = u_tint * clamp(l, 0.0, 1.2);
    float v = 1.0 - smoothstep(u_radius, u_radius + 0.25, length(centered(uv)));
    return vec4(col * mix(1.0, v, u_vignette), 1.0);
}
""", animated=True, seeded=True)

add('xray', 'edges', 'an x-ray picture: light and dark swap and everything is blue-white', [
    F('contrast', 1.5, 0.2, 4, 'how much the brightness is spread out'),
    RGB('tint', (0.55, 0.85, 1.0), 'the color of the film'),
    F('edges', 1.5, 0, 5, 'how strong the bright outlines are'),
], SOBEL + """
vec4 fx(vec4 c, vec2 uv) {
    float l = clamp((1.0 - luma(c.rgb) - 0.5) * u_contrast + 0.5, 0.0, 1.0);
    float e = sobel_luma(uv, PX) * u_edges;
    return vec4(u_tint * (l * 0.8 + e), 1.0);
}
""")

add('infrared', 'edges', 'an infrared photo: leaves glow white (or red) and the sky goes dark', [
    F('foliage', 1.0, 0, 1, 'how much plants glow'),
    C('look', 'mono', ['mono', 'color'], 'mono is a black and white photo, color is false color film (plants turn red)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec3 hsv = rgb2hsv(clamp(c.rgb, 0.0, 1.0));
    float h = hsv.x * 360.0;
    float leaf = smoothstep(50.0, 90.0, h) * (1.0 - smoothstep(160.0, 200.0, h)) * smoothstep(0.1, 0.3, hsv.y);
    float sky = smoothstep(190.0, 220.0, h) * (1.0 - smoothstep(250.0, 280.0, h));
    float ir = luma(c.rgb);
    ir = mix(ir, 1.0, leaf * u_foliage);
    ir = mix(ir, ir * 0.35, sky);
    if (u_look == LOOK_MONO) return vec4(vec3(ir), 1.0);
    return vec4(ir, c.r * 0.6 + ir * 0.2, c.g * 0.5 + c.b * 0.1 + ir * 0.1, 1.0);
}
""")
