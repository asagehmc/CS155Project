def begins_with(line, prefix):
    return len(line) > len(prefix) and line[0:len(prefix)] == prefix


def string_to_3tuple(line):
    split = line.split(",")
    return float(split[0].strip()), float(split[1].strip()), float(split[2].strip())