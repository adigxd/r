#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform vec2 u_resolution;

float random(vec2 co)
{
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main()
{
	const int LEVEL_COUNT = 8;
	float levels[LEVEL_COUNT] = float[](0.000, 0.125, 0.250, 0.375, 0.500, 0.625, 0.750, 0.875); // has to be initialized like this idk y
	const int MIN_STEP = 1; // minimum step between blackened pixels for dither, further altered by i in for loop

	vec3 color = texture(u_texture, v_uv).rgb;

	float brightness = dot(color, vec3(0.333, 0.333, 0.333));

	vec3 result = vec3(1.0, 1.0, 0.9375);

	for(int i = 0; i < LEVEL_COUNT; i++)
	{
		if(brightness <= levels[i])
		{
			if(mod(floor(v_uv.x * u_resolution.x), MIN_STEP * (i + 1)) == 0 && mod(floor(v_uv.y * u_resolution.y), MIN_STEP * (i + 1)) == 0)
			{
				result = vec3(0.0, 0.0, 0.0625);
			}

			break;
		}
	}

	frag_color = vec4(result, 1.0);

	//float noise = random(v_uv * u_resolution); // multiple by u_resolution to ensure randomness
	//
	//if(noise < brightness) { frag_color = vec4(vec3(1.0), 1.0); }
	//else                   { frag_color = vec4(vec3(0.0), 1.0); }
}
