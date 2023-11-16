from custom_types import *


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
    vertexes_buf = np.array([], dtype=vector_type)
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
        with open(read_path, 'r') as file:
            try:
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
                            self.num_triangles += 12
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
                            data = []
                            # store the material's index hashed by material name
                            # (for retrieval when creating triangle mat indexes later)
                            self.material_name_index[data[0]] = self.num_materials
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

            except Exception:
                raise Exception("Error parsing line " + str(line_num) + " of world file")
            line_num += 1
        self.world_data_buf = np.append(self.world_data_buf, (self.num_triangles,
                                                              self.num_lights,
                                                              self.world_background_color,
                                                              self.world_ambient_color,
                                                              self.world_ambient_intensity))

    def create_block(self, name, corner1, corner2, mat):
        print("CREATING NEW BLOCK")
        print(name)
        print(corner1)
        print(corner2)
        print(mat)

    def create_mat(self, name, ambient, diffuse, specular, spec_power):
        self.materials_buf = np.append(self.materials_buf, (name, ambient, diffuse, specular, spec_power))
        print("CREATED NEW MATERIAL!")
        print(name)
        print(ambient)
        print(diffuse)
        print(specular)
        print(spec_power)

    def create_light(self, name, position, color, intensity):
        current_len = self.lights_buf.shape[0]
        self.lights_buf = np.append(self.lights_buf, (name, position, color, intensity))

        print("CREATING NEW LIGHT!")
        print(name)
        print(position)
        print(color)
        print(intensity)
