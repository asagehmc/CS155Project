# given a square defined by 2 opposite corners, create 8 vertices and indexes to those vertices
# (with buffer offset included)
def generate_vertices(corner1, corner2):
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

    return [bottom, (top[0], bottom[1], bottom[2]),
            (bottom[0], bottom[1], top[2]), (top[0], bottom[1], top[2]),
            (bottom[0], top[1], bottom[2]), (top[0], top[1], bottom[2]),
            (bottom[0], top[1], top[2]), top]


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
        out += [(i[0] + offset, i[1] + offset, i[2] + offset)]
    return out


class Block:
    def __init__(self, tri_buf, tri_start, vert_buf, vert_start):
        self.tri_buf = tri_buf
        self.vert_buf = vert_buf
        self.tri_start = tri_start
        self.vert_start = vert_start
        self.upper_corner = self.get_upper_corner()
        self.lower_corner = self.get_lower_corner()

    def get_material(self):
        # all triangles in the block should have the same material
        return self.tri_buf["mat"][self.tri_start]

    def update_material(self, mat_index):
        # iterate through owned triangles, update material index
        for i in range(self.tri_start, self.tri_start + 12):
            self.tri_buf["mat"][i] = mat_index

    # using the fact that the order of triangle vertexes comes from this class, so we know the ordering
    def get_upper_corner(self):
        return self.vert_buf[self.vert_start]

    def get_lower_corner(self):
        return self.vert_buf[self.vert_start + 7]

