import numpy as np
from OpenGL.GL import *

def model_matrix(pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    # Create translation matrix and set last column (except w) to position values
    translation = np.identity(4, dtype=np.float32)
    translation[0:3, 3] = pos # Sets x,y,z translation in 4th column

    # Create 3 separate rotation matrices for x,y,z axes
    rot_x = np.identity(4, dtype=np.float32)
    rot_y = np.identity(4, dtype=np.float32)
    rot_z = np.identity(4, dtype=np.float32)

    # X rotation matrix - rotates around x axis
    rot_x[1,1] = np.cos(rot[0]) # cos θ
    rot_x[1,2] = -np.sin(rot[0]) # -sin θ
    rot_x[2,1] = np.sin(rot[0]) # sin θ
    rot_x[2,2] = np.cos(rot[0]) # cos θ

    # Y rotation matrix - rotates around y axis
    rot_y[0,0] = np.cos(rot[1]) # cos θ
    rot_y[0,2] = np.sin(rot[1]) # sin θ
    rot_y[2,0] = -np.sin(rot[1]) # -sin θ
    rot_y[2,2] = np.cos(rot[1]) # cos θ

    # Z rotation matrix - rotates around z axis
    rot_z[0,0] = np.cos(rot[2]) # cos θ
    rot_z[0,1] = -np.sin(rot[2]) # -sin θ
    rot_z[1,0] = np.sin(rot[2]) # sin θ
    rot_z[1,1] = np.cos(rot[2]) # cos θ

    # Scale matrix - stretches/shrinks along each axis
    scaling = np.identity(4, dtype=np.float32)
    scaling[0,0] = scale[0] # X scale
    scaling[1,1] = scale[1] # Y scale
    scaling[2,2] = scale[2] # Z scale

    # Combine all transforms in order: translate * rotX * rotY * rotZ * scale
    return translation @ rot_x @ rot_y @ rot_z @ scaling

def view_matrix(cam_pos, cam_rot):
    # Convert camera rotation angles from degrees to radians
    pitch = np.radians(cam_rot[0]) # Up/down rotation
    yaw = np.radians(cam_rot[1]) # Left/right rotation

    # Calculate forward vector - where camera is looking
    forward = np.array([
        np.sin(yaw) * np.cos(pitch), # X component
        np.sin(pitch), # Y component
        -np.cos(yaw) * np.cos(pitch) # Z component
    ])

    # Calculate right vector using cross product of forward and world-up
    right = np.cross(forward, [0, 1, 0])
    right = right / np.linalg.norm(right) # Normalize to unit length

    # Calculate camera's up vector using cross product of right and forward
    up = np.cross(right, forward)

    # Create rotation part of view matrix
    rotation = np.identity(4, dtype=np.float32)
    rotation[0, 0:3] = right # First row is right vector
    rotation[1, 0:3] = up # Second row is up vector
    rotation[2, 0:3] = -forward # Third row is negative forward vector

    # Create translation matrix
    translation = np.identity(4, dtype=np.float32)
    translation[0:3, 3] = -np.array(cam_pos) # Negative camera position

    # Combine rotation and translation
    return rotation @ translation

def look_direction(cam_rot):
    # the direction the camera looks in, from [pitch, yaw] in degrees (the same as in view_matrix)
    pitch = np.radians(cam_rot[0])
    yaw = np.radians(cam_rot[1])

    return (np.sin(yaw) * np.cos(pitch), np.sin(pitch), -np.cos(yaw) * np.cos(pitch))

def projection_matrix(fov, aspect, near, far):
    # Convert field of view from degrees to radians
    fov_rad = np.radians(fov)

    # Calculate scaling factor based on FOV
    f = 1.0 / np.tan(fov_rad / 2.0)

    # Create empty 4x4 matrix
    matrix = np.zeros((4, 4), dtype=np.float32)

    # Set perspective transform values
    matrix[0,0] = f / aspect # X scale (adjusted for aspect ratio)
    matrix[1,1] = f # Y scale
    matrix[2,2] = (far + near) / (near - far) # Z scale
    matrix[2,3] = (2.0 * far * near) / (near - far) # Z translation
    matrix[3,2] = -1.0 # Set w coordinate for perspective divide

    return matrix

def frustum_planes(clip):
    # the 6 planes (left, right, bottom, top, near, far) around the space the camera can see; clip is projection @ view
    # each plane is a row [a, b, c, d] with its normal (a, b, c) pointing inwards, so a point (x, y, z) is on the visible side when a*x + b*y + c*z + d >= 0
    rows = np.asarray(clip, dtype=np.float64)
    planes = np.array([
        rows[3] + rows[0], # left
        rows[3] - rows[0], # right
        rows[3] + rows[1], # bottom
        rows[3] - rows[1], # top
        rows[3] + rows[2], # near
        rows[3] - rows[2]  # far
    ])

    return planes / np.linalg.norm(planes[:, :3], axis=1)[:, None] # normal of length 1, so that a * x + ... + d is a real distance
