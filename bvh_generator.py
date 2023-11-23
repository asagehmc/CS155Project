import statistics

# this class takes the array of boxes and converts it into an bounding volume hierarchy
# this starts out as node-pointer tree and is later converted into a buffer to be passed into trace.cl

# simpler tree data here, basically a copy of block.py
import numpy as np


class __TreeNode:
    def __init__(self, bottom_top, left=None, right=None, same=False):
        self.bottom = bottom_top[0]
        self.top = bottom_top[1]
        self.left = left
        self.right = right
        self.same = same


# split the list in half along the given plane x, y, or z
def partition(tree_list, axis_index):
    data = [x.center[axis_index] for x in tree_list]
    median = statistics.median(data)
    low, high = [], []
    for x in tree_list:
        if x.center > median:
            high.append(x)
        else:
            low.append(x)
    return low, high

# find the minimum bounding box of the boxes included.
def get_min_aabb(boxes):
    minimum = boxes[0].bot
    maximum = boxes[0].top
    for box in boxes[1:]:
        minimum = np.minimum(minimum, box.bottom_corner)
        maximum = np.maximum(maximum, box.top_corner)
    return minimum, maximum


def branch(boxes, axis_index):
    left = None
    right = None
    if len(boxes) == 1:
        box = boxes[1]
        # boxes a, b, c, and d are marked "same" since they are all the same size as above
        #       [t]
        #      /   \
        #    [a]    [d]
        #    /\     / \
        #   1 [b]  [c] 6
        #     /\   /\
        #    2  3 4 5
        boxB = __TreeNode(np.array([(0, 0, 0), (0, 0, 0)]),
                          left=box.get_rect_index(2), right=box.get_rect_index(3), same=True)
        boxC = __TreeNode(np.array([(0, 0, 0), (0, 0, 0)]),
                          left=box.get_rect_index(4), right=box.get_rect_index(5), same=True)
        boxA = __TreeNode(np.array([(0, 0, 0), (0, 0, 0)]),
                          left=box.get_rect_index(1), right=boxB, same=True)
        boxD = __TreeNode(np.array([(0, 0, 0), (0, 0, 0)]),
                          left=boxC, right=box.get_rect_index(6), same=True)

        return __TreeNode(get_min_aabb(boxes), boxA, boxD), 3
    else:
        low, high = partition(boxes, axis_index)
        left, depth1 = branch(low, (axis_index + 1) % 3)
        right, depth2 = branch(high, (axis_index + 1) % 3)

    return __TreeNode(get_min_aabb(boxes), left, right), max(depth1, depth2)


def generate_bvh_tree(world_rects):
    root, depth = branch(world_rects, 0)









