#version 330 core

out vec4 FragColor; // Output color

flat in float ALT; // from vertex shader
flat in float X;   // from vertex shader
flat in float Z;   // from vertex shader

uniform vec3 COL_DEF; // Custom uniform for coloring

uniform vec3 COL_MIN;
uniform vec3 COL_MAX;

uniform float SIZ;

uniform float ALT_MIN;
uniform float ALT_MAX;

void main()
{
    FragColor = vec4(vec3(1.0), 1.0);
}
