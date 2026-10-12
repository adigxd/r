#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform vec2 u_resolution;

void main() {
	vec4 color = texture(u_texture, v_uv);

    frag_color = vec4(color);
}
