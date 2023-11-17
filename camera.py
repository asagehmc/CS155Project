from custom_types import *


class Camera:

    def __init__(self, camera_buffer):
        self.camera_buffer = camera_buffer

    def set_position(self, x, y, z):
        self.camera_buffer["position"][0] = (x, y, z)

    def set_direction(self, x, y, z):
        # when setting camera direction, we want to have the "right" direction be always horizontal
        # in the xz plane, it should form a right angle with the xz component of the new direction.
        direction = np.array([x, y, z])
        dir_norm = np.divide(direction, np.linalg.norm(direction))
        right = np.array([-z, 0, x])
        up = np.cross(right, dir_norm)
        self.camera_buffer["forward"][0] = (dir_norm[0], dir_norm[1], dir_norm[2])
        self.camera_buffer["right"][0] = (right[0], right[1], right[2])
        self.camera_buffer["up"][0] = (up[0], up[1], up[2])

    def get_position(self):
        return self.camera_buffer["position"][0]