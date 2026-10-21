#version 330 core

in vec2 v_uv;

uniform sampler2D u_texture; // white text with its shape in the alpha
uniform vec4 u_color;
uniform int u_textured; // 1 = text (the color times the texture), 0 = a plain rectangle

out vec4 frag_color;

void main()
{
    frag_color = (u_textured == 1) ? u_color * texture(u_texture, v_uv) : u_color;
}
