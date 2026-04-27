#version 330 core

out vec4 COL_FNL; // output color

flat in float X; // from vertex shader
flat in float Z; // from vertex shader
flat in float Y; // from vertex shader

in vec3 POS_ACT_OUT;
flat in vec3 NML_OUT;
in vec2 TEX_OUT;

uniform sampler2D ATL; // texture atlas

uniform vec3 LIT_POS;
uniform vec3 LIT_COL;
uniform float LIT_INT;
uniform float LIT_RAD;

vec3 COL_FNC(float RAT)
{
	// return vec3(0.5, 0.5, 0.5); // testing
	
    float RAT_MAX_0 = 0.200;
    float RAT_MAX_1 = 0.400;
    float RAT_MAX_2 = 0.600;
    float RAT_MAX_3 = 0.800;
    float RAT_MAX_4 = 1.000;
    
	vec3 COL_R = vec3(0.0, 0.0, 0.0);
	vec3 COL_Y = vec3(0.17, 0.17, 0.17);
	vec3 COL_G = vec3(0.33, 0.33, 0.33);
	vec3 COL_C = vec3(0.5, 0.5, 0.5);
	vec3 COL_B = vec3(0.67, 0.67, 0.67);
	vec3 COL_M = vec3(0.83, 0.83, 0.83);
	
	if(RAT <= RAT_MAX_0) { return mix(COL_R, COL_Y, 5 * RAT); }
	if(RAT <= RAT_MAX_1) { return mix(COL_Y, COL_G, 5 * (RAT - RAT_MAX_0)); }
	if(RAT <= RAT_MAX_2) { return mix(COL_G, COL_C, 5 * (RAT - RAT_MAX_1)); }
	if(RAT <= RAT_MAX_3) { return mix(COL_C, COL_B, 5 * (RAT - RAT_MAX_2)); }
	if(RAT <= RAT_MAX_4) { return mix(COL_B, COL_M, 5 * (RAT - RAT_MAX_3)); }
	else                 { return vec3(1.0, 1.0, 1.0); } // this should never happen
}

void main()
{
	// STEP 1: GRAB COLOR FROM TEXTURE

	vec3 COL_TEX = texture(ATL, TEX_OUT).rgb;
	//vec3 COL = COL_FNC(FRC_COL);
	//COL = mix(COL, vec3(1.0, 1.0, 1.0), 0.875); // brighten it up a bit before lighting
	
	
	// STEP 2: LIGHT DIRECTION AND DISTANCE
	
	vec3 POS_BLC = floor(POS_ACT_OUT - NML_OUT * 0.5);
	vec3 POS_BLC_CTR = POS_BLC + vec3(0.5);
	vec3 LIT_DIR = LIT_POS - POS_BLC_CTR; // direction from pixel to light
	float LIT_DIS = length(LIT_DIR); // distance magnitude
	LIT_DIR = normalize(LIT_DIR); // magnitude of 1
	
	
	// STEP 3: ATTENUATION (LIGHT FALLOFF)
	
	float LIT_ATN = LIT_INT * (1.0 - clamp(LIT_DIS / LIT_RAD, 0.0, 1.0));
	//float LIT_ATN = LIT_INT / (1.0 + LIT_DIS * LIT_DIS * 1); // last number is arbitrary; inverse relationship with world position scale
	//LIT_ATN *= 1.0 - clamp(LIT_DIS / LIT_RAD, 0.0, 1.0); // without this, light would never be 0 (just approaches it); but when distance > light radius here, it ensures 0
	
	
	// STEP 4: DIFFUSE LIGHTING (SURFACE ANGLE)
	
	float LIT_DIF = max(dot(normalize(NML_OUT), LIT_DIR), 0.0); // less brightness if it's coming at an angle to surface


	// STEP 5: FACE SHADING (DEPTH ILLUSION)

	float COL_SHD;

	if (NML_OUT.y > 0.5) {
	    COL_SHD = 1.0;    // top
	} else if (NML_OUT.y < -0.5) {
	    COL_SHD = 0.75;    // bottom
	} else if (NML_OUT.z > 0.5) {
	    COL_SHD = 0.916;    // front
	} else if (NML_OUT.z < -0.5) {
	    COL_SHD = 0.916;    // back
	} else if (NML_OUT.x > 0.5) {
	    COL_SHD = 0.833;    // right
	} else {
	    COL_SHD = 0.833;    // left
	}
	
	
	// STEP 6: AMBIENT LIGHTING
	
	float LIT_AMB = 0.0625; // hard-coded so every surface gets at least some brightness to prevent full black
	
	
	// STEP 7: COMBINE
	
	vec3 COL_LIT = (LIT_AMB + LIT_DIF * LIT_ATN) * (LIT_COL * 0.5);


	// STEP 8: OUTPUT COLOR

	COL_FNL = vec4(COL_TEX * COL_LIT * COL_SHD, 1.0);
}
