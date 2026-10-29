from .base import add, alias, F, I, B, C, RGB, PT, BLEND

# things drawn over the picture

add('vignette', 'overlay', 'the corners of the picture get dark', [
    F('amount', 0.6, 0, 1, 'how dark the corners get'),
    F('radius', 0.5, 0, 1.5, 'how far from the middle it starts getting dark (1 is the corner)'),
    F('softness', 0.6, 0.01, 1.5, 'how slowly it gets dark'),
    F('roundness', 0.5, 0, 1, '1 is a round vignette, 0 follows the shape of the screen'),
    RGB('color', (0.0, 0.0, 0.0), 'the color of the corners'),
    PT('center', (0.5, 0.5), 'the middle'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = (uv - u_center) * 2.0;
    vec2 shape = vec2(mix(1.0, ASPECT, u_roundness), 1.0);
    float d = length(q * shape) / length(shape);
    return vec4(mix(c.rgb, u_color, smoothstep(u_radius, u_radius + u_softness, d) * u_amount), 1.0);
}
""")

add('grain', 'overlay', 'film grain', [
    F('amount', 0.15, 0, 1, 'how strong'),
    F('size', 1.5, 1, 8, 'the size of the grains (pixels, measured on a screen 1080 high)'),
    F('rate', 24.0, 0, 120, 'how many times a second the grain changes (0 keeps it still)'),
    B('midtones', True, 'more grain in the middle tones, less in the very dark and light'),
    B('colored', False, 'every color on its own, like color film'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float frame = floor(u_time * u_rate) + float(u_seed);
    vec2 cell = floor(gl_FragCoord.xy / max(1.0, u_size * PX)) + frame * 61.7;
    vec3 g = vec3(hash12(cell) - 0.5);
    if (u_colored == 1) g = vec3(hash12(cell) - 0.5, hash12(cell + 19.1) - 0.5, hash12(cell + 47.3) - 0.5);
    float w = (u_midtones == 1) ? 1.0 - pow(abs(luma(c.rgb) * 2.0 - 1.0), 2.0) : 1.0;
    return vec4(c.rgb + g * u_amount * 2.0 * w, 1.0);
}
""", animated=True, seeded=True)

add('static', 'overlay', 'the snow of a tv without a signal', [
    F('amount', 0.35, 0, 1, 'how much of the picture is replaced by static'),
    F('size', 2.0, 1, 16, 'the size of the specks (pixels, measured on a screen 1080 high)'),
    F('rate', 60.0, 0, 240, 'how many times a second the static changes'),
    B('colored', False, 'colored static'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float frame = floor(u_time * u_rate) + float(u_seed);
    vec2 cell = floor(gl_FragCoord.xy / max(1.0, u_size * PX)) + frame * 61.7;
    vec3 s = vec3(hash12(cell));
    if (u_colored == 1) s = vec3(hash12(cell), hash12(cell + 19.1), hash12(cell + 47.3));
    return vec4(mix(c.rgb, s, u_amount), 1.0);
}
""", animated=True, seeded=True)

add('letterbox', 'overlay', 'black bars above and below (or left and right) so the picture has the shape of a film', [
    F('ratio', 2.35, 0.5, 6, 'the shape of the picture: width divided by height (2.35 is a wide film, 1.33 is an old tv)'),
    F('softness', 0.0, 0, 60, 'how soft the edge of the bars is (pixels, measured on a screen 1080 high)'),
    RGB('color', (0.0, 0.0, 0.0), 'the color of the bars'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv);
    float dy = abs(q.y) - 0.5 * min(1.0, ASPECT / u_ratio);
    float dx = abs(q.x) - 0.5 * min(ASPECT, u_ratio);
    float aa = max(u_softness * PX, 1.0) / u_resolution.y;
    return vec4(mix(c.rgb, u_color, smoothstep(-0.5 * aa, 0.5 * aa, max(dx, dy))), 1.0);
}
""")

add('border', 'overlay', 'a frame around the picture', [
    F('width', 20.0, 0, 400, 'the width of the frame (pixels, measured on a screen 1080 high)'),
    RGB('color', (1.0, 1.0, 1.0), 'the color of the frame'),
    C('style', 'solid', ['solid', 'double', 'fade'], 'solid is a plain frame, double is two thin lines, fade is a soft glow from the edge'),
    F('opacity', 1.0, 0, 1, 'how much of the frame is seen'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 px = gl_FragCoord.xy;
    float d = min(min(px.x, u_resolution.x - px.x), min(px.y, u_resolution.y - px.y));
    float w = u_width * PX;
    float m = 1.0 - smoothstep(w - 0.5, w + 0.5, d);

    if (u_style == STYLE_DOUBLE) {
        float outer = 1.0 - smoothstep(w / 3.0 - 0.5, w / 3.0 + 0.5, d);
        float inner = smoothstep(w * 2.0 / 3.0 - 0.5, w * 2.0 / 3.0 + 0.5, d) * m;
        m = max(outer, inner);
    }
    if (u_style == STYLE_FADE) m = 1.0 - smoothstep(0.0, max(w, 1.0), d);

    return vec4(mix(c.rgb, u_color, m * u_opacity), 1.0);
}
""")

add('crosshair', 'overlay', 'a crosshair (or a dot, a ring, a square) on the screen', [
    C('style', 'plus', ['plus', 'x', 'dot', 'circle', 'square'], 'the shape'),
    F('size', 12.0, 1, 200, 'the length of the arms, or the size of the ring (pixels, measured on a screen 1080 high)'),
    F('thickness', 2.0, 0.5, 20, 'how thick the lines are'),
    F('gap', 4.0, 0, 50, 'the gap in the middle (plus and x)'),
    F('outline', 1.0, 0, 6, 'the width of the dark outline that keeps it visible on any picture'),
    RGB('color', (1.0, 1.0, 1.0), 'the color'),
    F('opacity', 1.0, 0, 1, 'how much of it is seen'),
    B('invert', False, 'instead of a color it shows the opposite of the picture below it'),
    PT('center', (0.5, 0.5), 'where it is'),
], """
float sd_box(vec2 p, vec2 center, vec2 half_size) {
    vec2 d = abs(p - center) - half_size;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float plus_shape(vec2 p) {
    vec2 q = abs(p);
    float arm = u_size * 0.5;
    float t = u_thickness * 0.5;
    return min(sd_box(q, vec2(u_gap + arm, 0.0), vec2(arm, t)), sd_box(q, vec2(0.0, u_gap + arm), vec2(t, arm)));
}

vec4 fx(vec4 c, vec2 uv) {
    vec2 p = (gl_FragCoord.xy - u_center * u_resolution) / PX;
    float sd;

    if (u_style == STYLE_PLUS) sd = plus_shape(p);
    else if (u_style == STYLE_X) sd = plus_shape(rot2(0.785398) * p);
    else if (u_style == STYLE_DOT) sd = length(p) - u_thickness;
    else if (u_style == STYLE_CIRCLE) sd = abs(length(p) - u_size) - u_thickness * 0.5;
    else sd = abs(sd_box(p, vec2(0.0), vec2(u_size))) - u_thickness * 0.5;

    float aa = 1.0 / PX;
    float shape = 1.0 - smoothstep(-0.5 * aa, 0.5 * aa, sd);
    float line = 1.0 - smoothstep(-0.5 * aa, 0.5 * aa, sd - u_outline);
    vec3 col = c.rgb;
    if (u_outline > 0.0) col = mix(col, vec3(0.0), line * u_opacity);
    return vec4(mix(col, u_invert == 1 ? 1.0 - c.rgb : u_color, shape * u_opacity), 1.0);
}
""")

add('blend', 'overlay', 'covers the whole picture with a color, with any blend mode', [
    RGB('color', (1.0, 0.5, 0.2), 'the color'),
    BLEND('softlight'),
    F('opacity', 0.5, 0, 1, 'how much of it is seen'),
], """
vec4 fx(vec4 c, vec2 uv) { return vec4(mix(c.rgb, blend_mode(u_blend, c.rgb, u_color), u_opacity), 1.0); }
""")

add('gradient', 'overlay', 'a gradient of two colors over the picture, with any blend mode (a sunset sky, a color tilt)', [
    C('type', 'linear', ['linear', 'radial'], 'a straight gradient or one that grows from a point'),
    RGB('start', (0.1, 0.15, 0.5), 'the first color'),
    RGB('end', (1.0, 0.6, 0.25), 'the second color'),
    F('angle', 90.0, -180, 180, 'the direction from start to end, in degrees (linear): 90 is upwards'),
    PT('center', (0.5, 0.5), 'where it starts (radial)'),
    F('size', 1.0, 0.1, 4, 'how far it takes to go from the first to the second color'),
    BLEND('softlight'),
    F('opacity', 0.6, 0, 1, 'how much of it is seen'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv);
    float t;
    if (u_type == TYPE_LINEAR) t = dot(q, vec2(cos(radians(u_angle)), sin(radians(u_angle)))) / u_size + 0.5;
    else t = length(q - centered(u_center)) / u_size;
    vec3 col = mix(u_start, u_end, clamp(t, 0.0, 1.0));
    return vec4(mix(c.rgb, blend_mode(u_blend, c.rgb, col), u_opacity), 1.0);
}
""")

add('fadeto', 'overlay', 'fades the picture to a color: all of it, or only the top, the bottom, a side, the edges or the middle', [
    RGB('color', (0.0, 0.0, 0.0), 'the color it fades to'),
    F('amount', 0.5, 0, 1, 'how far it fades (1 is fully the color)'),
    C('where', 'all', ['all', 'top', 'bottom', 'left', 'right', 'edges', 'center'], 'which part fades'),
    F('size', 0.4, 0.05, 1.5, 'how far the fade reaches into the picture (a part of the screen)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float m = 1.0;
    if (u_where == WHERE_TOP) m = 1.0 - smoothstep(0.0, u_size, 1.0 - uv.y);
    else if (u_where == WHERE_BOTTOM) m = 1.0 - smoothstep(0.0, u_size, uv.y);
    else if (u_where == WHERE_LEFT) m = 1.0 - smoothstep(0.0, u_size, uv.x);
    else if (u_where == WHERE_RIGHT) m = 1.0 - smoothstep(0.0, u_size, 1.0 - uv.x);
    else if (u_where == WHERE_EDGES) m = 1.0 - smoothstep(0.0, u_size * 0.5, min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y)));
    else if (u_where == WHERE_CENTER) m = 1.0 - smoothstep(0.0, u_size, length(centered(uv)));
    return vec4(mix(c.rgb, u_color, m * u_amount), 1.0);
}
""")

add('pulse', 'overlay', 'the brightness of the picture goes up and down in time', [
    F('rate', 1.0, 0, 30, 'how many pulses a second'),
    F('depth', 0.3, 0, 1, 'how dark it gets at the lowest'),
    C('shape', 'sine', ['sine', 'triangle', 'square'], 'the shape of the pulse'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float ph = u_time * u_rate;
    float wave = 0.5 + 0.5 * sin(TAU * ph);
    if (u_shape == SHAPE_TRIANGLE) wave = abs(fract(ph) * 2.0 - 1.0);
    if (u_shape == SHAPE_SQUARE) wave = step(fract(ph), 0.5);
    return vec4(c.rgb * (1.0 - u_depth * (1.0 - wave)), 1.0);
}
""", animated=True)

add('flash', 'overlay', 'a flash of color that fades away, again and again (like lightning or a camera)', [
    F('rate', 0.5, 0, 10, 'how many flashes a second'),
    F('decay', 6.0, 0.5, 30, 'how fast the flash fades (higher is shorter)'),
    RGB('color', (1.0, 1.0, 1.0), 'the color of the flash'),
    F('strength', 0.8, 0, 1, 'how strong the flash is'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float m = exp(-fract(u_time * u_rate) * u_decay);
    return vec4(mix(c.rgb, u_color, m * u_strength), 1.0);
}
""", animated=True)

add('strobe', 'overlay', 'flashes the picture on and off at any rate (fast flashing can bother people who are sensitive to it)', [
    F('rate', 10.0, 0, 1000, 'how many flashes a second'),
    F('duty', 0.5, 0, 1, 'how much of every flash the effect is on'),
    C('mode', 'black', ['black', 'white', 'invert', 'color'], 'what the flash shows'),
    RGB('color', (1.0, 0.0, 0.0), 'the color of the flash (color mode)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    if (fract(u_time * u_rate) >= u_duty) return c;
    if (u_mode == MODE_BLACK) return vec4(0.0, 0.0, 0.0, 1.0);
    if (u_mode == MODE_WHITE) return vec4(1.0);
    if (u_mode == MODE_INVERT) return vec4(1.0 - c.rgb, 1.0);
    return vec4(u_color, 1.0);
}
""", animated=True)

add('godrays', 'overlay', 'beams of light that stream from a bright point through the picture', [
    PT('light', (0.5, 0.8), 'where the light is'),
    F('threshold', 0.9, 0, 1, 'how bright something has to be to make beams'),
    F('density', 0.9, 0.1, 1.5, 'how far the beams reach'),
    F('decay', 0.96, 0.8, 1.0, 'how fast the beams fade away from the light (1 is never)'),
    F('intensity', 0.6, 0, 4, 'how strong the beams are'),
    RGB('tint', (1.0, 0.95, 0.8), 'the color of the beams'),
    I('samples', 48, 16, 96, 'how smooth (more is slower)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 delta = (uv - u_light) * u_density / float(u_samples);
    vec2 p = uv;
    float illum = 1.0;
    vec3 sum = vec3(0.0);

    for (int i = 0; i < 96; i++) {
        if (i >= u_samples) break;
        p -= delta;
        vec3 s = prev(clamp(p, 0.0, 1.0)).rgb;
        float b = max(max(s.r, s.g), s.b);
        sum += s * smoothstep(u_threshold, u_threshold + 0.15, b) * illum;
        illum *= u_decay;
    }

    return vec4(c.rgb + sum / float(u_samples) * u_intensity * u_tint * 2.0, 1.0);
}
""")

add('lensflare', 'overlay', 'bright parts make rings and ghost images across the picture, like a camera lens', [
    I('ghosts', 4, 1, 8, 'how many ghost images'),
    F('dispersal', 0.3, 0, 1, 'how far apart the ghosts are'),
    F('halo', 0.45, 0, 1, 'how big the ring of light is'),
    F('distortion', 0.02, 0, 0.1, 'how much the colors split'),
    F('threshold', 0.8, 0, 1, 'how bright something has to be to make a flare'),
    F('intensity', 0.6, 0, 4, 'how strong the flare is'),
    RGB('inner', (1.0, 0.85, 0.6), 'the color of the flare near the middle'),
    RGB('outer', (0.5, 0.6, 1.0), 'the color of the flare near the edges'),
], """
vec3 flare_sample(vec2 p, vec2 dir) {
    vec3 s = vec3(prev(p + dir * -u_distortion).r, prev(p).g, prev(p + dir * u_distortion).b);
    return max(s - u_threshold, 0.0);
}

vec4 fx(vec4 c, vec2 uv) {
    vec2 tc = 1.0 - uv;
    vec2 ghost_vec = (vec2(0.5) - tc) * u_dispersal;
    vec2 dir = normalize(ghost_vec + vec2(0.0001));
    vec3 res = vec3(0.0);

    for (int i = 0; i < 8; i++) {
        if (i >= u_ghosts) break;
        vec2 offset = fract(tc + ghost_vec * float(i));
        float w = pow(1.0 - length(vec2(0.5) - offset) / length(vec2(0.5)), 10.0);
        res += flare_sample(offset, dir) * w;
    }

    vec2 halo_vec = dir * u_halo;
    float hw = pow(1.0 - length(vec2(0.5) - fract(tc + halo_vec)) / length(vec2(0.5)), 5.0);
    res += flare_sample(tc + halo_vec, dir) * hw;

    vec3 tint = mix(u_inner, u_outer, clamp(length(vec2(0.5) - uv) / 0.7071, 0.0, 1.0));
    return vec4(c.rgb + res * tint * u_intensity, 1.0);
}
""")

add('lightleak', 'overlay', 'warm colored light that leaks in from the edges, like an old camera', [
    RGB('color1', (1.0, 0.45, 0.1), 'the first color of the light'),
    RGB('color2', (1.0, 0.1, 0.4), 'the second color of the light'),
    F('amount', 0.5, 0, 1, 'how strong the light is'),
    F('scale', 1.2, 0.3, 5, 'how big the patches are'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) * u_scale;
    float n = fbm(q + vec2(u_time * 0.1, -u_time * 0.07), 3);
    float n2 = fbm(q * 0.7 + 13.0 + vec2(-u_time * 0.05, u_time * 0.08), 3);
    vec2 e = abs(uv * 2.0 - 1.0);
    float edge = pow(max(e.x, e.y), 2.0);
    float m = smoothstep(0.35, 0.85, n) * edge;
    vec3 leak = mix(u_color1, u_color2, smoothstep(0.3, 0.7, n2)) * m * u_amount * 2.0;
    return vec4(1.0 - (1.0 - c.rgb) * (1.0 - clamp(leak, 0.0, 1.0)), 1.0);
}
""", animated=True)

add('rain', 'overlay', 'rain falling over the picture', [
    F('density', 0.5, 0, 1, 'how much rain'),
    F('fall', 1.5, 0.1, 5, 'how fast the rain falls (screens a second)'),
    F('length', 90.0, 20, 400, 'how long the streaks are (pixels, measured on a screen 1080 high)'),
    F('angle', 8.0, -45, 45, 'how much the rain slants (wind)'),
    RGB('color', (0.7, 0.78, 0.9), 'the color of the rain'),
    F('opacity', 0.6, 0, 1, 'how much of the rain is seen'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 f = gl_FragCoord.xy / PX;
    vec2 p = rot2(-radians(u_angle)) * f;
    float amount = 0.0;

    for (int l = 0; l < 3; l++) {
        float fl = float(l);
        float lane = 6.0 + fl * 5.0;
        float id = floor(p.x / lane);
        float h = hash12(vec2(id, fl + float(u_seed) * 3.1));
        if (h > u_density) continue;

        float h2 = hash12(vec2(id + 91.0, fl));
        float len = u_length * (0.6 + 0.8 * h2);
        float v = u_fall * 1080.0 * (0.7 + 0.6 * h2) * (1.0 + fl * 0.3);
        float ph = mod(p.y + u_time * v + h2 * 1000.0, len * 4.0) / len;
        float streak = smoothstep(1.0, 0.0, ph);
        float lx = abs(fract(p.x / lane) - 0.5) * lane;
        float w = 0.5 + fl * 0.25;
        amount = max(amount, streak * (1.0 - smoothstep(w, w + 1.0, lx)) * (1.0 - fl * 0.2));
    }

    return vec4(mix(c.rgb, u_color, amount * u_opacity), 1.0);
}
""", animated=True, seeded=True)

add('snow', 'overlay', 'snow falling over the picture', [
    F('density', 0.35, 0, 1, 'how much snow'),
    F('size', 6.0, 1, 30, 'the size of the biggest flakes (pixels, measured on a screen 1080 high)'),
    F('fall', 0.15, -2, 2, 'how fast the snow falls (screens a second, negative rises)'),
    F('wind', 0.05, -2, 2, 'how fast the snow drifts sideways (screens a second)'),
    I('layers', 4, 1, 6, 'how many depths of snow (the far ones are smaller and slower)'),
    RGB('color', (1.0, 1.0, 1.0), 'the color of the flakes'),
    F('opacity', 0.9, 0, 1, 'how much of the snow is seen'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = u_time;
    vec2 f = gl_FragCoord.xy / PX;
    float amount = 0.0;

    for (int l = 0; l < 6; l++) {
        if (l >= u_layers) break;
        float fl = float(l);
        float r = u_size * (1.0 - 0.12 * fl);
        float cs = r * 7.0;
        vec2 p = f + vec2(-t * u_wind * 1080.0, t * u_fall * 1080.0 * (1.0 - 0.1 * fl)) + fl * 37.0;
        vec2 cell = floor(p / cs);
        float h = hash12(cell + fl * 17.0 + float(u_seed));
        if (h > u_density) continue;

        vec2 rnd = hash22(cell + 7.0 + fl);
        vec2 center = (cell + 0.25 + 0.5 * rnd) * cs;
        center.x += sin(t * (0.5 + rnd.x) + rnd.y * TAU) * cs * 0.1;
        float d = length(p - center);
        amount = max(amount, (1.0 - smoothstep(r * 0.4, r, d)) * (1.0 - 0.1 * fl));
    }

    return vec4(mix(c.rgb, u_color, amount * u_opacity), 1.0);
}
""", animated=True, seeded=True)

alias('dust', 'snow', 'tiny glowing specks of dust drifting slowly in the air', density=0.6, size=3.0, fall=0.03, wind=0.01, layers=5, color=(1.0, 0.9, 0.7), opacity=0.5)

add('stars', 'overlay', 'twinkling stars (they only show in the dark parts of the picture)', [
    F('density', 0.08, 0, 1, 'how many stars'),
    F('size', 2.5, 0.5, 8, 'the size of the biggest stars (pixels, measured on a screen 1080 high)'),
    F('twinkle', 0.5, 0, 1, 'how much the stars twinkle'),
    F('motion', 0.0, -1, 1, 'how fast the sky drifts sideways (screens a second)'),
    F('sky', 0.8, 0, 1, 'how much the stars hide behind bright parts of the picture'),
    RGB('color', (1.0, 1.0, 1.0), 'the color of the stars'),
    F('brightness', 1.0, 0, 3, 'how bright the stars are'),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = u_time;
    vec2 f = gl_FragCoord.xy / PX + vec2(u_motion * t * 1080.0, 0.0);
    float cs = 8.0 * u_size + 16.0;
    vec2 cell = floor(f / cs);
    float h = hash12(cell + float(u_seed) * 5.3);
    if (h > u_density) return c;

    vec2 rnd = hash22(cell + 13.0);
    vec2 center = (cell + 0.15 + 0.7 * rnd) * cs;
    float r = u_size * (0.5 + rnd.x);
    float star = pow(1.0 - smoothstep(0.0, r, length(f - center)), 2.0);
    float tw = 1.0 - u_twinkle * 0.5 * (1.0 + sin(t * (2.0 + 4.0 * rnd.y) + rnd.x * TAU));
    float vis = 1.0 - u_sky * smoothstep(0.2, 0.7, luma(c.rgb));
    return vec4(c.rgb + u_color * star * tw * vis * u_brightness * (0.5 + 0.5 * hash12(cell + 29.0)), 1.0);
}
""", animated=True, seeded=True)
