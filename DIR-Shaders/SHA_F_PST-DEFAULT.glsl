#version 330 core

in vec2 TEX_OUT;
out vec4 COL_FNL;

uniform sampler2D TEX;
uniform vec2 RES;

void main() {
	vec4 COL = texture(TEX, TEX_OUT);
	
    COL_FNL = vec4(COL);
}
