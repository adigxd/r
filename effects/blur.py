from .base import add, alias, F, I, B, C, RGB, PT

# blur, sharpen and glow

# a blur along one direction; TAP(p) is what is read at a place (defined by the effect before this is used)
BLUR1D = """
vec3 blur1d(vec2 dir, float radius, bool box) {
    const int TAPS = 10;
    float stride = radius / float(TAPS);
    vec3 sum = vec3(0.0);
    float total = 0.0;

    for (int i = -TAPS; i <= TAPS; i++) {
        float x = float(i) * stride;
        float w = box ? 1.0 : exp(-0.5 * pow(2.0 * float(i) / float(TAPS), 2.0));
        sum += TAP(v_uv + dir * x / u_resolution) * w;
        total += w;
    }

    return sum / total;
}
"""

# a round blur with a spiral of samples
DISC = """
vec3 disc_blur(vec2 uv, float radius, int samples) {
    vec3 sum = prev(uv).rgb;
    float total = 1.0;

    for (int i = 1; i < 64; i++) {
        if (i >= samples) break;
        float r = sqrt(float(i) / float(samples)) * radius;
        float a = float(i) * 2.39996323;
        sum += prev(uv + vec2(cos(a), sin(a)) * r / u_resolution).rgb;
        total += 1.0;
    }

    return sum / total;
}
"""

TAP_PREV = '#define TAP(p) texture(u_prev, p).rgb\n'

add('blur', 'blur', 'blurs the picture (a smooth gaussian blur or a flat box blur)', [
    F('radius', 6.0, 0, 100, 'how far the blur reaches (measured on a screen 1080 high)'),
    C('type', 'gaussian', ['gaussian', 'box'], 'gaussian is smooth, box is flat and a bit blocky'),
    F('x', 1.0, 0, 1, 'how much of the blur goes sideways'),
    F('y', 1.0, 0, 1, 'how much of the blur goes up and down'),
], passes=[
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) { return vec4(blur1d(vec2(1.0, 0.0), u_radius * u_x * PX, u_type == TYPE_BOX), 1.0); }
""",
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) { return vec4(blur1d(vec2(0.0, 1.0), u_radius * u_y * PX, u_type == TYPE_BOX), 1.0); }
"""])

