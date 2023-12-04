import block
import level_generator
from level_generator import LevelGenerator
from buffer_wrapper import BufferWrap
from camera import Camera
from custom_types import *
from light import Light
from player import Player
from util import string_to_3tuple, begins_with

C_GLIDE = 6
MAT_PATH = "./world_data/materials.txt"
LEVEL_PATH = "./world_data/1/world.txt"


def subtract(v1, v2):
    return np.array([v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2]])


class World:
    world_ambient_color = (1, 1, 1)
    world_background_color = (0, 0, 0)
    world_ambient_intensity = 0
    SHOW_SHADOWS = True
    MAX_VIEW_DISTANCE = 30

    # buffer for world triangles
    rects_data = np.array([], dtype=rect_type)
    # buffer for world materials
    materials_buf = np.array([], dtype=material_type)
    # buffer for world lights
    lights_buf = np.array([], dtype=light_type)
    # buffer to contain 1 element, the world data
    world_data_buf = np.array([], dtype=world_data_type)

    # maps material name to it's index in the buffer
    material_name_index = {}

    # light object dictionary
    game_lights = {}
    game_blocks = {}

    def __init__(self):
        data = []
        self.num_rects = 0

        self.num_materials = 0
        self.num_materials_added = 0

        self.player = None
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
                self.create_mat(data[0], data[1], data[2], data[3], data[4])
                data = []

        # generate world bufs:

        # 1 box for the player and then a set amount per level
        rects_data = np.empty(6 * (1 + 2 ** (level_generator.MAX_TREE_DEPTH_PER_LEVEL + 2)), dtype=rect_type)

        # buffer for the world bounding volume hierarchy (4 branches of max depth)
        hierarchy_data = np.empty((level_generator.MAX_TREE_DEPTH_PER_LEVEL + 2) ** 2, dtype=bounding_node_type)

        self.buf_wrap = BufferWrap(rects_data, hierarchy_data)
        self.create_block("PLAYER_BLOCK", (0, 0, 0), (1, 1, 1), "PLAYER_MAT")

        # functionality is left in here to have 2+ lights, but we'll leave it at 1 for performance
        self.num_lights = 1
        self.lights_buf = np.array([((0, 0, 0), (1, 1, 0), 1)], dtype=light_type)
        self.game_lights[0] = Light(self.lights_buf, 0)

        self.camera_data_buf = np.array([((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))], dtype=camera_data_type)

        self.camera = Camera(self.camera_data_buf)
        if self.player is None:
            raise Exception("No player block was initialized! \n Create a PLAYER_BLOCK block in world.txt")
        # get
        buffer_wrapper = BufferWrap(rects_data, None)
        generator = LevelGenerator(self.material_name_index, buffer_wrapper)

        bounding_hierarchy, rects_data = bvh_generator.generate_bvh_tree(list(self.game_blocks.values()), self.player.block)
        self.buf_wrap.bounding_hierarchy = bounding_hierarchy
        self.buf_wrap.rects_data = rects_data
        self.world_data_buf = np.array([(self.MAX_VIEW_DISTANCE,
                                         self.buf_wrap.bounding_hierarchy.shape[0],
                                         self.num_lights,
                                         self.SHOW_SHADOWS,
                                         self.world_ambient_color,
                                         self.world_background_color,
                                         self.world_ambient_intensity)], dtype=world_data_type)
        self.player.assign_world_bufs(self.buf_wrap)


    def create_mat(self, name, ambient, diffuse, specular, spec_power):
        self.materials_buf[self.num_materials_added] = (ambient, diffuse, specular, spec_power)

        # store the material's index hashed by material name
        # (for retrieval when creating triangle mat indexes later)
        self.material_name_index[name] = self.num_materials_added
        self.num_materials_added += 1


    def update(self, dt):
        self.player.update_position(dt)
        target = self.player.get_center() + [self.player.size[0]/2, 4, -2]
        current = self.camera.get_position()
        shift = subtract(target, current)
        # TODO: move this functionality to camera, make it dt smooth
        self.camera.set_position(current[0] + shift[0] / C_GLIDE,
                                 current[1] + shift[1] / C_GLIDE,
                                 current[2] + shift[2] / C_GLIDE)
        self.camera.set_direction(0, -1, 1)
