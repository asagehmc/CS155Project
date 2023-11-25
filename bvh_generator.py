import statistics

# this class takes the array of boxes and converts it into an bounding volume hierarchy
# For simplicity's sake, we create this first as a node-pointer tree
# and then convert into an array backed tree so that it can be passed as a buffer into trace.cl

# simpler tree data here, basically a copy of block.py
import numpy as np

from custom_types import bounding_node_type


class __TreeNode:
    def __init__(self, bottom_top, left=None, right=None, same=False):
        self.bottom = bottom_top[0]
        self.top = bottom_top[1]
        self.left = left
        self.right = right
        self.same = same

    def print_self(self, depth):
        return "    " * depth + "NODE: " + str(self.bottom) + ", " + str(self.top) + ", " + str(self.same) \
                + (("\n" + str(self.left.print_self(depth + 1))) if type(self.left) != int else (" " + str(self.left) + " ")) \
                + (("\n" + str(self.right.print_self(depth + 1))) if type(self.right) != int else (" " + str(self.right) + " "))


# split the list in half along the given plane x, y, or z
def partition(tree_list, axis_index):
    data = [x.center()[axis_index] for x in tree_list]
    median = statistics.median(data)
    low, high = [], []
    for x in tree_list:
        if x.center()[axis_index] > median:
            high.append(x)
        else:
            low.append(x)
    return low, high


def get_min(a, b):
    return min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2])


def get_max(a, b):
    return max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])


# find the minimum bounding box of the boxes included.
def get_min_aabb(boxes):
    minimum = boxes[0].bottom_corner
    maximum = boxes[0].top_corner
    for box in boxes[1:]:
        minimum = get_min(minimum, box.bottom_corner)
        maximum = get_max(maximum, box.top_corner)
    return minimum, maximum


def branch(boxes, axis_index):

    if len(boxes) == 1:
        box = boxes[0]
        # boxes a, b, c, and d are marked "same" since they are all the same size as above
        #       [t]
        #      /   \
        #    [a]    [d]
        #    /\     / \
        #   1 [b]  [c] 6
        #     /\   /\
        #    2  3 4 5
        boxB = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=box.get_rect_index(2), right=box.get_rect_index(3), same=True)
        boxC = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=box.get_rect_index(4), right=box.get_rect_index(5), same=True)
        boxA = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=box.get_rect_index(1), right=boxB, same=True)
        boxD = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=boxC, right=box.get_rect_index(6), same=True)
        return __TreeNode(get_min_aabb(boxes), boxA, boxD), 3
    else:
        low, high = partition(boxes, axis_index)
        left, depth1 = branch(low, (axis_index + 1) % 3)
        right, depth2 = branch(high, (axis_index + 1) % 3)
    return __TreeNode(get_min_aabb(boxes), left, right), max(depth1, depth2) + 1


# root_index: the index to insert the current node into the buffer
# depth: how far down the tree we already are
def fill_tree_buf(root, buf, root_index):
    if type(root) == int:
        return

    new_val = (
        True,  # this node has been initialized
        root.top,
        root.bottom,
        # most non-leaf branches will not have plane indexes
        root.left if type(root.left) == int else -1,
        root.right if type(root.right) == int else -1,
        root.same
    )
    print(buf[root_index])
    print("newval", new_val)
    buf[root_index] = new_val
    fill_tree_buf(root.left, buf, root_index * 2 + 1)
    fill_tree_buf(root.right, buf, root_index * 2 + 2)


def generate_bvh_tree(world_rects):
    root, depth = branch(world_rects, 0)
    # fill with empty values marked as initialized=False

    # bvh_tree_buf = np.empty(pow(2, depth) - 1, dtype=bounding_node_type)
    value_to_fill = (False, (0, 0, 0), (0, 0, 0), -1, -1, False)
    # pow(2, depth) - 1,
    bvh_tree_buf = np.array(value_to_fill, dtype=bounding_node_type)
    bvh_tree_buf = np.repeat(bvh_tree_buf, pow(2, depth) - 1)
    fill_tree_buf(root, bvh_tree_buf, 0)
    return bvh_tree_buf
