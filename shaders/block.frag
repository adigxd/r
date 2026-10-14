#version 330 core

#define MAX_LIGHTS 16 // keep in sync with MAX_LIGHTS in config.py

out vec4 frag_color; // output color

flat in float v_cell_x; // from vertex shader
flat in float v_cell_z; // from vertex shader
flat in float v_cell_y; // from vertex shader

in vec3 v_world_pos;
flat in vec3 v_normal;
in vec2 v_uv;

uniform sampler2D u_atlas; // texture atlas

// the lights: one array per attribute, the first u_light_count entries are used
uniform int u_light_count;
uniform vec3 u_light_pos[MAX_LIGHTS];
uniform vec3 u_light_color[MAX_LIGHTS];
uniform float u_light_radius[MAX_LIGHTS];
uniform float u_light_intensity[MAX_LIGHTS];
uniform int u_light_falloff[MAX_LIGHTS]; // 0 = linear, 1 = inverse square
uniform float u_light_falloff_scale[MAX_LIGHTS];
uniform float u_light_diffuse[MAX_LIGHTS]; // 0 = surface angle doesn't matter, 1 = fully matters

// everything in the scene that isn't one light
uniform float u_ambient;
uniform vec3 u_ambient_color;
uniform float u_brightness;
uniform int u_per_block; // 1 = every block is lit from its middle, 0 = every pixel is lit separately
uniform int u_translucent; // 0 = drawing opaque blocks and cutouts, 1 = drawing translucent blocks
uniform float u_face_shade[6]; // top, bottom, front, back, left, right

void main()
{
	// STEP 1: GRAB COLOR FROM TEXTURE

	vec4 tex = texture(u_atlas, v_uv);

	if (u_translucent == 0)
	{
		// cutout: a pixel is either there or not (the texture is smoothed at a distance, so "not" means less than half there)
		if (tex.a < 0.5) discard;

		// the smoothing also mixed in the black of the pixels that are gone, which made the ones that are left darker: undo that
		if (tex.a < 0.999) tex.rgb /= tex.a;

		tex.a = 1.0;
	}
	else if (tex.a <= 0.0)
	{
		discard; // nothing to blend
	}

	vec3 tex_color = tex.rgb;


	// STEP 2: WHERE THE LIGHT IS MEASURED FROM

	vec3 block_pos = floor(v_world_pos - v_normal * 0.5);
	vec3 block_center = block_pos + vec3(0.5);
	vec3 surface_pos = (u_per_block == 1) ? block_center : v_world_pos;


	// STEP 3: AMBIENT LIGHTING (hard-coded value so every surface gets at least some brightness to prevent full black)

	vec3 lit_color = u_ambient * (u_ambient_color * u_brightness);


	// STEP 4: ADD UP EVERY LIGHT

	for (int i = 0; i < u_light_count; i++)
	{
		// light direction and distance
		vec3 light_dir = u_light_pos[i] - surface_pos; // direction from pixel to light
		float light_dist = length(light_dir); // distance magnitude

		if (light_dist > 0.0001)
		{
			light_dir = normalize(light_dir); // magnitude of 1
		}
		else
		{
			light_dir = vec3(0.0); // light is exactly on the surface point, there is no direction
		}

		// attenuation (light falloff)
		float fade = 1.0 - clamp(light_dist / u_light_radius[i], 0.0, 1.0); // without this, inverse square would never be 0 (just approaches it); but when distance > light radius here, it ensures 0
		float attenuation;

		if (u_light_falloff[i] == 1)
		{
			attenuation = u_light_intensity[i] / (1.0 + light_dist * light_dist * u_light_falloff_scale[i]); // inverse relationship with world position scale
			attenuation *= fade;
		}
		else
		{
			attenuation = u_light_intensity[i] * fade;
		}

		// diffuse lighting (surface angle): less brightness if it's coming at an angle to surface
		float diffuse = mix(1.0, max(dot(normalize(v_normal), light_dir), 0.0), u_light_diffuse[i]);

		lit_color += diffuse * attenuation * (u_light_color[i] * u_brightness);
	}


	// STEP 5: FACE SHADING (DEPTH ILLUSION)

	float face_shade;

	if (v_normal.y > 0.5) {
	    face_shade = u_face_shade[0];    // top
	} else if (v_normal.y < -0.5) {
	    face_shade = u_face_shade[1];    // bottom
	} else if (v_normal.z > 0.5) {
	    face_shade = u_face_shade[2];    // front
	} else if (v_normal.z < -0.5) {
	    face_shade = u_face_shade[3];    // back
	} else if (v_normal.x > 0.5) {
	    face_shade = u_face_shade[5];    // right
	} else {
	    face_shade = u_face_shade[4];    // left
	}


	// STEP 6: OUTPUT COLOR

	frag_color = vec4(tex_color * lit_color * face_shade, tex.a);
}
