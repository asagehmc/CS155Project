import os

from level_creation.tinker_color_to_material import mapping
import numpy as np

path = './materials_and_objects'

for folder in os.listdir(path):
    mat_path = "./materials_and_objects/" + folder + "/obj.mtl"
    blocks_path = "./materials_and_objects/" + folder + "/tinker.obj"
    index = ""
    color_index_to_hex = {}
    color_index_start_finish = {}
    out_str = ""

    with open(mat_path, 'r') as file:
        startFinish = False
        for line in file:
            line = line.strip()
            if len(line) > 5 and line[0:6] == "newmtl":
                index = line.split(" ")[1]

            if len(line) > 2 and line[0:2] == "Kd":
                out = ""
                line = line.split(" ")[1:4]
                for string in line:
                    num = int(float(string) * 255)
                    hex_str = hex(num)[2:]
                    out += "0" * (2 - len(hex_str)) + hex_str
                    color_index_to_hex[index] = out
                startFinish = False

    with open(blocks_path, 'r') as file:
        material = None
        num_blocks = 0
        vertexes = []
        min_corner = np.array([float("inf"), float("inf"), float("inf")])
        max_corner = np.array([float("-inf"), float("-inf"), float("-inf")])
        blocks = []
        start_end_1 = -1
        start_end_2 = -1
        start_or_end_block = False
        for line in file:
            line = line.strip()
            if len(line) > 0 and line[0:1] == "v":
                vertex_coords = [float(x.strip()) for x in line.split(" ")[1:4]]
                temp = vertex_coords[2]
                vertex_coords[2] = vertex_coords[1]
                vertex_coords[1] = temp
                vertexes.append(np.array(vertex_coords))
            if len(line) > 5 and line[0:6] == "usemtl":
                mat_code = line.split(" ")[1]
                material_hex = color_index_to_hex[mat_code]
                if material_hex in mapping:
                    material = mapping[material_hex][0]
                    start_or_end_block = mapping[material_hex][1]
                else:
                    raise Exception("COLOR IS MISSING!!  " + material_hex)
            elif len(line) > 0 and line[0:1] == "f" and material is not None:
                vertex_indexes = [int(x.strip()) for x in line.split(" ")[1:4]]
                for vertex_idx in vertex_indexes:
                    box_corner = vertexes[vertex_idx - 1]
                    min_corner = np.minimum(box_corner, min_corner)
                    max_corner = np.maximum(box_corner, max_corner)
            elif len(line) > 0 and line[0:1] == "#" and material is not None:
                blocks.append([f"block: block{num_blocks}", [], min_corner.copy(), max_corner.copy(), material])
                if start_or_end_block:
                    if start_end_1 == -1:
                        start_end_1 = num_blocks
                    elif start_end_2 == -1:
                        start_end_2 = num_blocks
                    else:
                        raise Exception("Can't have more than 2 start/end blocks in a level!")
                num_blocks += 1
                min_corner = np.array([float("inf"), float("inf"), float("inf")])
                max_corner = np.array([float("-inf"), float("-inf"), float("-inf")])
                material = None

        if start_end_2 == -1:
            start_end_2 = start_end_1
        start = 0
        # if start_end_1 is lower z, let it have the start flag
        if blocks[start_end_1][2][2] < blocks[start_end_2][2][2]:
            blocks[start_end_1][1].append("start")
            blocks[start_end_2][1].append("finish")
            start = start_end_1
        else:
            blocks[start_end_2][1].append("start")
            blocks[start_end_1][1].append("finish")
            start = start_end_2
        # shift world so that start center

        shift = blocks[start][3] - blocks[start][2]
        shift = shift / 2
        shift = shift + blocks[start][2]
        shift[1] = shift[1] + 3
        for block in blocks:
            block[2] = block[2] - shift
            block[3] = block[3] - shift


        def join_with_commas(str_list):
            output = ""
            for i in range(len(str_list)):
                output += str(str_list[i]) + (", " if i != len(str_list) - 1 else "")
            return output


        for block in blocks:
            out_str += block[0] + "\n"
            if len(block[1]) > 0:
                out_str += f"        flags: {join_with_commas(block[1])}\n"
            out_str += f"        corner1: {join_with_commas(block[2])}\n"
            out_str += f"        corner2: {join_with_commas(block[3])}\n"
            out_str += f"        material: {block[4]}\n"
            out_str += f"        reflectivity: 0\n"
        print(out_str)
        with open(f"./materials_and_objects/{folder}/{folder}.txt", 'w') as file:
            file.write(out_str)
