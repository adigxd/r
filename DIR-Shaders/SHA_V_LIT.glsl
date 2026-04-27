#version 330 core

layout (location = 0) in vec3 POS;
layout (location = 1) in vec3 NML;
layout (location = 2) in vec2 TEX;

flat out float X; // to fragment shader
flat out float Z; // to fragment shader
flat out float Y; // to fragment shader

out vec3 POS_ACT_OUT; // actual position after model matrix
flat out vec3 NML_OUT; // normal vector for light
out vec2 TEX_OUT; // texture vector

uniform mat4 MAT_M; // model transformation
uniform mat4 MAT_V; // camera view transformation
uniform mat4 MAT_P; // perspective projection

void main()
{
    X = floor(POS.x);
    Z = floor(POS.z);
    Y = floor(POS.y);
	
    POS_ACT_OUT = vec3(MAT_M * vec4(POS, 1.0));
	NML_OUT = mat3(transpose(inverse(MAT_M))) * NML; // transform normal (idk)
    TEX_OUT = TEX;

    gl_Position = MAT_P * MAT_V * MAT_M * vec4(POS, 1.0); // transform vertex

    // how it works: 
    // POS       = where the vertex is in the block's local space
    // POS_WLD   = where the vertex actually is in the world
    // POS * MAT_V * MAT_P = where it ends up on screen
}
