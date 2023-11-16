

class Block:
    def __init__(self, name, corner1, corner2, mat_name):
        self.name = name
        self.low_corner = (min(corner1[0], corner2[0]), min(corner1[1], corner2[1]), min(corner1[2], corner2[2]))
        self.high_corner = (max(corner1[0], corner2[0]), max(corner1[1], corner2[1]), max(corner1[2], corner2[2]))
        self.mat_name = mat_name

# to delete an element, use np.delete(a, index)
