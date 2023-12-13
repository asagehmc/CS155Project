import math

import numpy as np
import pygame
from numpy import array

import util
from custom_types import TOP, BOTTOM, NORMAL

X = 0
Y = 1
Z = 2
BOUNCE = 0.3  # 0 to 1 with 1 being highest
XZ_SPEED = 30
JUMP_SPEED = 30  # 30
SPEED_DECAY = [0.05, 0.999, 0.05]  # closer to zero is faster decay
SPEED_DECAY_SHIFTED = [0.0001, 0.999, 0.0001]  # closer to zero is faster decay

GRAVITY = 100


# an annoying side effect of void types not adding nicely
# wonder if there is a way to not need this function?
def add_void_to_vector(v1, v2):
    return v1[X] + v2[X], v1[Y] + v2[Y], v1[Z] + v2[Z]


# generated using chatgpt
# axis to ignore is used to avoid floating point error issues for plane-plane intersection
def are_blocks_overlapping(rect1, rect2, axis_to_ignore=-1):
    # Check for intersection along each axis
    x_intersect = (rect1[BOTTOM][X] < rect2[TOP][X] and rect1[TOP][X] > rect2[BOTTOM][X]) or axis_to_ignore == X
    y_intersect = (rect1[BOTTOM][Y] < rect2[TOP][Y] and rect1[TOP][Y] > rect2[BOTTOM][Y]) or axis_to_ignore == Y
    z_intersect = (rect1[BOTTOM][Z] < rect2[TOP][Z] and rect1[TOP][Z] > rect2[BOTTOM][Z]) or axis_to_ignore == Z

    # If there is an intersection along all three axes, the rectangles intersect
    return x_intersect and y_intersect and z_intersect


def check_plane(plane, moving_rect, block_idx, x_planes, y_planes, z_planes):
    if are_blocks_overlapping((plane[BOTTOM], plane[TOP]), moving_rect):
        if plane[NORMAL][X] != 0:
            x_planes.append((plane, block_idx))
        elif plane[NORMAL][Y] != 0:
            y_planes.append((plane, block_idx))
        else:
            z_planes.append((plane, block_idx))