add('zoomblur', 'blur', 'a blur that streaks away from a point, like speed', [
    F('strength', 0.15, -1, 1, 'how long the streaks are (negative: the other way)'),
    PT('center', (0.5, 0.5), 'the point they come from'),
    I('samples', 24, 4, 64, 'how smooth (more is slower)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 d = uv - u_center;
    vec3 sum = vec3(0.0);

    for (int i = 0; i < 64; i++) {
        if (i >= u_samples) break;
        float t = float(i) / float(max(u_samples - 1, 1));
        sum += prev(uv - d * t * u_strength).rgb;
    }

    return vec4(sum / float(u_samples), 1.0);
}
""")

add('spinblur', 'blur', 'a blur that turns around a point', [
    F('angle', 8.0, -90, 90, 'how many degrees it turns over'),
    PT('center', (0.5, 0.5), 'the point it turns around'),
    I('samples', 24, 4, 64, 'how smooth (more is slower)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 p = centered(uv) - centered(u_center);
    vec3 sum = vec3(0.0);

    for (int i = 0; i < 64; i++) {
        if (i >= u_samples) break;
        float t = float(i) / float(max(u_samples - 1, 1)) - 0.5;
        vec2 q = rot2(radians(u_angle) * t) * p + centered(u_center);
        sum += prev(uncentered(q)).rgb;
    }

    return vec4(sum / float(u_samples), 1.0);
}
""")

add('directionalblur', 'blur', 'a blur in one direction, like a camera that moved', [
    F('distance', 24.0, 0, 200, 'how long the streaks are (pixels, measured on a screen 1080 high)'),
    F('angle', 0.0, -180, 180, 'the direction of the streaks'),
    I('samples', 24, 4, 64, 'how smooth (more is slower)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 dir = vec2(cos(radians(u_angle)), sin(radians(u_angle))) * u_distance * PX / u_resolution;
    vec3 sum = vec3(0.0);

    for (int i = 0; i < 64; i++) {
        if (i >= u_samples) break;
        float t = float(i) / float(max(u_samples - 1, 1)) - 0.5;
        sum += prev(uv + dir * t).rgb;
    }

    return vec4(sum / float(u_samples), 1.0);
}
""")

add('tiltshift', 'blur', 'only a strip of the picture is sharp, the rest is blurred (makes everything look like a toy model)', [
    F('position', 0.5, 0, 1, 'where the sharp strip is (0 bottom, 1 top)'),
    F('width', 0.12, 0, 1, 'how wide the sharp strip is (a part of the screen height)'),
    F('falloff', 0.25, 0.01, 1, 'how slowly it goes from sharp to blurred'),
    F('radius', 12.0, 0, 60, 'how blurred the far parts are (pixels, measured on a screen 1080 high)'),
    F('angle', 0.0, -90, 90, 'turns the strip'),
    F('saturation', 1.3, 0, 3, 'makes the colors stronger, like a painted model'),
    I('samples', 32, 8, 64, 'how smooth (more is slower)'),
], DISC + """
vec4 fx(vec4 c, vec2 uv) {
    float a = radians(u_angle);
    float d = abs(dot(centered(uv) - vec2(0.0, u_position - 0.5), vec2(-sin(a), cos(a))));
    float amount = smoothstep(u_width, u_width + u_falloff, d);
    float r = amount * u_radius * PX;
    vec3 col = r < 0.5 ? c.rgb : disc_blur(uv, r, u_samples);
    return vec4(mix(vec3(luma(col)), col, u_saturation), 1.0);
}
""")

add('sharpen', 'blur', 'makes small details crisper', [
    F('amount', 1.0, 0, 5, 'how much'),
    F('radius', 1.0, 0.5, 4, 'how big the details are (pixels, measured on a screen 1080 high)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 t = max(0.5, u_radius * PX) / u_resolution;
    vec3 avg = (prev(uv + vec2(t.x, 0.0)).rgb + prev(uv - vec2(t.x, 0.0)).rgb + prev(uv + vec2(0.0, t.y)).rgb + prev(uv - vec2(0.0, t.y)).rgb) * 0.25;
    return vec4(c.rgb + (c.rgb - avg) * u_amount, 1.0);
}
""")

add('unsharp', 'blur', 'makes the picture crisper by adding back what a blur takes away (an unsharp mask)', [
    F('radius', 6.0, 1, 60, 'how big the details are (pixels, measured on a screen 1080 high)'),
    F('amount', 1.0, 0, 5, 'how much'),
    F('threshold', 0.0, 0, 0.5, 'leaves differences smaller than this alone (keeps noise down)'),
    B('luma_only', False, 'only the brightness is sharpened, the colors stay as they are'),
    I('samples', 24, 8, 64, 'how smooth (more is slower)'),
], DISC + """
vec4 fx(vec4 c, vec2 uv) {
    vec3 d = c.rgb - disc_blur(uv, u_radius * PX, u_samples);
    if (u_luma_only == 1) d = vec3(luma(d));
    d *= smoothstep(0.0, max(u_threshold, 0.0001), length(d));
    return vec4(c.rgb + d * u_amount, 1.0);
}
""")

alias('clarity', 'unsharp', 'adds punch to the middle tones (a big, gentle unsharp mask on the brightness)', radius=30.0, amount=0.8, luma_only=True)

BLOOM_BRIGHT = """
vec3 bright_part(vec3 c) {
    float l = max(max(c.r, c.g), c.b);
    float soft = clamp(l - u_threshold + u_knee, 0.0, 2.0 * u_knee + 0.0001);
    soft = soft * soft / (4.0 * u_knee + 0.0001);
    float contrib = max(soft, l - u_threshold) / max(l, 0.0001);
    return c * contrib;
}
"""

BLOOM_PARAMS = [
    F('threshold', 0.7, 0, 1, 'how bright something has to be to glow'),
    F('knee', 0.3, 0, 1, 'how soft the start of the glow is'),
    F('intensity', 1.0, 0, 5, 'how strong the glow is'),
    F('radius', 16.0, 1, 150, 'how far the glow reaches (pixels, measured on a screen 1080 high)'),
    RGB('tint', (1.0, 1.0, 1.0), 'the color of the glow'),
    C('mode', 'screen', ['add', 'screen'], 'how the glow goes over the picture (screen cannot go past white)'),
]

add('bloom', 'blur', 'bright parts glow into the dark around them', BLOOM_PARAMS, passes=[
    '#define TAP(p) bright_part(texture(u_prev, p).rgb)\n' + BLOOM_BRIGHT + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) { return vec4(blur1d(vec2(1.0, 0.0), u_radius * 0.5 * PX, false), 1.0); }
""",
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) { return vec4(blur1d(vec2(0.0, 1.0), u_radius * 0.5 * PX, false), 1.0); }
""",
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) { return vec4(blur1d(vec2(1.0, 0.0), u_radius * PX, false), 1.0); }
""",
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) {
    vec3 glow = blur1d(vec2(0.0, 1.0), u_radius * PX, false) * u_tint * u_intensity;
    vec3 base = src(uv).rgb;
    return vec4(u_mode == MODE_ADD ? base + glow : 1.0 - (1.0 - base) * (1.0 - clamp(glow, 0.0, 1.0)), 1.0);
}
"""])

