
class Player:

    def __init__(self, player_block, game_blocks):
        self.player_block = player_block
        self.game_blocks = game_blocks
        bot = player_block.get_lower_corner()
        top = player_block.get_upper_corner()
        self.x_width = top[0] - bot[0]
        self.height = top[1] - bot[1]
        self.z_width = top[2] - bot[2]
        self.x = bot[0]
        self.y = bot[1]
        self.z = bot[2]

    def update_position(self):
        pass
