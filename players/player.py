# players/player.py
class Player:
    def __init__(self, pid, color, is_bot=False):
        self.id = pid
        self.color = color
        self.is_bot = is_bot
