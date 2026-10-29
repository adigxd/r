from .base import add, F, I, B, C, RGB, PT, EDGE

# bending, waving and moving the picture
# every effect here reads the picture at a moved place, and `edge` says what to show where that place is off the screen

add('wave', 'distort', 'the picture ripples like a flag or like heat over a road', [
    F('amount', 12.0, 0, 200, 'how far the picture moves (pixels, measured on a screen 1080 high)'),
    F('frequency', 6.0, 0.1, 60, 'how many waves fit in the screen height'),
    C('direction', 'horizontal', ['horizontal', 'vertical', 'both'], 'horizontal moves the picture sideways (waves go up the screen), vertical moves it up and down'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv);
    vec2 amp = u_amount * PX / u_resolution;
    vec2 p = uv;
    float ph = u_time * 2.0;
    if (u_direction != DIRECTION_VERTICAL) p.x += sin(q.y * u_frequency * TAU + ph) * amp.x;
    if (u_direction != DIRECTION_HORIZONTAL) p.y += sin(q.x * u_frequency * TAU + ph) * amp.y;
    return vec4(prev_edge(p, u_edge), 1.0);
}
""", animated=True)

add('ripple', 'distort', 'rings spread out from a point, like a stone in water', [
    F('amount', 10.0, 0, 100, 'how far the picture moves (pixels, measured on a screen 1080 high)'),
    F('wavelength', 0.08, 0.01, 1, 'the distance from one ring to the next (a part of the screen height)'),
    F('decay', 2.0, 0, 10, 'how fast the rings fade with the distance'),
    PT('center', (0.5, 0.5), 'where the rings start'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) - centered(u_center);
    float r = length(q);
    float wave = sin((r / u_wavelength - u_time * 0.8) * TAU);
    vec2 dir = q / max(r, 0.0001);
    q += dir * wave * exp(-r * u_decay) * u_amount * PX / u_resolution.y;
    return vec4(prev_edge(uncentered(q + centered(u_center)), u_edge), 1.0);
}
""", animated=True)

add('swirl', 'distort', 'twists the picture around a point', [
    F('angle', 180.0, -720, 720, 'how many degrees the middle is turned'),
    F('radius', 0.5, 0.05, 2, 'how far the twist reaches (a part of the screen height)'),
    PT('center', (0.5, 0.5), 'the middle of the twist'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) - centered(u_center);
    float k = smoothstep(u_radius, 0.0, length(q));
    q = rot2(radians(u_angle) * k) * q;
    return vec4(prev_edge(uncentered(q + centered(u_center)), u_edge), 1.0);
}
""")

add('bulge', 'distort', 'pushes the picture out (a bulge) or pulls it in (a pinch) around a point', [
    F('strength', 0.5, -1, 1, 'positive bulges, negative pinches'),
    F('radius', 0.5, 0.05, 2, 'how far it reaches (a part of the screen height)'),
    PT('center', (0.5, 0.5), 'the middle'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) - centered(u_center);
    float r = length(q) / u_radius;
    if (r < 1.0) q *= max(1.0 - u_strength * (1.0 - r) * (1.0 - r), 0.02);
    return vec4(prev_edge(uncentered(q + centered(u_center)), u_edge), 1.0);
}
""")

