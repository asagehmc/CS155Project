import numpy as np
from numpy import array


# an annoying side effect of custom data types needing to be indexed by name only
# wonder if there is a way to not need this function?
def add_to_vector_type(v_type, v2):
    return v_type.x + v2[0], v_type.y + v2[1], v_type.z + v2[2]


# generated using chatgpt
# axis to ignore is used to avoid floating point error issues for plane-plane intersection
def are_blocks_intersecting(rect1, rect2, axis_to_ignore=-1):
    # Check for intersection along each axis
    x_intersect = (rect1[0][0] <= rect2[1][0] and rect1[1][0] >= rect2[0][0]) or axis_to_ignore == 0
    y_intersect = (rect1[0][1] <= rect2[1][1] and rect1[1][1] >= rect2[0][1]) or axis_to_ignore == 1
    z_intersect = (rect1[0][2] <= rect2[1][2] and rect1[1][2] >= rect2[0][2]) or axis_to_ignore == 2

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
        self.move(self.velocity * dt)
        self.block.set_corners(self.pos, self.pos + self.size)
        self.velocity[1] += -9.8 * dt

    def move(self, move_vec, limit=3):
        # failsafe to prevent hangs
        if limit == 0:
            return
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
        closest_hit_dist_sq = float("inf")
        closest_hit_axis_v = 0
        closest_hit_axis = -1
        closest_hit_scalar = -1

        for axis in range(3):
            if self.velocity[axis] == 0:
                continue
            inv_axis = 1 / self.velocity[axis]
            player_leading_edge = self.rects[player_wall_indexes[axis]].top[self.axis_names[axis]]
            for plane in axis_planes[axis]:
                plane_pos = plane.top[self.axis_names[axis]]
                dist_to_travel = plane_pos - player_leading_edge
                move_vec_scalar = inv_axis * dist_to_travel
                move_vec = self.velocity * move_vec_scalar
                travel_dist_sq = np.dot(move_vec, move_vec)
                # if this movement is further than a collision we already have, skip it.
                if travel_dist_sq > closest_hit_dist_sq:
                    continue
                # if there's a corner hit, tiebreak by whichever axis velocity is faster
                if travel_dist_sq == closest_hit_dist_sq and closest_hit_axis_v > self.velocity[axis]:
                    continue
                new_projected_plane = (add_to_vector_type(player_leading_edge.bottom, move_vec),
                                       add_to_vector_type(player_leading_edge.top, move_vec))
                if are_blocks_intersecting(new_projected_plane, plane_pos, axis):
                    closest_hit_dist_sq = travel_dist_sq
                    closest_hit_axis_v = self.velocity[axis]
                    closest_hit_axis = axis
                    closest_hit_scalar = move_vec_scalar

        if closest_hit_axis != -1:
            self.pos = self.pos + move_vec * closest_hit_scalar
            move_vec[closest_hit_axis] = 0
            # do a little bit of a bounce
            self.velocity[closest_hit_axis] *= -.2
            self.move(move_vec, limit-1)

    def assign_world_bufs(self, rects, hierarchy):
        self.rects = rects
        self.world_hierarchy = hierarchy

    # find the planes that the player could possibly collide with
    # (find all planes that exist in a bounding box which intersects with the players movement rect)
    def find_planes(self, moving_rect):
        # using in-place traversal method as trace.cl
        x_planes = []  # an x-plane is one which is normal to the x axis
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
