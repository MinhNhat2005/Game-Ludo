# players/player_factory.py
from .player import Player
from utils.constants import PLAYER_COLORS

def create_human_player(pid):
    color = PLAYER_COLORS[pid]
    return Player(pid, color, is_bot=False)