add('fisheye', 'distort', 'the whole picture is bent like it is seen through a fisheye lens', [
    F('strength', 0.8, -1, 2, 'positive is a fisheye, negative is the other way (pincushion)'),
    F('zoom', 1.0, 0.5, 3, 'zooms in (hides the edges)'),
    PT('center', (0.5, 0.5), 'the middle of the lens'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = (centered(uv) - centered(u_center)) / u_zoom;
    q *= 1.0 + u_strength * dot(q, q);
    return vec4(prev_edge(uncentered(q + centered(u_center)), u_edge), 1.0);
}
""")

add('lens', 'distort', 'a round magnifying glass that you can put anywhere on the screen', [
    F('radius', 0.2, 0.02, 1, 'the size of the lens (a part of the screen height)'),
    F('magnification', 2.0, 0.2, 8, 'how much it magnifies (below 1 it shrinks)'),
    PT('center', (0.5, 0.5), 'where the lens is'),
    F('rim', 3.0, 0, 40, 'the width of the ring around the lens (pixels, measured on a screen 1080 high)'),
    RGB('rim_color', (1.0, 1.0, 1.0), 'the color of the ring'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) - centered(u_center);
    float r = length(q);
    vec2 q2 = q;
    if (r < u_radius) q2 = q * mix(1.0 / u_magnification, 1.0, pow(r / u_radius, 2.0));

    vec3 col = texture(u_prev, clamp(uncentered(q2 + centered(u_center)), 0.0, 1.0)).rgb;
    float half_rim = 0.5 * u_rim * PX / u_resolution.y;
    float ring = (1.0 - smoothstep(half_rim - 0.001, half_rim + 0.001, abs(r - u_radius))) * step(0.0001, u_rim);
    return vec4(mix(col, u_rim_color, ring), 1.0);
}
""")

add('transform', 'distort', 'zooms, turns, moves and flips the whole picture', [
    F('zoom', 1.5, 0.1, 10, 'above 1 zooms in, below 1 zooms out'),
    F('rotate', 0.0, -360, 360, 'degrees to turn the picture'),
    F('x', 0.0, -1, 1, 'moves the picture sideways (a part of the screen width)'),
    F('y', 0.0, -1, 1, 'moves the picture up (a part of the screen height)'),
    B('flip_x', False, 'mirrors the picture left to right'),
    B('flip_y', False, 'mirrors the picture top to bottom'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv);
    if (u_flip_x == 1) q.x = -q.x;
    if (u_flip_y == 1) q.y = -q.y;
    q = rot2(radians(-u_rotate)) * q;
    q = q / u_zoom - vec2(u_x * ASPECT, u_y);
    return vec4(prev_edge(uncentered(q), u_edge), 1.0);
}
""")

add('mirror', 'distort', 'one side of the picture is copied to the other, like a mirror', [
    C('side', 'left', ['left', 'right', 'top', 'bottom', 'quad'], 'the side that is kept (quad keeps the bottom left and copies it to all 4 corners)'),
    F('position', 0.5, 0, 1, 'where the mirror is'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 p = uv;
    float m = u_position;
    if (u_side == SIDE_LEFT || u_side == SIDE_QUAD) { if (uv.x > m) p.x = 2.0 * m - uv.x; }
    if (u_side == SIDE_RIGHT) { if (uv.x < m) p.x = 2.0 * m - uv.x; }
    if (u_side == SIDE_TOP) { if (uv.y < m) p.y = 2.0 * m - uv.y; }
    if (u_side == SIDE_BOTTOM || u_side == SIDE_QUAD) { if (uv.y > m) p.y = 2.0 * m - uv.y; }
    return vec4(prev_edge(p, u_edge), 1.0);
}
""")

add('kaleidoscope', 'distort', 'the picture is cut into slices that are mirrored around a point, like a kaleidoscope', [
    I('segments', 6, 2, 32, 'how many slices'),
    F('angle', 0.0, -180, 180, 'turns the picture'),
    F('spin', 0.0, -360, 360, 'degrees a second the picture keeps turning'),
    F('zoom', 1.0, 0.2, 5, 'zooms in'),
    PT('center', (0.5, 0.5), 'the middle'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) - centered(u_center);
    float r = length(q);
    float a = atan(q.y, q.x) + radians(u_angle + u_spin * u_time);
    float seg = TAU / float(u_segments);
    a = abs(mod(a, seg) - seg * 0.5);
    vec2 q2 = r / u_zoom * vec2(cos(a), sin(a));
    return vec4(prev_edge(uncentered(q2 + centered(u_center)), u_edge), 1.0);
}
""", animated=True)

add('tile', 'distort', 'the whole picture is repeated in rows and columns (and can slide)', [
    F('columns', 3.0, 1, 20, 'how many copies across'),
    F('rows', 3.0, 1, 20, 'how many copies down'),
    B('mirror', False, 'every other copy is mirrored'),
    F('scroll_x', 0.0, -2, 2, 'how fast the copies slide sideways (screens a second)'),
    F('scroll_y', 0.0, -2, 2, 'how fast the copies slide up (screens a second)'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 p = uv * vec2(u_columns, u_rows) + vec2(u_scroll_x, u_scroll_y) * u_time;
    return vec4(prev_edge(p, u_mirror == 1 ? 1 : 2), 1.0);
}
""", animated=True)

add('polar', 'distort', 'turns the picture into a ring (a tiny planet), or a ring into a flat picture', [
    C('mode', 'planet', ['planet', 'unwrap'], 'planet wraps the picture around a point, unwrap does the opposite'),
    F('zoom', 1.0, 0.2, 5, 'zooms in'),
    F('rotate', 0.0, -180, 180, 'turns it'),
    PT('center', (0.5, 0.5), 'the middle'),
    EDGE('repeat'),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 mid = centered(u_center);
    vec2 p;

    if (u_mode == MODE_PLANET) {
        vec2 q = centered(uv) - mid;
        float a = atan(q.y, q.x) + radians(u_rotate);
        p = vec2(a / TAU + 0.5, length(q) * 2.0 / u_zoom);
    } else {
        float a = (uv.x - 0.5) * TAU + radians(u_rotate);
        float r = uv.y * 0.5 * u_zoom;
        p = uncentered(mid + r * vec2(cos(a), sin(a)));
    }

    return vec4(prev_edge(p, u_edge), 1.0);
}
""")

add('shear', 'distort', 'slants the picture sideways or up and down', [
    F('shear_x', 0.3, -2, 2, 'slants the picture sideways (the top moves right when positive)'),
    F('shear_y', 0.0, -2, 2, 'slants the picture up and down (the right side moves up when positive)'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv);
    vec2 s = vec2(q.x - u_shear_x * q.y, q.y - u_shear_y * q.x);
    return vec4(prev_edge(uncentered(s), u_edge), 1.0);
}
""")

add('stretch', 'distort', 'stretches the middle of the picture and squeezes the edges (or the other way round), each direction on its own', [
    F('x', 1.0, 0.3, 3, 'below 1 stretches the middle sideways, above 1 squeezes it'),
    F('y', 1.8, 0.3, 3, 'below 1 stretches the middle up and down, above 1 squeezes it'),
    PT('center', (0.5, 0.5), 'the middle'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 d = uv - u_center;
    vec2 m = vec2(d.x > 0.0 ? 1.0 - u_center.x : u_center.x, d.y > 0.0 ? 1.0 - u_center.y : u_center.y);
    vec2 s = sign(d) * pow(abs(d) / max(m, vec2(0.0001)), vec2(u_x, u_y)) * m;
    return vec4(prev_edge(u_center + s, u_edge), 1.0);
}
""")

add('shake', 'distort', 'the camera shakes', [
    F('amount', 10.0, 0, 100, 'how far the picture moves (pixels, measured on a screen 1080 high)'),
    F('rotation', 0.5, 0, 10, 'how many degrees it turns'),
    F('rate', 24.0, 0, 120, 'how many shakes a second'),
    B('smooth', True, 'moves smoothly from one shake to the next (off: it jumps)'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    float k = u_time * u_rate + float(u_seed) * 13.0;
    float i = floor(k);
    float f = u_smooth == 1 ? smoothstep(0.0, 1.0, fract(k)) : 0.0;
    vec2 n = mix(hash22(vec2(i, 1.0)), hash22(vec2(i + 1.0, 1.0)), f) * 2.0 - 1.0;
    float ra = mix(hash12(vec2(i, 2.0)), hash12(vec2(i + 1.0, 2.0)), f) * 2.0 - 1.0;
    vec2 q = rot2(radians(u_rotation) * ra) * centered(uv);
    q += n * u_amount * PX / u_resolution.y;
    return vec4(prev_edge(uncentered(q), u_edge), 1.0);
}
""", animated=True, seeded=True)

add('sway', 'distort', 'the picture slowly rocks and drifts, like a boat', [
    F('angle', 2.0, 0, 30, 'how many degrees it rocks'),
    F('distance', 20.0, 0, 300, 'how far it drifts (pixels, measured on a screen 1080 high)'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = u_time;
    vec2 q = rot2(radians(u_angle) * sin(t * 0.7)) * centered(uv);
    q += vec2(sin(t * 0.9), cos(t * 1.3)) * u_distance * PX / u_resolution.y;
    return vec4(prev_edge(uncentered(q), u_edge), 1.0);
}
""", animated=True)

add('heat', 'distort', 'a shimmering haze, like the air over a fire or a hot road', [
    F('amount', 6.0, 0, 60, 'how far the picture moves (pixels, measured on a screen 1080 high)'),
    F('scale', 12.0, 1, 60, 'how many shimmers fit in the screen height'),
    F('rise', 1.0, 0, 5, 'how fast the haze rises'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) * u_scale - vec2(0.0, u_time * u_rise);
    vec2 n = vec2(fbm(q, 3), fbm(q + 31.7, 3)) - 0.5;
    return vec4(prev_edge(uv + n * 2.0 * u_amount * PX / u_resolution, u_edge), 1.0);
}
""", animated=True)

add('noisewarp', 'distort', 'the picture flows and bends like it is under oil or water', [
    F('amount', 20.0, 0, 200, 'how far the picture moves (pixels, measured on a screen 1080 high)'),
    F('scale', 4.0, 0.5, 40, 'how many bends fit in the screen height'),
    I('octaves', 3, 1, 6, 'how much fine detail the bends have'),
    F('flow', 0.3, 0, 5, 'how fast it flows'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    vec2 q = centered(uv) * u_scale + vec2(0.0, u_time * u_flow);
    vec2 n = vec2(fbm(q, u_octaves), fbm(q + 17.3, u_octaves)) - 0.5;
    return vec4(prev_edge(uv + n * 2.0 * u_amount * PX / u_resolution, u_edge), 1.0);
}
""", animated=True)

add('slice', 'distort', 'strips of the picture slide sideways (or up and down) by different amounts', [
    C('direction', 'horizontal', ['horizontal', 'vertical'], 'which way the strips slide'),
    I('count', 24, 2, 200, 'how many strips'),
    F('amount', 40.0, 0, 300, 'how far a strip can slide (pixels, measured on a screen 1080 high)'),
    F('chance', 0.5, 0, 1, 'how many of the strips slide'),
    F('rate', 8.0, 0, 60, 'how many times a second they change'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    float slot = floor(u_time * u_rate) + float(u_seed);
    bool horizontal = u_direction == DIRECTION_HORIZONTAL;
    float id = floor((horizontal ? uv.y : uv.x) * float(u_count));
    float moving = step(1.0 - u_chance, hash12(vec2(id, slot)));
    float shift = (hash12(vec2(id, slot + 9.0)) - 0.5) * 2.0 * moving * u_amount * PX;
    vec2 p = horizontal ? vec2(uv.x + shift / u_resolution.x, uv.y) : vec2(uv.x, uv.y + shift / u_resolution.y);
    return vec4(prev_edge(p, u_edge), 1.0);
}
""", animated=True, seeded=True)

add('jitter', 'distort', 'every little square of the picture is moved a bit at random, like frosted glass', [
    F('amount', 3.0, 0, 30, 'how far a square moves (pixels, measured on a screen 1080 high)'),
    F('size', 1.0, 1, 32, 'the size of the squares (pixels, measured on a screen 1080 high)'),
    F('rate', 0.0, 0, 120, 'how many times a second they move again (0 keeps them still)'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    float slot = floor(u_time * u_rate) + float(u_seed);
    vec2 cell = floor(gl_FragCoord.xy / max(1.0, u_size * PX));
    vec2 rnd = hash22(cell + slot * 17.3);
    return vec4(prev_edge(uv + (rnd - 0.5) * 2.0 * u_amount * PX / u_resolution, u_edge), 1.0);
}
""", animated=True, seeded=True)

add('zoompulse', 'distort', 'the picture zooms in and out in time, like a beat', [
    F('amount', 0.06, 0, 1, 'how much it zooms'),
    F('rate', 1.5, 0, 30, 'how many pulses a second'),
    C('shape', 'beat', ['sine', 'beat', 'saw'], 'sine is smooth, beat is a sharp thump that fades, saw grows and snaps back'),
    PT('center', (0.5, 0.5), 'the point it zooms into'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    float ph = u_time * u_rate;
    float wave = 0.5 + 0.5 * sin(TAU * ph);
    if (u_shape == SHAPE_BEAT) wave = pow(1.0 - fract(ph), 4.0);
    if (u_shape == SHAPE_SAW) wave = fract(ph);
    vec2 q = (centered(uv) - centered(u_center)) / (1.0 + u_amount * wave);
    return vec4(prev_edge(uncentered(q + centered(u_center)), u_edge), 1.0);
}
""", animated=True)

add('underwater', 'distort', 'as if you look through water: wobbling, blue-green, with light patterns and dark depths', [
    F('wobble', 8.0, 0, 60, 'how much the picture wobbles (pixels, measured on a screen 1080 high)'),
    RGB('tint', (0.3, 0.7, 1.0), 'the color of the water'),
    F('strength', 0.5, 0, 1, 'how much the water colors the picture'),
    F('caustics', 0.3, 0, 1, 'how bright the moving light patterns are'),
    F('depth', 0.4, 0, 1, 'how dark it gets towards the bottom'),
    EDGE(),
], """
vec4 fx(vec4 c, vec2 uv) {
    float t = u_time;
    vec2 q = centered(uv);
    vec2 off = vec2(sin(q.y * 18.0 + t * 1.7) + sin(q.y * 7.0 - t * 1.1), sin(q.x * 15.0 + t * 1.4) + sin(q.x * 9.0 + t * 0.8)) * 0.5 * u_wobble * PX / u_resolution;
    vec3 col = prev_edge(uv + off, u_edge);
    col = mix(col, col * u_tint, u_strength);

    float n1 = vnoise(q * 9.0 + vec2(t * 0.3, t * 0.2));
    float n2 = vnoise(q * 11.7 - vec2(t * 0.25, -t * 0.3) + 5.0);
    float net = pow(clamp(1.0 - abs(n1 - n2) * 3.0, 0.0, 1.0), 4.0);
    col += net * u_caustics * u_tint;

    col *= mix(1.0, uv.y * 0.7 + 0.3, u_depth);
    return vec4(col, 1.0);
}
""", animated=True)
