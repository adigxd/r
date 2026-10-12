#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform vec2 u_resolution;

// ordered dithering: the screen is split into little squares (dither pixels), and every one of them is compared against a threshold from a repeating 8x8 Bayer pattern
// brighter than its threshold = light color, otherwise dark color; the pattern spreads the thresholds out evenly, so brightness comes out as an even texture instead of random dots

const int PIXEL_SIZE = 2; // size of one dither pixel in screen pixels (1 = finest)
const float BLACK_POINT = 0.01; // anything darker than this is plain dark, so the empty background doesn't speckle
const float CONTRAST = 0.6; // below 1 brightens the dark parts so more of the dark scene survives (1 = no change)
const vec3 COLOR_DARK = vec3(0.0, 0.0, 0.0625);
const vec3 COLOR_LIGHT = vec3(1.0, 1.0, 0.9375);

const float BAYER[64] = float[64](
	 0.0, 32.0,  8.0, 40.0,  2.0, 34.0, 10.0, 42.0,
	48.0, 16.0, 56.0, 24.0, 50.0, 18.0, 58.0, 26.0,
	12.0, 44.0,  4.0, 36.0, 14.0, 46.0,  6.0, 38.0,
	60.0, 28.0, 52.0, 20.0, 62.0, 30.0, 54.0, 22.0,
	 3.0, 35.0, 11.0, 43.0,  1.0, 33.0,  9.0, 41.0,
	51.0, 19.0, 59.0, 27.0, 49.0, 17.0, 57.0, 25.0,
	15.0, 47.0,  7.0, 39.0, 13.0, 45.0,  5.0, 37.0,
	63.0, 31.0, 55.0, 23.0, 61.0, 29.0, 53.0, 21.0
);

void main()
{
	// the dither pixel this pixel belongs to, and the middle of it in the scene texture (so a whole dither pixel gets one color)
	ivec2 cell = ivec2(gl_FragCoord.xy) / PIXEL_SIZE;
	vec2 uv = (vec2(cell * PIXEL_SIZE) + 0.5 * float(PIXEL_SIZE)) / u_resolution;

	vec3 color = texture(u_texture, uv).rgb;

	float brightness = dot(color, vec3(0.299, 0.587, 0.114)); // luminance
	brightness = pow(max(brightness - BLACK_POINT, 0.0) / (1.0 - BLACK_POINT), CONTRAST);

	float threshold = (BAYER[(cell.y & 7) * 8 + (cell.x & 7)] + 0.5) / 64.0;

	frag_color = vec4(brightness > threshold ? COLOR_LIGHT : COLOR_DARK, 1.0);
}
