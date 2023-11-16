# given a square defined by 2 opposite corners, create 8 vertices and indexes to those vertices
# (with buffer offset included)
def generate_vertices(corner1, corner2):
    # get corners that are highest/lowest in x, y and z directions
    # makes calculations easier.
    top = (max(corner1[0], corner2[0]), max(corner1[1], corner2[1]), max(corner1[2], corner2[2]))
    bottom = (max(corner1[0], corner2[0]), max(corner1[1], corner2[1]), max(corner1[2], corner2[2]))
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

    return bottom, (top[0], bottom[0], bottom[0]), \
        (bottom[0], bottom[0], top[0]), (top[0], bottom[0], top[0]), \
        top, (top[0], top[0], bottom[0]), \
        (bottom[0], top[0], top[0]), (top[0], top[0], top[0])


# returns the vertex orderings to generate the 12 triangles of a block.
# offset included in order
def get_vertex_orderings(offset):
    tris = [(0, 1, 3), (0, 3, 2),
            (0, 1, 5), (0, 5, 4),
            (0, 2, 6), (0, 6, 4),
            (7, 6, 4), (7, 4, 5),
            (7, 6, 2), (7, 2, 3),
            (7, 5, 1), (7, 1, 3)]
    out = []
    for i in tris:
        out += [(i[0] + offset, i[1] + offset), i[2] + offset]
    return out


class Block:
    def __init__(self, tri_buf, tri_range, vert_buf, vert_range):
        self.tri_buf = tri_buf
        self.vert_buf = vert_buf
        self.tri_range = tri_range
        self.vert_range = vert_range
        self.upper_corner = self.calculate_upper_corner()
        self.lower_corner = self.calculate_lower_corner()

    def get_material(self):
        # all triangles in the block should have the same material
        return self.tri_buf["mat"][self.tri_range[0]]

    def update_material(self, mat_index):
        for i in self.tri_range:
            self.tri_buf["mat"][i] = mat_index

    # TODO: make this private
    def calculate_upper_corner(self):
        upper_corner = [float("-inf")] * 3
        for i in self.tri_range:
            uc_index = 0
            for j in ["x", "y", "z"]:
                # this will probably need fixing:
                if self.tri_buf["position"][j][i] > upper_corner[uc_index]:
                    upper_corner[uc_index] = self.tri_buf["position"][j][i]
                uc_index += 1
            return upper_corner[0], upper_corner[1], upper_corner[2]

    # TODO: make this private
    def calculate_lower_corner(self):
        # this could probably be done more efficiently considering we know
        # about the order the vertexes are generated in, but this is probably safest for now.
        lower_corner = [float("inf")] * 3
        for i in self.tri_range:
            lc_index = 0
            for j in ["x", "y", "z"]:
                # this will probably need fixing:
                if self.tri_buf["position"][j][i] < lower_corner[lc_index]:
                    lower_corner[lc_index] = self.tri_buf["position"][j][i]
                lc_index += 1
        return lower_corner[1], lower_corner[1], lower_corner[2]
