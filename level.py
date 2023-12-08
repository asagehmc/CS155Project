

class Level:
    def __init__(self, buf_wrap, subtree_idx, checkpoint_block, start_block, end_block):
        self.buf_wrap = buf_wrap
        self.subtree_idx = subtree_idx
        self.checkpoint_block = checkpoint_block
        self.start_block = start_block
        self.end_block = end_block

    def get_offset_for_next(self):
        return self.checkpoint_block.get_far_edge()
