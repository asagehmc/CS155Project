import os
import random
import statistics

import block
from block import Block
import custom_types
from util import string_to_3tuple, begins_with

import numpy as np

from custom_types import bounding_node_type

DIFFICULTY_SCALING = 5
MAX_TREE_DEPTH_PER_LEVEL = 7


class __TreeNode:
    def __init__(self, bottom_top, left=None, right=None, same=False):
        self.bottom = bottom_top[0]
        self.top = bottom_top[1]
        self.left = left
        self.right = right
        self.same = same

    def print_self(self, depth):
        return "    " * depth + "NODE: " + str(self.bottom) + ", " + str(self.top) + ", " + str(self.same) \
               + (("\n" + str(self.left.print_self(depth + 1))) if type(self.left) != int else (
                    " " + str(self.left) + " ")) \
               + (("\n" + str(self.right.print_self(depth + 1))) if type(self.right) != int else (
                    " " + str(self.right) + " "))


def generate_new_level(level_idx, buf_wrap, materials):
    subtree_size = 2 ** MAX_TREE_DEPTH_PER_LEVEL
    # make a copy since we don't want to affect these until completion
    bvh_tree_buf_copy = np.copy(buf_wrap.hierarchy)
    rect_buf_copy = np.copy(buf_wrap.rect_buf)

    # we cycle through subtrees to overwrite
    subtree_to_replace = level_idx % 4
    base_difficulty = level_idx / DIFFICULTY_SCALING
    # randomize the difficulty of the world a little bit
    difficulty = int((2.51 * (random.random() - 0.5)) ** 7) + base_difficulty
    # bound it
    difficulty = max(0, difficulty)
    difficulty = min(5, difficulty)
    dirpath = f"./world_data/{difficulty}"
    filepath = random.choice([f for f in os.listdir(dirpath)])
    lines = []
    num_rects = 0
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            lines.append(line.strip())
            if begins_with(line, "block:"):
                num_rects += 6
    data = []
    blocks = []
    rect_start_index = 6 * (1 + subtree_size * subtree_to_replace)
    num_rects_initialized = 0
    for line in lines:
        if begins_with(line, "block:"):
            data.append(line.split(":")[1].strip())
        if begins_with(line, "corner1:"):
            data.append(string_to_3tuple(line.split(":")[1].strip()))
        if begins_with(line, "corner2:"):
            data.append(string_to_3tuple(line.split(":")[1].strip()))
        if begins_with(line, "material:"):
            data.append(line.split(":")[1].strip())
            mat_index = materials[data[3]]
            blocks.append(
                block.Block(buf_wrap, rect_start_index + num_rects_initialized * 6, data[1], data[2], mat_index))
            data = []
    if (len(blocks) < 2) or len(blocks) > 128:
        raise Exception(f"A level must have between 2 and 28 blocks! (has {len(blocks)})")
    # generate the subtree
    subtree = generate_bvh_tree(blocks)

    # copy subtree data into larger tree
    for i in range(subtree.shape[0]):
        # shift the new set down past the 3 root nodes
        new_pos = 4 * i + 3 + subtree_to_replace
        bvh_tree_buf_copy[new_pos] = subtree[i]
    # copy new rect data into rect buf
    start = 6 + subtree_size * subtree_to_replace
    for i in range(len(blocks)):
        block_rects = blocks[i].generate_rects()
        for j in range(0, 6):
            rect_buf_copy[start + 6 * i + j] = block_rects[i] + (blocks[i].material,)

    # update the parent nodes of the tree
    def recalculate_bounds(idx):
        bvh_tree_buf_copy["top"][idx] = max(bvh_tree_buf_copy["top"][2 * idx + 1],
                                            bvh_tree_buf_copy["top"][2 * idx + 2])
        bvh_tree_buf_copy["bottom"][idx] = max(bvh_tree_buf_copy["bottom"][2 * idx + 1],
                                               bvh_tree_buf_copy["bottom"][2 * idx + 2])

    recalculate_bounds(subtree // 2)
    recalculate_bounds(0)

    return bvh_tree_buf_copy, rect_buf_copy


class LevelGenerator:

    def __init__(self, materials, buf_wrap):
        empty = (True, (0, 0, 0), (0, 0, 0), -1, -1, False)
        self.buf_wrap = buf_wrap
        self.materials = materials
        # we have 4 loaded levels at a time. Generate the top 3 nodes of the tree and keep them
        hierarchy = np.array([empty, empty, empty], dtype=custom_types.bounding_node_type)
        hierarchy.reshape(2 ** (MAX_TREE_DEPTH_PER_LEVEL + 2))
        self.buf_wrap.hierarchy_buf = hierarchy

    def initialize_world(self):
        for i in range(4):
            self.buf_wrap.hierarchy_buf, self.buf_wrap.rect_buf = generate_new_level(i, self.buf_wrap, self.materials)


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
        #   0 [b]  [c] 5
        #     /\   /\
        #    1  2 3 4
        boxB = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=box.get_rect_index(1), right=box.get_rect_index(2), same=True)
        boxC = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=box.get_rect_index(3), right=box.get_rect_index(4), same=True)
        boxA = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=box.get_rect_index(0), right=boxB, same=True)
        boxD = __TreeNode(((0, 0, 0), (0, 0, 0)),
                          left=boxC, right=box.get_rect_index(5), same=True)
        return __TreeNode(get_min_aabb(boxes), boxA, boxD, False), 3
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
    buf[root_index] = new_val
    fill_tree_buf(root.left, buf, root_index * 2 + 1)
    fill_tree_buf(root.right, buf, root_index * 2 + 2)


def generate_bvh_tree(world_rects):
    world_root, depth = branch(world_rects, 0)
    value_to_fill = (False, (0, 0, 0), (0, 0, 0), -1, -1, False)
    bvh_tree_buf = np.array(value_to_fill, dtype=bounding_node_type)
    bvh_tree_buf = np.repeat(bvh_tree_buf, pow(2, depth) - 1)
    fill_tree_buf(world_root, bvh_tree_buf, 0)
    return bvh_tree_buf
