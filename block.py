# given a square defined by 2 opposite corners, create 8 vertices and indexes to those vertices
# (with buffer offset included)
import numpy as np

import util


def generate_rects(corner1, corner2):
    # get corners that are highest/lowest in x, y and z directions
    # makes calculations easier.
    top = (max(corner1[0], corner2[0]), max(corner1[1], corner2[1]), max(corner1[2], corner2[2]))
    bottom = (min(corner1[0], corner2[0]), min(corner1[1], corner2[1]), min(corner1[2], corner2[2]))
    #   x-  y|   z/
    #
    #    btt_____ttt
    #      /    /|
    #  btb/____/ |
    #     |    | | tbt
    #  bbb|____|/tbb
    #
    # bbb, tbb, bbt, tbt: bottom 4 vertices in block
    # btb, ttb, btt, ttt: top 4 vertices in block

    return [
        (bottom, (top[0], bottom[1], top[2]), (0, -1, 0)),  # -y bottom rect
        (bottom, (top[0], top[1], bottom[2]), (0, 0, -1)),  # -z face
        (bottom, (bottom[0], top[1], top[2]), (-1, 0, 0)),  # -x face

        ((bottom[0], top[1], bottom[2]), top, (0, 1, 0)),  # y top rect
        ((bottom[0], bottom[1], top[2]), top, (0, 0, 1)),  # z face
        ((top[0], bottom[1], bottom[2]), top, (1, 0, 0)),  # x face
    ]


class Block:
    def __init__(self, name, buf_wrap, rect_start, bottom_corner, top_corner, material, level=None, flags=None):
        self.level = level
        self.name = name
        self.buf_wrap = buf_wrap
        self.rect_start = rect_start
        self.top_corner = top_corner
        self.bottom_corner = bottom_corner
        self.material = material
        if flags is None:
            flags = []
        self.is_lvl_start = "start" in flags
        self.is_lvl_end = "finish" in flags
        self.is_checkpoint = "checkpoint" in flags

    def __str__(self):
        return f"b[{self.bottom_corner}, {self.top_corner}]"

    def generate_rects(self):
        return generate_rects(self.bottom_corner, self.top_corner)

    def __get_material(self):
        # all triangles in the block should have the same material
        return self.buf_wrap.rects["mat"][self.rect_start]

    def update_material(self, mat_index):
        # iterate through owned triangles, update material index
        for i in range(self.rect_start, self.rect_start + 6):
            self.buf_wrap.rects["mat"][i] = mat_index
        self.material = mat_index

    # using the fact that the order of triangle vertexes comes from this class, so we know the ordering
    def __get_top_corner(self):
        return self.buf_wrap.rects["top"][self.rect_start + 5]

    def __get_bottom_corner(self):
        return self.buf_wrap.rects["bot"][self.rect_start]

    def apply_offset(self, offset):
        # for use in level generation, so we don't need to update buffer yet
        self.top_corner = util.triple_add(offset, self.top_corner)
        self.bottom_corner = util.triple_add(offset, self.bottom_corner)

    def set_buf_corners(self, upper, lower):
        rects = generate_rects(upper, lower)
        for i in range(6):
            self.buf_wrap.rects[i + self.rect_start] = rects[i] + (self.material,)

    def center(self):
        return np.array(
            [(self.top_corner[0] + self.bottom_corner[0]) / 2,
             (self.top_corner[1] + self.bottom_corner[1]) / 2,
             (self.top_corner[2] + self.bottom_corner[2]) / 2]
        )

    def get_rect_index(self, index):
        if index > 5 or index < 0:
            raise Exception("Invalid get_rect index " + str(index))
        return index + self.rect_start

    def get_far_edge(self):
        # return the coordinate of the center x, top y, , top z (for placing the next level)
        return np.array(
            [(self.top_corner[0] + self.bottom_corner[0]) / 2,
             self.top_corner[1],
             self.top_corner[2]]
        )

    def get_near_edge(self):
        # return the coordinate of the center x, top y, , top z (for placing the next level)
        return np.array(
            [(self.top_corner[0] + self.bottom_corner[0]) / 2,
             self.top_corner[1],
             self.bottom_corner[2]]
        )
