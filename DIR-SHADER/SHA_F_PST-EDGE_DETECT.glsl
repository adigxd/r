#version 330 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D TXT;
uniform vec2 RES;

vec2 TXL_SIZ = 1.0 / RES;

vec4 COL_C = texture(TXT, TexCoord);

vec4 COL_U = texture(TXT, TexCoord + vec2(0.0, TXL_SIZ.y));
vec4 COL_D = texture(TXT, TexCoord - vec2(0.0, TXL_SIZ.y));
vec4 COL_L = texture(TXT, TexCoord - vec2(TXL_SIZ.x, 0.0));
vec4 COL_R = texture(TXT, TexCoord + vec2(TXL_SIZ.x, 0.0));

vec4 COL_UL = texture(TXT, TexCoord + TXL_SIZ * vec2(-1.0, 1.0));
vec4 COL_UR = texture(TXT, TexCoord + TXL_SIZ * vec2(1.0, 1.0));
vec4 COL_DL = texture(TXT, TexCoord + TXL_SIZ * vec2(-1.0, -1.0));
vec4 COL_DR = texture(TXT, TexCoord + TXL_SIZ * vec2(1.0, -1.0));

float __GS_(vec4 COL) {
    return dot(COL.rgb, vec3(0.299, 0.587, 0.114)); // luminance
}

void main() {
	// float COL_AVG     = dot(COL_C.rgb, vec3(0.333));
	float COL_MAX_CNL = max(max(COL_C.r, COL_C.g), COL_C.b);
	float COL_MIN_SKP = 0.9375;

	if(COL_MAX_CNL <= COL_MIN_SKP)
	{
		float VAL_UL = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2(-1,  1)));
		float VAL_U  = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2( 0,  1)));
		float VAL_UR = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2( 1,  1)));

		float VAL_L  = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2(-1, 0)));
		float VAL_R  = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2( 1, 0)));

		float VAL_DL = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2(-1, -1)));
		float VAL_D  = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2( 0, -1)));
		float VAL_DR = __GS_(texture(TXT, TexCoord + TXL_SIZ * vec2( 1, -1)));

		float GRD_X = -1.0 * VAL_UL + 1.0 * VAL_UR +
					  -2.0 * VAL_L  + 2.0 * VAL_R +
					  -1.0 * VAL_DL + 1.0 * VAL_DR;

		float GRD_Y =  1.0 * VAL_UL + 2.0 * VAL_U + 1.0 * VAL_UR +
					  -1.0 * VAL_DL - 2.0 * VAL_D - 1.0 * VAL_DR;

		float EDG_MAG = sqrt(GRD_X * GRD_X + GRD_Y * GRD_Y);

		FragColor = vec4(vec3(0.0, 0.0, EDG_MAG), 1.0);
	}
	
	else
	{
		FragColor = vec4(COL_C);
	}
}
