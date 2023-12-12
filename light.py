class Light:

    def __init__(self, buffer, light_index):
        self.light_buffer = buffer
        self.light_index = light_index

    def get_position(self):
        return self.light_buffer[self.light_index]["position"]

    def set_position(self, x, y, z):
        self.light_buffer[self.light_index]["position"] = (x, y, z)

    def set_position_tuple(self, tuple):
        self.light_buffer[self.light_index]["position"] = tuple

    def set_intensity(self, intensity):
        self.light_buffer[self.light_index]["intensity"] = intensity

