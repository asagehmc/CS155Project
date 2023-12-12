import os
import random
import statistics

import util
from block import Block
from buf_wrap import BufferWrap
from level import Level
from util import string_to_3tuple, begins_with, triple_add

import numpy as np

from custom_types import bounding_node_type, rect_type

DIFFICULTY_SCALING = 1
MAX_TREE_DEPTH_PER_LEVEL = 5
CHECK_D = 3


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


def generate_new_level(level_idx, buf_wrap, materials, prev_level):
    subtree_size = 2 ** MAX_TREE_DEPTH_PER_LEVEL
    # make a copy since we don't want to affect these until completion
    bvh_tree_buf_copy = np.copy(buf_wrap.hierarchy)
    rect_buf_copy = np.copy(buf_wrap.rects)
    game_blocks_copy = buf_wrap.game_blocks.copy()

    # erase old game Blocks
    subtree_to_replace = level_idx % 4
    rect_start_index = 6 * (1 + subtree_size * subtree_to_replace)
    # delete the Block objects for the old tree
    if prev_level is not None:
        for i in range(1 + subtree_size * subtree_to_replace, 1 + subtree_size * (subtree_to_replace + 1)):
            if i in game_blocks_copy:
                del game_blocks_copy[i]
    # we cycle through subtrees to overwrite
    base_difficulty = level_idx / DIFFICULTY_SCALING
    # randomize the difficulty of the world a little bit
    difficulty = (2.51 * (random.random() - 0.5)) ** 7 + base_difficulty
    # bound it
    difficulty = max(1, difficulty)
    difficulty = min(5, difficulty)
    dirpath = f"./world_data/{int(difficulty)}/"
    print(dirpath)
    filepath = dirpath + random.choice([f for f in os.listdir(dirpath)])
    lines = []
    num_rects = 0
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            lines.append(line.strip())
            if begins_with(line, "block:"):
                num_rects += 6
    data = [None, None, None, None, None]
    blocks = []
    num_rects_initialized = 0

    for line in lines:
        if begins_with(line, "block:"):
            data[0] = line.split(":")[1].strip()
        if begins_with(line, "flags:"):
            flags = line.split(":")[1].split(",")
            data[1] = [x.strip() for x in flags]
        if begins_with(line, "corner1:"):
            data[2] = string_to_3tuple(line.split(":")[1].strip())
        if begins_with(line, "corner2:"):
            data[3] = string_to_3tuple(line.split(":")[1].strip())
        if begins_with(line, "material:"):
            data[4] = line.split(":")[1].strip()
            mat_index = materials[data[4]]
            bot_corner = get_min(data[2], data[3])
            top_corner = get_max(data[2], data[3])
            blocks.append(
                Block(data[0], buf_wrap, rect_start_index + num_rects_initialized * 6,
                      bot_corner, top_corner, mat_index, level_idx, data[1]))
            data = [None, None, None, None, None]
            num_rects_initialized += 1
    start_block = None
    end_block = None
    for block in blocks:
        if block.is_lvl_start:
            start_block = block
        if block.is_lvl_end:
            end_block = block
    if start_block is None:
        raise Exception(f"Level {dirpath} must have a block with a 'start' flag")
    if end_block is None:
        raise Exception(f"Level {dirpath} must have a block with a 'finish' flag")

    # add in checkpoint blocks here!
    offset = (0, 0, 0)
    if prev_level is not None:
        offset = util.triple_add(prev_level.get_offset_for_next(), (0, 0, 3))
        offset = util.triple_sub(offset, start_block.get_near_edge())
    for block in blocks:
        block.apply_offset(offset)

    # buf_wrap, rect_start, bottom_corner, top_corner, material, flags=None
    checkpoint_block = Block(f"CHECKPOINT{subtree_to_replace}", buf_wrap, rect_start_index + num_rects_initialized * 6,
                             (-1.5, 0, CHECK_D), (1.5, 1, 3 + CHECK_D),
                             materials["CHECKPOINT1"], level_idx, ["checkpoint"])
    num_rects_initialized += 1
    checkpoint_block.apply_offset(end_block.get_far_edge())
    blocks.append(checkpoint_block)

    level = Level(buf_wrap, subtree_to_replace, checkpoint_block, start_block, end_block)

    if (len(blocks) < 2) or len(blocks) > 128:
        raise Exception(f"A level must have between 1 and 127 blocks! (has {len(blocks)})")
    # generate the subtree
    subtree = generate_bvh_tree(blocks)

    # copy subtree data into larger tree
    layer_size = 1
    current_pos_in_layer = 0
    first_idx_in_subtree_layer = 0
    start = subtree_to_replace + 3
    for i in range(subtree.shape[0]):
        if current_pos_in_layer == layer_size:
            layer_size *= 2
            current_pos_in_layer = 0
            first_idx_in_layer = 2 * (2 * i + 1) + 1
            start = first_idx_in_layer + layer_size * subtree_to_replace
            first_idx_in_subtree_layer = i
        new_idx = i - first_idx_in_subtree_layer + start

        bvh_tree_buf_copy[new_idx] = subtree[i]
        current_pos_in_layer += 1
    # copy new rect data into rect buf
    start = 6 + subtree_size * 6 * subtree_to_replace
    for i in range(len(blocks)):
        block_rects = blocks[i].generate_rects()
        game_blocks_copy[1 + i + subtree_size * subtree_to_replace] = blocks[i]
        for j in range(0, 6):
            rect_buf_copy[start + 6 * i + j] = block_rects[j] + (blocks[i].material,)

    # update the parent nodes of the tree
    def recalculate_bounds(idx):
        bvh_tree_buf_copy["top"][idx] = get_max(bvh_tree_buf_copy["top"][2 * idx + 1],
                                                bvh_tree_buf_copy["top"][2 * idx + 2])
        bvh_tree_buf_copy["bottom"][idx] = get_min(bvh_tree_buf_copy["bottom"][2 * idx + 1],
                                                   bvh_tree_buf_copy["bottom"][2 * idx + 2])
    # recalculate the bounds of the node to the left or right of the root
    recalculate_bounds(subtree_to_replace // 2 + 1)
    # recalculate the bounds of the root node
    recalculate_bounds(0)

    return bvh_tree_buf_copy, rect_buf_copy, level, game_blocks_copy


# TODO: we should probably make this not an object, it doesn't really need to be one.
class LevelGenerator:
    def __init__(self, materials):
        self.materials = materials

        # RECTS initialization
        rect_empty = ((0, 0, 0), (0, 0, 0), (0, 0, 0), 0)
        rects = np.array(rect_empty, dtype=rect_type)
        # num rects possible in hierarchy + 1 for the player
        rects = rects.repeat(6 * (1 + 2 ** (MAX_TREE_DEPTH_PER_LEVEL + 2)))

        # HIERARCHY initialization
        # we have 4 loaded levels at a time. Generate the top 3 nodes of the tree and keep them
        empty_unfilled = (False, (0, 0, 0), (0, 0, 0), -1, -1, False)
        hierarchy = np.array(empty_unfilled, dtype=bounding_node_type)
        hierarchy = hierarchy.repeat(2 ** (MAX_TREE_DEPTH_PER_LEVEL + 2))
        hierarchy["filled"][0:3] = True
        self.buf_wrap = BufferWrap(rects, hierarchy, {})

    def initialize_world(self, levels):
        for i in range(4):
            prev_level = levels[i - 1 % 4]
            self.buf_wrap.hierarchy, self.buf_wrap.rects, level, self.buf_wrap.game_blocks = \
                generate_new_level(i, self.buf_wrap, self.materials, prev_level)
            levels[i] = level
        return levels


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
        root.bottom,
        root.top,
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
