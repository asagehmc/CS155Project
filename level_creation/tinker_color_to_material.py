

mapping = {
    "e9968c": "RED_LIGHT",
    "fbc59a": "ORANGE_LIGHT",
    "f8e6b7": "YELLOW_LIGHT",
    "c8e4bd": "GREEN_LIGHT",
    "b0e8ef": "CYAN_LIGHT",
    "85cde6": "BLUE_LIGHT",
    "aebeed": "NAVY_LIGHT",
    "d3bfe5": "PURPLE_LIGHT",
    "efb1d4": "PINK_LIGHT",
    "e2c095": "BROWN_LIGHT",
    "fafafa": "GRAY_LIGHT",
    "a7adb1": "ASH_LIGHT",
    "e91d2d": "RED",
    "f5831f": "ORANGE",
    "ffdd1a": "YELLOW",
    "46b749": "GREEN",
    "75cedb": "CYAN",
    "009fd7": "BLUE",
    "3b55a3": "NAVY",
    "7e3f98": "PURPLE",
    "d70b8c": "PINK",
    "a97b50": "BROWN",
    "61676a": "ASH",
    "951a21": "DARK_RED ",
    "e35b22": "DARK_ORANGE",
    "e1ad34": "DARK_YELLOW",
    "126936": "DARK_GREEN",
    "1c505a": "DARK_CYAN",
    "0076a9": "DARK_BLUE",
    "192e62": "DARK_NAVY",
    "492e72": "DARK_PURPLE",
    "901c53": "DARK_PINK",
    "603913": "DARK_BROWN",
    "bfc7cc": "DARK_GRAY",
    "2b2e31": "DARK_ASH",
}


for color, name in mapping.items():
    ambient = ""
    specular = ""
    diffuse = ""
    for i in range(0, 3):
        print
        float_val = int(color[i*2:i*2+2], 16) / 255
        ambient += str(float_val * 0.1) + (", " if i != 2 else "")
        diffuse += str(float_val * 0.6) + (", " if i != 2 else "")
        specular += str(float_val * 0.4) + (", " if i != 2 else "")

    print(f"    mat: {name}")
    print(f"        ambient_color: {ambient}")
    print(f"        diffuse_color: {diffuse}")
    print(f"        specular_color: {specular}")
    print("        specular_power: 40")

