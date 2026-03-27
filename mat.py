import numpy as np
from OpenGL.GL import *

def _GEN_MAT_M(pos=[0,0,0], rot=[0,0,0], scl=[1,1,1]):
    # Create 4x4 identity matrix filled with zeros except diagonal which is 1
    mat = np.identity(4, dtype=np.float32)
    
    # Create translation matrix and set last column (except w) to position values
    mat_trs = np.identity(4, dtype=np.float32)
    mat_trs[0:3, 3] = pos  # Sets x,y,z translation in 4th column

    # Create 3 separate rotation matrices for x,y,z axes
    rot_x = np.identity(4, dtype=np.float32)
    rot_y = np.identity(4, dtype=np.float32)
    rot_z = np.identity(4, dtype=np.float32)
    
    # X rotation matrix - rotates around x axis
    rot_x[1,1] = np.cos(rot[0])     # cos θ
    rot_x[1,2] = -np.sin(rot[0])    # -sin θ
    rot_x[2,1] = np.sin(rot[0])     # sin θ
    rot_x[2,2] = np.cos(rot[0])     # cos θ

    # Y rotation matrix - rotates around y axis
    rot_y[0,0] = np.cos(rot[1])     # cos θ
    rot_y[0,2] = np.sin(rot[1])     # sin θ
    rot_y[2,0] = -np.sin(rot[1])    # -sin θ
    rot_y[2,2] = np.cos(rot[1])     # cos θ

    # Z rotation matrix - rotates around z axis
    rot_z[0,0] = np.cos(rot[2])     # cos θ
    rot_z[0,1] = -np.sin(rot[2])    # -sin θ
    rot_z[1,0] = np.sin(rot[2])     # sin θ
    rot_z[1,1] = np.cos(rot[2])     # cos θ

    # Scale matrix - stretches/shrinks along each axis
    mat_scl = np.identity(4, dtype=np.float32)
    mat_scl[0,0] = scl[0]  # X scale
    mat_scl[1,1] = scl[1]  # Y scale
    mat_scl[2,2] = scl[2]  # Z scale
    
    # Combine all transforms in order: translate * rotX * rotY * rotZ * scale
    mat = mat_trs @ rot_x @ rot_y @ rot_z @ mat_scl
    return mat

def _GEN_MAT_V(cam_pos, cam_rot):
    # Convert camera rotation angles from degrees to radians
    pit = np.radians(cam_rot[0])  # Up/down rotation
    yaw = np.radians(cam_rot[1])    # Left/right rotation

    # Calculate forward vector - where camera is looking
    fwd = np.array([
        np.sin(yaw) * np.cos(pit),   # X component
        np.sin(pit),                  # Y component
        -np.cos(yaw) * np.cos(pit)   # Z component
    ])
    
    # Calculate right vector using cross product of forward and world-up
    rit = np.cross(fwd, [0, 1, 0])
    rit = rit / np.linalg.norm(rit)  # Normalize to unit length
    
    # Calculate camera's up vector using cross product of right and forward
    up = np.cross(rit, fwd)
    
    # Create rotation part of view matrix
    rotation = np.identity(4, dtype=np.float32)
    rotation[0, 0:3] = rit     # First row is right vector
    rotation[1, 0:3] = up        # Second row is up vector
    rotation[2, 0:3] = -fwd  # Third row is negative forward vector
    
    # Create translation matrix
    translation = np.identity(4, dtype=np.float32)
    translation[0:3, 3] = -np.array(cam_pos)  # Negative camera position
    
    # Combine rotation and translation
    return rotation @ translation

def _GEN_MAT_P(fov, res_rat, see_min, see_max):
    # Convert field of view from degrees to radians
    fov_rad = np.radians(fov)

    # Calculate scaling factor based on FOV
    f = 1.0 / np.tan(fov_rad / 2.0)
    
    # Create empty 4x4 matrix
    mat = np.zeros((4, 4), dtype=np.float32)
    
    # Set perspective transform values
    mat[0,0] = f / res_rat    # X scale (adjusted for aspect ratio)
    mat[1,1] = f             # Y scale
    mat[2,2] = (see_max + see_min) / (see_min - see_max)     # Z scale
    mat[2,3] = (2.0 * see_max * see_min) / (see_min - see_max)  # Z translation
    mat[3,2] = -1.0  # Set w coordinate for perspective divide

    return mat