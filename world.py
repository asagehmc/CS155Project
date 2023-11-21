import block
from camera import Camera
from custom_types import *
from light import Light


def begins_with(line, prefix):
    return len(line) > len(prefix) and line[0:len(prefix)] == prefix


def string_to_3tuple(line):
    split = line.split(",")
    return float(split[0].strip()), float(split[1].strip()), float(split[2].strip())


class World:
    world_ambient_color = (1, 1, 1)
    world_background_color = (0, 0, 0)
    world_ambient_intensity = 0

    # buffer for world triangles
    triangles_buf = np.array([], dtype=triangle_type)
    # buffer for world materials
    materials_buf = np.array([], dtype=material_type)
    # buffer for world vertexes
    vertices_buf = np.array([], dtype=vector_type)
    # buffer for world lights
    lights_buf = np.array([], dtype=light_type)
    # buffer to contain 1 element, the world data
    world_data_buf = np.array([], dtype=world_data_type)

    # maps material name to it's index in the buffer
    material_name_index = {}

    # light object dictionary
    game_lights = {}
    game_blocks = {}

    def __init__(self, read_path):
        context = "world_settings"
        line_num = 1
        data = []
        self.num_triangles = 0
        self.num_lights = 0
        self.num_materials = 0
        self.num_vertices = 0
        with open(read_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line == "Blocks:":
                    context = "blocks"
                    continue
                if line == "Materials:":
                    context = "materials"
                    continue
                if line == "Lights:":
                    context = "lights"
                    continue
                if context == "world_settings":
                    if begins_with(line, "World Ambient Light"):
                        self.world_ambient_light = string_to_3tuple(line.split(":")[1])
                    if begins_with(line, "World Background Color"):
                        self.world_background_color = string_to_3tuple(line.split(":")[1])
                    if begins_with(line, "World Ambient Intensity"):
                        self.world_ambient_intensity = float(line.split(":")[1])
                if context == "blocks":
                    if begins_with(line, "block:"):
                        data.append(line.split(":")[1].strip())
                    if begins_with(line, "corner1:"):
                        data.append(string_to_3tuple(line.split(":")[1].strip()))
                    if begins_with(line, "corner2:"):
                        data.append(string_to_3tuple(line.split(":")[1].strip()))
                    if begins_with(line, "material:"):
                        data.append(line.split(":")[1].strip())
                        self.create_block(data[0], data[1], data[2], data[3])
                        data = []
                if context == "materials":
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
                        self.num_materials += 1
                        data = []

                if context == "lights":
                    if begins_with(line, "light:"):
                        data.append(line.split(":")[1].strip())
                    if begins_with(line, "position:"):
                        data.append(string_to_3tuple(line.split(":")[1].strip()))
                    if begins_with(line, "color:"):
                        data.append(string_to_3tuple(line.split(":")[1].strip()))
                    if begins_with(line, "intensity:"):
                        data.append(float(line.split(":")[1].strip()))
                        self.create_light(data[0], data[1], data[2], data[3])
                        data = []
                        self.num_lights += 1
                line_num += 1

        self.camera_data_buf = np.array([((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))],
                                        dtype=camera_data_type)
        self.camera = Camera(self.camera_data_buf)

        self.world_data_buf = np.array([(self.num_triangles,
                                         self.num_lights,
                                         self.world_ambient_color,
                                         self.world_background_color,
                                         self.world_ambient_intensity)], dtype=world_data_type)

    def create_block(self, name, corner1, corner2, mat):

        mat_index = self.material_name_index[mat]
        # get the 8 new vertices for the block
        new_vertices = np.array(block.generate_vertices(corner1, corner2), dtype=vector_type)
        self.vertices_buf = np.append(self.vertices_buf, new_vertices)
        # get the vertex indices for each of the 12 triangles for the block
        new_triangles = block.get_vertex_orderings(self.num_vertices)
        # add material data to each triangle indexes to create whole tri structs, append them to triangle buffer
        self.triangles_buf = np.append(self.triangles_buf,
                                       np.array([x + (mat_index,) for x in new_triangles], dtype=triangle_type))

        # if 2 blocks have the same name, just rename until it fits
        if name in self.game_blocks:
            short_name = name
            num = 2
            while name in self.game_blocks:
                name = short_name + str(num)
                num += 1
        if name != "PLAYER_BLOCK":
            # pass in the triangle and vertex buffers, and the start references for their data locations in buffers
            self.game_blocks[name] = block.Block(self.triangles_buf, self.num_triangles,
                                                 self.vertices_buf, self.num_vertices)
        self.num_triangles += 12
        self.num_vertices += 8

    def create_mat(self, name, ambient, diffuse, specular, spec_power):
        new_mat = np.array([(ambient, diffuse, specular, spec_power)], dtype=material_type)
        self.materials_buf = np.append(self.materials_buf, new_mat)
        # store the material's index hashed by material name
        # (for retrieval when creating triangle mat indexes later)
        self.material_name_index[name] = self.num_materials

    def create_light(self, name, position, color, intensity):
        current_len = self.lights_buf.shape[0]
        # add the light data to the light buffer
        new_light = np.array([(position, color, intensity)], dtype=light_type)
        self.lights_buf = np.append(self.lights_buf, new_light)
        # initialize a light object with a pointer to the light buffer where the light data is stored
        self.game_lights[name] = Light(self.lights_buf, current_len)
