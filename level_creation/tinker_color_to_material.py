

mapping = {
    "e9968c": ("RED_LIGHT", False),
    "fbc59a": ("ORANGE_LIGHT", False),
    "f8e6b7": ("YELLOW_LIGHT", False),
    "c8e4bd": ("GREEN_LIGHT", False),
    "b0e8ef": ("CYAN_LIGHT", False),
    "85cde6": ("BLUE_LIGHT", False),
    "aebeed": ("NAVY_LIGHT", False),
    "d3bfe5": ("PURPLE_LIGHT", False),
    "efb1d4": ("PINK_LIGHT", False),
    "e2c095": ("BROWN_LIGHT", False),
    "fafafa": ("GRAY_LIGHT", False),
    "a7adb1": ("ASH_LIGHT", False),
    "e91d2d": ("RED", False),
    "f5831f": ("ORANGE", False),
    "ffdd1a": ("YELLOW", False),
    "46b749": ("GREEN", False),
    "75cedb": ("CYAN", False),
    "009fd7": ("BLUE", False),
    "3b55a3": ("NAVY", False),
    "7e3f98": ("PURPLE", False),
    "d70b8c": ("PINK", False),
    "a97b50": ("BROWN", False),
    "dde2e4": ("GRAY", False),
    "61676a": ("ASH", False),
    "951a21": ("DARK_RED ", False),
    "e35b22": ("DARK_ORANGE", False),
    "e1ad34": ("DARK_YELLOW", False),
    "126936": ("DARK_GREEN", False),
    "1c505a": ("DARK_CYAN", False),
    "0076a9": ("DARK_BLUE", False),
    "192e62": ("DARK_NAVY", False),
    "492e72": ("DARK_PURPLE", False),
    "901c53": ("DARK_PINK", False),
    "603913": ("DARK_BROWN", False),
    "bfc7cc": ("DARK_GRAY", False),
    "2b2e31": ("DARK_ASH", False),

    "e9968d": ("RED_LIGHT", True),
    "fbc59b": ("ORANGE_LIGHT", True),
    "f8e6b8": ("YELLOW_LIGHT", True),
    "c8e4be": ("GREEN_LIGHT", True),
    "b0e8f0": ("CYAN_LIGHT", True),
    "85cde7": ("BLUE_LIGHT", True),
    "aebeee": ("NAVY_LIGHT", True),
    "d3bfe6": ("PURPLE_LIGHT", True),
    "efb1d5": ("PINK_LIGHT", True),
    "e2c096": ("BROWN_LIGHT", True),
    "fafafb": ("GRAY_LIGHT", True),
    "a7adb2": ("ASH_LIGHT", True),
    "e91d2e": ("RED", True),
    "f58320": ("ORANGE", True),
    "ffdd1b": ("YELLOW", True),
    "46b74f": ("GREEN", True),
    "75cedc": ("CYAN", True),
    "009fd8": ("BLUE", True),
    "3b55a4": ("NAVY", True),
    "7e3f99": ("PURPLE", True),
    "d70b8d": ("PINK", True),
    "a97b51": ("BROWN", True),
    "dde2e5": ("GRAY", True),
    "61676b": ("ASH", True),
    "951a22": ("DARK_RED ", True),
    "e35b23": ("DARK_ORANGE", True),
    "e1ad35": ("DARK_YELLOW", True),
    "126937": ("DARK_GREEN", True),
    "1c505b": ("DARK_CYAN", True),
    "0076aa": ("DARK_BLUE", True),
    "192e63": ("DARK_NAVY", True),
    "492e73": ("DARK_PURPLE", True),
    "901c54": ("DARK_PINK", True),
    "603914": ("DARK_BROWN", True),
    "bfc7cd": ("DARK_GRAY", True),
    "2b2e32": ("DARK_ASH", True)
}


if __name__ == '__main__':
    for color, name in mapping.items():
        if not name[1]:
            name = name[0]
            ambient = ""
            specular = ""
            diffuse = ""
            for i in range(0, 3):
                float_val = int(color[i*2:i*2+2], 16) / 255
                ambient += str(float_val * 0.1) + (", " if i != 2 else "")
                diffuse += str(float_val * 0.6) + (", " if i != 2 else "")
                specular += str(float_val * 0.4) + (", " if i != 2 else "")

            print(f"    mat: {name}")
            print(f"        ambient_color: {ambient}")
            print(f"        diffuse_color: {diffuse}")
            print(f"        specular_color: {specular}")
            print("        specular_power: 40")

