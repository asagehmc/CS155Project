

def begins_with(line, prefix):
    return len(line) > len(prefix) and line[0:len(prefix)] == prefix


def string_to_3tuple(line):
    split = line.split(",")
    return float(split[0].strip()), float(split[1].strip()), float(split[2].strip())


class World:
    world_ambient_color = (1, 1, 1)
    world_background_color = (0, 0, 0)
    world_ambient_intensity = 0

    def __init__(self, read_path):
        context = "world_settings"
        line_num = 1
        data = []
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


            except Exception:
                raise Exception("Error parsing line " + str(line_num) + " of world file")
                line_num += 1

    def create_block(self, name, corner1, corner2, mat):
        print("CREATING NEW BLOCK")
        print(name)
        print(corner1)
        print(corner2)
        print(mat)

    def create_mat(self, name, ambient, diffuse, specular, spec_power):
        print("CREATING NEW MATERIAL!")
        print(name)
        print(ambient)
        print(diffuse)
        print(specular)
        print(spec_power)

    def create_light(self, name, position, color, intensity):
        print("CREATING NEW LIGHT!")
        print(name)
        print(position)
        print(color)
        print(intensity)
