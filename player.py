import numpy as np
from numpy import array


class Player:
    def __init__(self, player_block, game_blocks):
        self.player_block = player_block
        self.game_blocks = game_blocks
        bot = player_block.get_lower_corner()
        top = player_block.get_upper_corner()
        x_width = top[0] - bot[0]
        height = top[1] - bot[1]
        z_width = top[2] - bot[2]
        self.size = array([x_width, height, z_width], dtype=np.float64)
        self.pos = array([bot[0], bot[1], bot[2]], dtype=np.float64)
        self.velocity = array([0, 0, 0], dtype=np.float64)

    def update_position(self, dt):
        self.pos += self.velocity * dt
        self.player_block.set_corners(self.pos, self.pos + self.size)
        # self.velocity[1] += -9.8 * dt



