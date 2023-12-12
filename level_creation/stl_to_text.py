
import os
import stl
from stl import mesh

from level_creation.tinker_color_to_material import mapping

file_path = './materials_and_objects/obj.mtl'


# with open(file_path, 'r') as file:
#     for line in file:
#         if len(line) > 2 and line[0:2] == "Kd":
#             line = "Kd 0 0.6235294117647059 0.8431372549019608".split(" ")[1:4]
#             out = ""
#             for string in line:
#                 num = int(float(string) * 255)
#                 hex_str = hex(num)[2:]
#                 out += "0" * (2 - len(hex_str)) + hex_str
#









