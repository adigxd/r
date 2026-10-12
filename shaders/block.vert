#version 330 core

layout (location = 0) in vec3 a_pos;
layout (location = 1) in vec3 a_normal;
layout (location = 2) in vec2 a_uv;

flat out float v_cell_x; // to fragment shader
flat out float v_cell_z; // to fragment shader
flat out float v_cell_y; // to fragment shader

out vec3 v_world_pos; // actual position after model matrix
flat out vec3 v_normal; // normal vector for light
out vec2 v_uv; // texture vector

uniform mat4 u_model; // model transformation
uniform mat4 u_view; // camera view transformation
uniform mat4 u_projection; // perspective projection

void main()
{
    v_cell_x = floor(a_pos.x);
    v_cell_z = floor(a_pos.z);
    v_cell_y = floor(a_pos.y);

    v_world_pos = vec3(u_model * vec4(a_pos, 1.0));
	v_normal = mat3(transpose(inverse(u_model))) * a_normal; // transform normal (idk)
    v_uv = a_uv;

    gl_Position = u_projection * u_view * u_model * vec4(a_pos, 1.0); // transform vertex

    // how it works:
    // a_pos       = where the vertex is in the block's local space
    // v_world_pos = where the vertex actually is in the world
    // pos * u_view * u_projection = where it ends up on screen
}