alias('glow', 'bloom', 'the whole picture glows softly, not only the bright parts', threshold=0.0, knee=0.5, intensity=0.6, radius=24.0)
alias('halation', 'bloom', 'a red-orange glow around bright parts, like film', threshold=0.75, knee=0.2, intensity=1.2, radius=26.0, tint=(1.0, 0.35, 0.15), mode='add')

add('softfocus', 'blur', 'a dreamy soft picture that still has its details', [
    F('radius', 8.0, 1, 80, 'how soft (pixels, measured on a screen 1080 high)'),
    F('strength', 0.6, 0, 1, 'how much of the blurred picture is mixed in'),
    F('glow', 0.25, 0, 1, 'how much the light parts glow'),
], passes=[
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) { return vec4(blur1d(vec2(1.0, 0.0), u_radius * PX, false), 1.0); }
""",
    TAP_PREV + BLUR1D + """
vec4 fx(vec4 c, vec2 uv) {
    vec3 blurred = blur1d(vec2(0.0, 1.0), u_radius * PX, false);
    vec3 col = mix(src(uv).rgb, blurred, u_strength);
    return vec4(1.0 - (1.0 - col) * (1.0 - clamp(blurred * u_glow, 0.0, 1.0)), 1.0);
}
"""])

add('median', 'blur', 'every pixel becomes the middle value of its neighbors: noise and small details vanish, edges stay (a painted look)', [
    F('radius', 1.0, 1, 6, 'how far the neighbors are (pixels, measured on a screen 1080 high)'),
], """
#define s2(a, b) temp = a; a = min(a, b); b = max(temp, b);
#define mn3(a, b, c) s2(a, b); s2(a, c);
#define mx3(a, b, c) s2(b, c); s2(a, c);
#define mnmx3(a, b, c) mx3(a, b, c); s2(a, b);
#define mnmx4(a, b, c, d) s2(a, b); s2(c, d); s2(a, c); s2(b, d);
#define mnmx5(a, b, c, d, e) s2(a, b); s2(c, d); mn3(a, c, e); mx3(b, d, e);
#define mnmx6(a, b, c, d, e, f) s2(a, d); s2(b, e); s2(c, f); mn3(a, b, c); mx3(d, e, f);

vec4 fx(vec4 c, vec2 uv) {
    vec2 t = max(1.0, u_radius * PX) / u_resolution;
    vec3 v[9];
    vec3 temp;

    for (int i = 0; i < 9; i++) {
        vec2 o = vec2(float(i % 3) - 1.0, float(i / 3) - 1.0);
        v[i] = prev(uv + o * t).rgb;
    }

    mnmx6(v[0], v[1], v[2], v[3], v[4], v[5]);
    mnmx5(v[1], v[2], v[3], v[4], v[6]);
    mnmx4(v[2], v[3], v[4], v[7]);
    mnmx3(v[3], v[4], v[8]);
    return vec4(v[4], 1.0);
}
""")

add('kuwahara', 'blur', 'a painted look: flat patches of color with sharp edges between them (a Kuwahara filter)', [
    I('radius', 3, 1, 8, 'the size of the patches (pixels, measured on a screen 1080 high)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 t = max(1.0, floor(PX + 0.5)) / u_resolution;
    vec3 mean[4];
    float spread[4];

    for (int k = 0; k < 4; k++) {
        vec2 dir = vec2((k % 2 == 0) ? -1.0 : 1.0, (k < 2) ? -1.0 : 1.0);
        vec3 sum = vec3(0.0);
        vec3 sumsq = vec3(0.0);
        float n = 0.0;

        for (int j = 0; j <= 8; j++) {
            if (j > u_radius) break;
            for (int i = 0; i <= 8; i++) {
                if (i > u_radius) break;
                vec3 s = prev(uv + dir * vec2(float(i), float(j)) * t).rgb;
                sum += s;
                sumsq += s * s;
                n += 1.0;
            }
        }

        mean[k] = sum / n;
        vec3 var = sumsq / n - mean[k] * mean[k];
        spread[k] = var.r + var.g + var.b;
    }

    vec3 best = mean[0];
    float least = spread[0];
    for (int k = 1; k < 4; k++) {
        if (spread[k] < least) { least = spread[k]; best = mean[k]; }
    }

    return vec4(best, 1.0);
}
""")
