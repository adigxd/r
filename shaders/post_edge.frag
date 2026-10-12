#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform vec2 u_resolution;

vec2 texel = 1.0 / u_resolution;

vec4 color_center = texture(u_texture, v_uv);

vec4 color_up = texture(u_texture, v_uv + vec2(0.0, texel.y));
vec4 color_down = texture(u_texture, v_uv - vec2(0.0, texel.y));
vec4 color_left = texture(u_texture, v_uv - vec2(texel.x, 0.0));
vec4 color_right = texture(u_texture, v_uv + vec2(texel.x, 0.0));

vec4 color_up_left = texture(u_texture, v_uv + texel * vec2(-1.0, 1.0));
vec4 color_up_right = texture(u_texture, v_uv + texel * vec2(1.0, 1.0));
vec4 color_down_left = texture(u_texture, v_uv + texel * vec2(-1.0, -1.0));
vec4 color_down_right = texture(u_texture, v_uv + texel * vec2(1.0, -1.0));

float luminance(vec4 color) {
    return dot(color.rgb, vec3(0.299, 0.587, 0.114)); // luminance
}

void main() {
	// float average     = dot(color_center.rgb, vec3(0.333));
	float max_channel = max(max(color_center.r, color_center.g), color_center.b);
	float skip_threshold = 0.9375;

	if(max_channel <= skip_threshold)
	{
		float lum_ul = luminance(texture(u_texture, v_uv + texel * vec2(-1,  1)));
		float lum_u  = luminance(texture(u_texture, v_uv + texel * vec2( 0,  1)));
		float lum_ur = luminance(texture(u_texture, v_uv + texel * vec2( 1,  1)));

		float lum_l  = luminance(texture(u_texture, v_uv + texel * vec2(-1, 0)));
		float lum_r  = luminance(texture(u_texture, v_uv + texel * vec2( 1, 0)));

		float lum_dl = luminance(texture(u_texture, v_uv + texel * vec2(-1, -1)));
		float lum_d  = luminance(texture(u_texture, v_uv + texel * vec2( 0, -1)));
		float lum_dr = luminance(texture(u_texture, v_uv + texel * vec2( 1, -1)));

		float grad_x = -1.0 * lum_ul + 1.0 * lum_ur +
					   -2.0 * lum_l  + 2.0 * lum_r +
					   -1.0 * lum_dl + 1.0 * lum_dr;

		float grad_y =  1.0 * lum_ul + 2.0 * lum_u + 1.0 * lum_ur +
					   -1.0 * lum_dl - 2.0 * lum_d - 1.0 * lum_dr;

		float edge_strength = sqrt(grad_x * grad_x + grad_y * grad_y);

		frag_color = vec4(vec3(0.0, 0.0, edge_strength), 1.0);
	}

	else
	{
		frag_color = vec4(color_center);
	}
}
