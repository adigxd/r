#version 330 core

// draws flat rectangles on the window (the chat): a_pos is in pixels from the top left of the window

layout (location = 0) in vec2 a_pos;
layout (location = 1) in vec2 a_uv;

uniform vec2 u_screen; // size of the window in pixels

out vec2 v_uv;

void main()
{
    gl_Position = vec4(a_pos.x / u_screen.x * 2.0 - 1.0, 1.0 - a_pos.y / u_screen.y * 2.0, 0.0, 1.0);
    v_uv = a_uv;
}
