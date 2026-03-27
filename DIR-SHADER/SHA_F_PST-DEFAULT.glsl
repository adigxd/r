#version 330 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D TXT;
uniform vec2 RES;

void main() {
	vec4 COL = texture(TXT, TexCoord);
	
    FragColor = vec4(COL);
}
