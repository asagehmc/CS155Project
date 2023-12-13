import threading

import pygame

import level_generator
import util
from block import Block
from level_generator import LevelGenerator
from camera import Camera
from custom_types import *
from light import Light
from player import Player
from util import string_to_3tuple, begins_with

C_GLIDE = 6
MAT_PATH = "./world_data/materials.txt"
LEVEL_PATH = "world_data/2/world1.txt"
X, Y, Z = 0, 1, 2
DEATH_DIST = 4
CAN_DIE = True
LIGHT_INTENSITY = 10
NUM_LIVES = 5


def subtract(v1, v2):
    return np.array([v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2]])


def threaded_call_level_generate(output, level_idx_to_replace, buf_wrap, materials, prev_level):
    tree_buf, rect_buf, new_level, game_blocks = level_generator.generate_new_level(level_idx_to_replace, buf_wrap,
                                                                                    materials, prev_level)
    output.tree_buf = tree_buf
    output.rect_buf = rect_buf
    output.new_level = new_level
    output.game_blocks = game_blocks


class LevelGenOutput:
    tree_buf = None
    rect_buf = None
    new_level = None
    game_blocks = None


class World:
    world_ambient_color = (1, 1, 1)
    world_background_color = (0, 0, 0)
    world_ambient_intensity = 0
    SHOW_SHADOWS = True
    MAX_VIEW_DISTANCE = 25

    # buffer for world triangles
    rects_data = np.array([], dtype=rect_type)
    # buffer for world materials
    materials_buf = np.array([], dtype=material_type)
    # buffer for world lights
    lights_buf = np.array([], dtype=light_type)
    # buffer to contain 1 element, the world data
    world_data_buf = np.array([], dtype=world_data_type)

    # maps material name to it's index in the buffer
    material_name_lookup = {}

    # light object dictionary
    game_lights = {}
    game_blocks = {}

    def __init__(self):
        data = []
        self.num_rects = 0
        self.checkpoint = (0, 5, 0)
        self.num_materials = 0
        self.num_materials_added = 0
        self.num_player_deaths = 0
        self.level_num = 0
        self.num_levels_to_regenerate = 0
        self.level_regen_thread = None
        self.level_gen_output = None
        self.highest_level = 3
        self.player = None
        self.game_over = False
        mat_lines = []
        world_lines = []
        with open(MAT_PATH, 'r') as file:
            for line in file:
                mat_lines.append(line.strip())

        for line in mat_lines:
            if begins_with(line, "mat:"):
                self.num_materials += 1
        for line in world_lines:
            if begins_with(line, "block:"):
                self.num_rects += 6
        # for the player
        self.num_rects += 6

        self.materials_buf = np.empty(self.num_materials, dtype=material_type)
        for line in mat_lines:

            if begins_with(line, "World Ambient Light"):
                self.world_ambient_light = string_to_3tuple(line.split(":")[1])
            if begins_with(line, "World Background Color"):
                self.world_background_color = string_to_3tuple(line.split(":")[1])
            if begins_with(line, "World Ambient Intensity"):
                self.world_ambient_intensity = float(line.split(":")[1])

            if begins_with(line, "mat:"):
                data.append(line.split(":")[1].strip())
            if begins_with(line, "ambient_color:"):
                data.append(string_to_3tuple(line.split(":")[1].strip()))
            if begins_with(line, "diffuse_color:"):
                data.append(string_to_3tuple(line.split(":")[1].strip()))
            if begins_with(line, "specular_color:"):
                data.append(string_to_3tuple(line.split(":")[1].strip()))
            if begins_with(line, "specular_power:"):
                data.append(int(line.split(":")[1].strip()))
            if begins_with(line, "reflectivity:"):
                data.append(float(line.split(":")[1].strip()))
                self.create_mat(data[0], data[1], data[2], data[3], data[4], data[5])
                data = []

        # functionality is left in here to have 2+ lights, but we'll leave it at 1 for performance
        self.num_lights = 1
        self.lights_buf = np.array([((0, 5, 0), (1, 1, 1), LIGHT_INTENSITY)], dtype=light_type)
        self.game_lights[0] = Light(self.lights_buf, 0)

        self.camera_data_buf = np.array([((0, 4.5, -4.5), (1, 0, 0), (0, 1, 0), (0, 0, 1))], dtype=camera_data_type)

        self.camera = Camera(self.camera_data_buf)
        self.levels = [None, None, None, None]
        # get
        generator = LevelGenerator(self.material_name_lookup)
        # generate player
        self.buf_wrap = generator.buf_wrap
        p_block = Block("PLAYER", self.buf_wrap, 0, (-0.5, 1, -0.5), (0.5, 2, 0.5),
                        self.material_name_lookup["PLAYER_MAT"])
        self.player = Player(p_block, self.buf_wrap)

        self.levels = generator.initialize_world(self.levels)

        self.world_data_buf = np.array([(self.MAX_VIEW_DISTANCE,
                                         self.buf_wrap.hierarchy.shape[0],
                                         self.num_lights,
                                         self.SHOW_SHADOWS,
                                         self.world_ambient_color,
                                         self.world_background_color,
                                         self.world_ambient_intensity)], dtype=world_data_type)

    def create_mat(self, name, ambient, diffuse, specular, spec_power, reflectivity):
        self.materials_buf[self.num_materials_added] = (ambient, diffuse, specular, spec_power, reflectivity)

        # store the material's index hashed by material name
        # (for retrieval when creating triangle mat indexes later)
        self.material_name_lookup[name] = self.num_materials_added
        self.num_materials_added += 1

    def update(self, dt):
        # update world positions
        self.player.update_position(dt)

        # update checkpoints
        for block in self.player.touching_blocks:
            if (block.is_checkpoint
                    and block.level == self.level_num
                    and block.center()[Z] > self.checkpoint[Z]):
                self.update_checkpoint(block)
            elif block.level == self.level_num + 1:
                checkpoint_block = self.levels[self.level_num % 4].checkpoint_block
                self.update_checkpoint(checkpoint_block)
        # do we need to regenerate levels, and we haven't started yet?
        if self.num_levels_to_regenerate > 0 and self.level_regen_thread is None:
            if self.level_num > 1:
                self.level_gen_output = LevelGenOutput()

                self.level_regen_thread = threading.Thread(target=threaded_call_level_generate,
                                                           args=(self.level_gen_output,
                                                                 self.level_num - 2,  # level to replace
                                                                 self.buf_wrap,
                                                                 self.material_name_lookup,
                                                                 self.levels[(self.level_num + 1) % 4]))  # prev level
                self.level_regen_thread.start()

        # Has the thread completed? if so, update the world!
        if self.level_regen_thread is not None and not self.level_regen_thread.is_alive():
            self.buf_wrap.hierarchy = self.level_gen_output.tree_buf
            self.buf_wrap.rects = self.level_gen_output.rect_buf
            self.buf_wrap.game_blocks = self.level_gen_output.game_blocks
            self.highest_level += 1
            self.levels[self.highest_level % 4] = self.level_gen_output.new_level
            self.level_regen_thread = None
            self.num_levels_to_regenerate -= 1

        # let player die
        if self.player.get_center()[Y] < self.buf_wrap.hierarchy["bottom"][0][Y] - DEATH_DIST:
            self.player.set_position(self.checkpoint)
            self.num_player_deaths += 1

        # move camera
        target = self.player.get_center() + [0, 4, -2]
        current = self.camera.get_position()
        shift = subtract(target, current)
        # TODO: move this functionality to camera, make it dt smooth
        self.camera.set_position(current[0] + shift[0] / C_GLIDE,
                                 current[1] + shift[1] / C_GLIDE,
                                 current[2] + shift[2] / C_GLIDE)
        self.camera.set_direction(0, -1, 1)
            
        # set light intensity to decrease with player deaths
        if CAN_DIE and not self.player.cheat_death:
            self.game_lights[0].set_intensity(max(LIGHT_INTENSITY - self.num_player_deaths * (LIGHT_INTENSITY/NUM_LIVES), 0))

        # kill if deaths exceeds lives
        if self.num_player_deaths >= NUM_LIVES and CAN_DIE and not self.player.cheat_death:
            self.game_over = True

    def update_checkpoint(self, block):
        # handle checkpoint stuff
        block.update_material(self.material_name_lookup["CHECKPOINT2"])
        self.checkpoint = util.triple_add((0, 5, 0), block.center())
        # start loading next level
        self.level_num += 1
        if self.level_num > 1:
            self.num_levels_to_regenerate += 1