class Player:
    touch_directions = [False, False, False]
    touching_blocks = []

    def __init__(self, player_block, buf_wrapper):
        self.block = player_block
        bot = player_block.bottom_corner
        top = player_block.top_corner
        x_width = top[X] - bot[X]
        height = top[Y] - bot[Y]
        z_width = top[Z] - bot[Z]
        self.size = array([x_width, height, z_width], dtype=np.float64)
        self.pos = array([bot[X], bot[Y], bot[Z]], dtype=np.float64)
        self.velocity = array([0, 0, 0], dtype=np.float64)
        self.buf_wrap = buf_wrapper
        self.cheat_death = False

    def set_position(self, pos):
        self.pos = util.triple_sub(pos, self.size/2)
        self.velocity = array([0, 0, 0], dtype=np.float64)
        self.block.set_buf_corners(self.pos, self.pos + self.size)

    def update_position(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d]:
            self.velocity[X] += -XZ_SPEED * dt
        if keys[pygame.K_a]:
            self.velocity[X] += XZ_SPEED * dt
        if keys[pygame.K_w]:
            self.velocity[Z] += XZ_SPEED * dt
        if keys[pygame.K_s]:
            self.velocity[Z] += -XZ_SPEED * dt
        if keys[pygame.K_SPACE] and self.touch_directions[Y] < 0:
            self.velocity[Y] = JUMP_SPEED
        if keys[pygame.K_c]:
            self.velocity[Y] = 0
            if keys[pygame.K_LSHIFT]:
                self.velocity[Y] = 5
        else:
            self.velocity[Y] += -GRAVITY * dt
        if keys[pygame.K_p]:
            self.cheat_death = not self.cheat_death
        self.velocity[Y] += -GRAVITY * dt

        # determine if we should ever "bounce" in a direction (in case frames go low and we get a high dt force)
        prev_touch_directions = self.touch_directions
        self.touch_directions = [0, 0, 0]
        self.touching_blocks = []
        self.move(self.velocity * dt, prev_touch_directions, dt)
        # update graphics positions
        self.block.set_buf_corners(self.pos, self.pos + self.size)
        for i in range(0, 3):
            # slow the player down a bit, more if shifting
            self.velocity[i] *= math.pow((SPEED_DECAY_SHIFTED if keys[pygame.K_LSHIFT] else SPEED_DECAY)[i], dt)

    def move(self, move_vec, last_touch_directions, dt, limit=3, ):
        # failsafe to prevent hangs
        if limit == 0:
            return
        # get the index for the player front rect face rect based on the direction (leading edges)
        x_player_wall_index = 2 if move_vec[X] < 0 else 5
        y_player_wall_index = 0 if move_vec[Y] < 0 else 3
        z_player_wall_index = 1 if move_vec[Z] < 0 else 4
        player_wall_indexes = [x_player_wall_index, y_player_wall_index, z_player_wall_index]

        bot_shift = array([
            move_vec[X] if move_vec[X] < 0 else 0,
            move_vec[Y] if move_vec[Y] < 0 else 0,
            move_vec[Z] if move_vec[Z] < 0 else 0,
        ])
        top_shift = array([
            move_vec[X] if move_vec[X] > 0 else 0,
            move_vec[Y] if move_vec[Y] > 0 else 0,
            move_vec[Z] if move_vec[Z] > 0 else 0,
        ])

        moving_rect = (self.pos + bot_shift, self.pos + self.size + top_shift)
        axis_planes = self.find_planes(moving_rect)
        closest_hit_dist_sq = float("inf")
        closest_hit_axis_v = 0
        closest_hit_axis = -1
        closest_hit_scalar = -1
        closest_hit_pos = 0
        closest_y_hit_dist_sq = -1
        closest_hit_block = -1
        for axis in range(3):
            if move_vec[axis] == 0:
                continue
            inv_axis = 1 / move_vec[axis]
            # get the upper axis coordinate of the leading face in the axis direction
            player_leading_edge = self.buf_wrap.rects[player_wall_indexes[axis]]
            for plane, block_idx in axis_planes[axis]:
                plane_pos = plane[BOTTOM][axis]
                dist_to_travel = plane_pos - player_leading_edge[BOTTOM][axis]
                move_vec_scalar = inv_axis * dist_to_travel
                # trim any rectangles that we don't want to collide with
                if move_vec_scalar < 0:
                    continue
                travel_vec = move_vec * move_vec_scalar
                travel_dist_sq = np.dot(travel_vec, travel_vec)
                if axis == 1 and closest_y_hit_dist_sq < travel_dist_sq + 0.0001:
                    closest_y_hit_dist_sq = travel_dist_sq
                # if this movement is further than a collision we already have, skip it.
                if travel_dist_sq > closest_hit_dist_sq:
                    continue
                # # if there's a corner hit, tiebreak by whichever axis velocity is faster
                # if travel_dist_sq == closest_hit_dist_sq and abs(closest_hit_axis_v) > abs(move_vec[axis]):
                #     continue

                new_projected_plane = (add_void_to_vector(player_leading_edge[BOTTOM], travel_vec),
                                       add_void_to_vector(player_leading_edge[TOP], travel_vec))
                if are_blocks_overlapping(new_projected_plane, plane, axis):
                    closest_hit_dist_sq = travel_dist_sq
                    closest_hit_axis_v = move_vec[axis]
                    closest_hit_axis = axis
                    closest_hit_scalar = move_vec_scalar
                    closest_hit_pos = plane_pos
                    closest_hit_block = block_idx
        if closest_hit_axis != -1:
            self.touching_blocks.append(self.buf_wrap.game_blocks[closest_hit_block])
            # move until collision
            self.pos = self.pos + move_vec * closest_hit_scalar
            # lock this position to exactly the collision location to fix for floating pt error
            self.pos[closest_hit_axis] = closest_hit_pos -\
                (self.size[closest_hit_axis] if closest_hit_axis_v > 0 else 0)  # if we're traveling in a + direction,
            #                                                                     set front to plane, not back
            # should we bounce? Only if speed is above threshold and we weren't touching that axis/dir last frame.
            self.touch_directions[closest_hit_axis] = self.velocity[closest_hit_axis]
            if last_touch_directions[closest_hit_axis] * self.velocity[closest_hit_axis] <= 0:
                self.velocity[closest_hit_axis] *= -BOUNCE
            else:
                self.velocity[closest_hit_axis] = 0

            move_vec[closest_hit_axis] = 0
            self.move(move_vec, last_touch_directions, dt, limit - 1)

        else:
            self.pos = self.pos + move_vec

    # find the planes that the player could possibly collide with
    # (find all planes that exist in a bounding box which intersects with the players movement rect)
    def find_planes(self, moving_rect):
        # using in-place traversal method as trace.cl
        # find rectangles inside shape that is player's mvmt block

        x_planes = []  # an x-plane is one which is normal to the x axis
        y_planes = []
        z_planes = []
        index = 0  # start at left 1 in order to skip player rect
        prev_index = -1
        tree_size = self.buf_wrap.hierarchy.shape[0]
        while True:
            if ((prev_index == index * 2 + 2)  # we are coming from right child
                    or index >= tree_size  # we are outside the tree
                    or not self.buf_wrap.hierarchy["filled"][index]  # we are in an empty node
                    # \/ should we continue traversing the tree (only if we overlap or hit a "same" node)
                    or (not self.buf_wrap.hierarchy["same"][index] and
                        not are_blocks_overlapping(moving_rect, (self.buf_wrap.hierarchy["bottom"][index],
                                                                 self.buf_wrap.hierarchy["top"][index])))):
                prev_index = index
                index = (index - 1) >> 1
                if index == -1:
                    break
            if self.buf_wrap.hierarchy["plane1"][index] != -1:
                # pass in the rectangle pointed to by plane1
                block_idx = self.buf_wrap.hierarchy["plane1"][index] // 6
                check_plane(self.buf_wrap.rects[self.buf_wrap.hierarchy["plane1"][index]],
                            moving_rect, block_idx, x_planes, y_planes, z_planes)
            if self.buf_wrap.hierarchy["plane2"][index] != -1:
                block_idx = self.buf_wrap.hierarchy["plane2"][index] // 6
                check_plane(self.buf_wrap.rects[self.buf_wrap.hierarchy["plane2"][index]],
                            moving_rect, block_idx, x_planes, y_planes, z_planes)
            if prev_index < index:  # coming from parent node, go left
                prev_index = index
                index = index * 2 + 1
            elif prev_index == index * 2 + 1:  # coming from left node, then go right
                prev_index = index
                index = index * 2 + 2
        return x_planes, y_planes, z_planes

    def get_center(self):
        return self.pos + self.size / 2
