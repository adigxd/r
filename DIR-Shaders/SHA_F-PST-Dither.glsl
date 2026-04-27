#version 330 core

in vec2 TEX_OUT;
out vec4 COL_FNL;

uniform sampler2D TEX;
uniform vec2 RES;

float FLT_RAN(vec2 co)
{
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main()
{
	const int VAL_CNL_ARR_SIZ = 8;
	float VAL_CNL_ARR[VAL_CNL_ARR_SIZ] = float[](0.000, 0.125, 0.250, 0.375, 0.500, 0.625, 0.750, 0.875); // has to be initialized like this idk y
	const int VAL_CNL_ARR_STP_MIN = 1; // minimum step between blackened pixels for dither, further altered by C in for loop
	
	vec3 COL = texture(TEX, TEX_OUT).rgb;
	
	float VAL = dot(COL, vec3(0.333, 0.333, 0.333));
	
	vec3 COL_FIN = vec3(1.0, 1.0, 0.9375);
	
	for(int C = 0; C < VAL_CNL_ARR_SIZ; C++)
	{
		if(VAL <= VAL_CNL_ARR[C])
		{
			if(mod(floor(TEX_OUT.x * RES.x), VAL_CNL_ARR_STP_MIN * (C + 1)) == 0 && mod(floor(TEX_OUT.y * RES.y), VAL_CNL_ARR_STP_MIN * (C + 1)) == 0)
			{
				COL_FIN = vec3(0.0, 0.0, 0.0625);
			}
			
			break;
		}
	}
	
	COL_FNL = vec4(COL_FIN, 1.0);
	
	//float FLT_RAN_VAL = FLT_RAN(TEX_OUT * RES); // multiple by RES to ensure randomness
	//
	//if(FLT_RAN_VAL < VAL) { COL_FNL = vec4(vec3(1.0), 1.0); }
	//else                  { COL_FNL = vec4(vec3(0.0), 1.0); }
}
