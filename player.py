import numpy as np
from numpy import array


# generated using chatgpt
def are_blocks_intersecting(rect1, rect2):
    # Check for intersection along each axis
    x_intersect = (rect1[0][0] <= rect2[1][0] and rect1[1][0] >= rect2[0][0])
    y_intersect = (rect1[0][1] <= rect2[1][1] and rect1[1][1] >= rect2[0][1])
    z_intersect = (rect1[0][2] <= rect2[1][2] and rect1[1][2] >= rect2[0][2])

    # If there is an intersection along all three axes, the rectangles intersect
    return x_intersect and y_intersect and z_intersect


def check_plane(plane, moving_rect, x_planes, y_planes, z_planes):
    if are_blocks_intersecting((plane.bottom, plane.top), moving_rect):
        if plane.normal[0] != 0:
            x_planes.append(plane)
        elif plane.normal[1] != 0:
            y_planes.append(plane)
        else:
            z_planes.append(plane)


class Player:
    # makes it easier to do collision calculations on an axis index
    axis_names = ["x", "y", "z"]

    def __init__(self, player_block):
        self.block = player_block
        bot = player_block.bottom_corner
        top = player_block.top_corner
        x_width = top[0] - bot[0]
        height = top[1] - bot[1]
        z_width = top[2] - bot[2]
        self.size = array([x_width, height, z_width], dtype=np.float64)
        self.pos = array([bot[0], bot[1], bot[2]], dtype=np.float64)
        self.velocity = array([0, 7, 0], dtype=np.float64)
        self.world_hierarchy = None
        self.rects = None

    def update_position(self, dt):
        self.pos += self.velocity * dt
        self.block.set_corners(self.pos, self.pos + self.size)
        self.velocity[1] += -9.8 * dt

        # get the index for the player front rect face rect based on the direction (leading edges)
        x_player_wall_index = 2 if self.velocity[0] < 0 else 5
        y_player_wall_index = 0 if self.velocity[1] < 0 else 3
        z_player_wall_index = 1 if self.velocity[2] < 0 else 4
        player_wall_indexes = [x_player_wall_index, y_player_wall_index, z_player_wall_index]

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
        axis_planes = self.find_planes(moving_rect)

        for axis in range(3):
            if self.velocity[axis] == 0:
                continue
            inv_axis = self.velocity[axis]
            player_leading_edge = self.rects[player_wall_indexes[axis]].top[self.axis_names[axis]]
            for plane in axis_planes[axis]:
                plane_pos = plane.top[self.axis_names[axis]]
                dist_to_travel = plane_pos - player_leading_edge



    def assign_world_bufs(self, rects, hierarchy):
        self.rects = rects
        self.world_hierarchy = hierarchy

    # find the planes that the player could possibly collide with
    # (find all planes that exist in a bounding box which intersects with the players movement rect)
    def find_planes(self, moving_rect):
        # using in-place traversal method as trace.cl
        x_planes = [] # an x-plane is one which is normal to the x axis
        y_planes = []
        z_planes = []
        index = 1  # start at left 1 in order to skip player rect
        prev_index = 0
        tree_size = self.world_hierarchy.shape[0]
        while True:
            coming_from_right = (prev_index == index * 2 + 2)
            out_of_tree = (index >= tree_size or not self.world_hierarchy[index].initialized)
            intersecting = are_blocks_intersecting(moving_rect, (self.world_hierarchy[index].bottom,
                                                                 self.world_hierarchy[index].top))

            if coming_from_right or out_of_tree or not intersecting:
                prev_index = index
                index = (index - 1) >> 1
                if index == 1:
                    break
            if self.world_hierarchy[index].plane1 != -1:
                # pass in the rectangle pointed to by plane1
                check_plane(self.rects[self.world_hierarchy[index].plane1],
                                 moving_rect, x_planes, y_planes, z_planes)
            if self.world_hierarchy[index].plane2 != -1:
                check_plane(self.rects[self.world_hierarchy[index].plane2],
                                 moving_rect, x_planes, y_planes, z_planes)
            if prev_index < index:  # coming from parent node, go left
                prev_index = index
                index = index * 2 + 1
            elif prev_index == index * 2 + 1:  # coming from left node, then go right
                prev_index = index
                index = index * 2 + 2
        return x_planes, y_planes, z_planes