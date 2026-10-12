#version 330 core

out vec4 frag_color; // output color

flat in float v_cell_x; // from vertex shader
flat in float v_cell_z; // from vertex shader
flat in float v_cell_y; // from vertex shader

in vec3 v_world_pos;
flat in vec3 v_normal;
in vec2 v_uv;

uniform sampler2D u_atlas; // texture atlas

uniform vec3 u_light_pos;
uniform vec3 u_light_color;
uniform float u_light_intensity;
uniform float u_light_radius;

vec3 ramp_color(float ratio)
{
	// return vec3(0.5, 0.5, 0.5); // testing

    float stop_0 = 0.200;
    float stop_1 = 0.400;
    float stop_2 = 0.600;
    float stop_3 = 0.800;
    float stop_4 = 1.000;

	vec3 gray_0 = vec3(0.0, 0.0, 0.0);
	vec3 gray_1 = vec3(0.17, 0.17, 0.17);
	vec3 gray_2 = vec3(0.33, 0.33, 0.33);
	vec3 gray_3 = vec3(0.5, 0.5, 0.5);
	vec3 gray_4 = vec3(0.67, 0.67, 0.67);
	vec3 gray_5 = vec3(0.83, 0.83, 0.83);

	if(ratio <= stop_0) { return mix(gray_0, gray_1, 5 * ratio); }
	if(ratio <= stop_1) { return mix(gray_1, gray_2, 5 * (ratio - stop_0)); }
	if(ratio <= stop_2) { return mix(gray_2, gray_3, 5 * (ratio - stop_1)); }
	if(ratio <= stop_3) { return mix(gray_3, gray_4, 5 * (ratio - stop_2)); }
	if(ratio <= stop_4) { return mix(gray_4, gray_5, 5 * (ratio - stop_3)); }
	else                { return vec3(1.0, 1.0, 1.0); } // this should never happen
}

void main()
{
	// STEP 1: GRAB COLOR FROM TEXTURE

	vec3 tex_color = texture(u_atlas, v_uv).rgb;
	//vec3 color = ramp_color(frac_color);
	//color = mix(color, vec3(1.0, 1.0, 1.0), 0.875); // brighten it up a bit before lighting


	// STEP 2: LIGHT DIRECTION AND DISTANCE

	vec3 block_pos = floor(v_world_pos - v_normal * 0.5);
	vec3 block_center = block_pos + vec3(0.5);
	vec3 light_dir = u_light_pos - block_center; // direction from pixel to light
	float light_dist = length(light_dir); // distance magnitude
	light_dir = normalize(light_dir); // magnitude of 1


	// STEP 3: ATTENUATION (LIGHT FALLOFF)

	float attenuation = u_light_intensity * (1.0 - clamp(light_dist / u_light_radius, 0.0, 1.0));
	//float attenuation = u_light_intensity / (1.0 + light_dist * light_dist * 1); // last number is arbitrary; inverse relationship with world position scale
	//attenuation *= 1.0 - clamp(light_dist / u_light_radius, 0.0, 1.0); // without this, light would never be 0 (just approaches it); but when distance > light radius here, it ensures 0


	// STEP 4: DIFFUSE LIGHTING (SURFACE ANGLE)

	float diffuse = max(dot(normalize(v_normal), light_dir), 0.0); // less brightness if it's coming at an angle to surface


	// STEP 5: FACE SHADING (DEPTH ILLUSION)

	float face_shade;

	if (v_normal.y > 0.5) {
	    face_shade = 1.0;    // top
	} else if (v_normal.y < -0.5) {
	    face_shade = 0.75;    // bottom
	} else if (v_normal.z > 0.5) {
	    face_shade = 0.916;    // front
	} else if (v_normal.z < -0.5) {
	    face_shade = 0.916;    // back
	} else if (v_normal.x > 0.5) {
	    face_shade = 0.833;    // right
	} else {
	    face_shade = 0.833;    // left
	}


	// STEP 6: AMBIENT LIGHTING

	float ambient = 0.0625; // hard-coded so every surface gets at least some brightness to prevent full black


	// STEP 7: COMBINE

	vec3 lit_color = (ambient + diffuse * attenuation) * (u_light_color * 0.5);


	// STEP 8: OUTPUT COLOR

	frag_color = vec4(tex_color * lit_color * face_shade, 1.0);
}
