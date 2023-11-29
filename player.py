import numpy as np
from numpy import array


# generated using chatgpt
def are_rectangles_intersecting(rect1, rect2):
    # Check for intersection along each axis
    x_intersect = (rect1[0][0] <= rect2[1][0] and rect1[1][0] >= rect2[0][0])
    y_intersect = (rect1[0][1] <= rect2[1][1] and rect1[1][1] >= rect2[0][1])
    z_intersect = (rect1[0][2] <= rect2[1][2] and rect1[1][2] >= rect2[0][2])

    # If there is an intersection along all three axes, the rectangles intersect
    return x_intersect and y_intersect and z_intersect


class Player:
    def __init__(self, player_block, game_blocks):
        self.block = player_block
        self.game_blocks = game_blocks
        bot = player_block.bottom_corner
        top = player_block.top_corner
        x_width = top[0] - bot[0]
        height = top[1] - bot[1]
        z_width = top[2] - bot[2]
        self.size = array([x_width, height, z_width], dtype=np.float64)
        self.pos = array([bot[0], bot[1], bot[2]], dtype=np.float64)
        self.velocity = array([0, 7, 0], dtype=np.float64)
        self.world_hierarchy = None

    def update_position(self, dt):
        self.pos += self.velocity * dt
        self.block.set_corners(self.pos, self.pos + self.size)
        # this feels right but I didn't check the math -> need to verify this is valid
        self.velocity[1] += -1.2 * np.sqrt(dt)

        # get the index for the player front rect face rect based on the direction (leading edges)
        x_wall_idx = 2 if self.velocity[0] < 0 else 5
        y_wall_idx = 0 if self.velocity[1] < 0 else 3
        z_wall_idx = 1 if self.velocity[2] < 0 else 4

        bot_shift = array([
            self.velocity[0] if self.velocity[0] < 0 else 0,
            self.velocity[1] if self.velocity[0] < 1 else 0,
            self.velocity[2] if self.velocity[0] < 2 else 0,
        ])
        top_shift = array([
            self.velocity[0] if self.velocity[0] > 0 else 0,
            self.velocity[1] if self.velocity[0] > 1 else 0,
            self.velocity[2] if self.velocity[0] > 2 else 0,
        ])

        moving_rect = (self.pos - bot_shift, self.pos + self.size + top_shift)
        # valid_planes = self.find_planes(moving_rect)
        # print(valid_planes)

    def assign_world_hierarchy(self, hierarchy):
        self.world_hierarchy = hierarchy

    def find_planes(self, moving_rect):
        pass
        # using in-place traversal method as trace.cl
        # index = 1  # start at left 1 in order to skip player rect
        # prev_index = 0
        # tree_size = self.world_hierarchy.shape[0]
        # while True:
        #     if prev_index == index * 2 + 2 \
        #         or index >= tree_size \
        #         or !self.world_hierarchy[index].initialized \
        #         or within
        #
        #
        #
        # return 1
