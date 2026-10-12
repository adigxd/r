#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform vec2 u_resolution;

// noise dithering: every pixel is compared against a random number instead of a pattern, so it looks like film grain
// (the old random dither from post_dither.frag)

float random(vec2 co)
{
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main()
{
	vec3 color = texture(u_texture, v_uv).rgb;

	float brightness = dot(color, vec3(0.333, 0.333, 0.333));

	float noise = random(v_uv * u_resolution); // multiple by u_resolution to ensure randomness

	if(noise < brightness) { frag_color = vec4(vec3(1.0), 1.0); }
	else                   { frag_color = vec4(vec3(0.0), 1.0); }
}
