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
	float ALT_FIX = ALT; // clamp(ALT, ALT_MIN, ALT_MAX);

    float ALT_RAT = (ALT_FIX - ALT_MIN) / (ALT_MAX - ALT_MIN);

    float X_FIX = abs(X + SIZ / 2);
    float Z_FIX = abs(Z + SIZ / 2);

    float X_RAT = X_FIX / SIZ;
    float Z_RAT = Z_FIX / SIZ;

    float DIS = ((X + Z) / 2) / SIZ;

    vec3 COL_MIN = vec3(0.0, 0.0, 0.0);
    vec3 COL_MAX = vec3(1.0, 1.0, 1.0);

    vec3 COL_RED = vec3(1.0, 0.0, 0.0);
    vec3 COL_GRE = vec3(0.0, 1.0, 0.0);
    vec3 COL_BLU = vec3(0.0, 0.0, 1.0);

    vec3 COL_YEL = vec3(1.0, 1.0, 0.0);
    vec3 COL_CYA = vec3(0.0, 1.0, 1.0);
    vec3 COL_PUR = vec3(1.0, 0.0, 1.0);

    vec3 COL = mix(mix(COL_CYA, COL_PUR, Z_RAT), mix(COL_RED, COL_YEL, X_RAT), ALT_RAT);

    FragColor = vec4(COL, 1.0);
}
