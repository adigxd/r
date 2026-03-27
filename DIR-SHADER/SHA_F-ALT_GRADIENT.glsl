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
    float ALT_FIX = ALT; clamp(ALT, ALT_MIN, ALT_MAX);

    float ALT_RAT = (ALT_FIX - ALT_MIN) / (ALT_MAX - ALT_MIN);

    vec3 COL = mix(COL_MIN, COL_MAX, ALT_RAT);

    FragColor = vec4(COL, 1.0);
}
