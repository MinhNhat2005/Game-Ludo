# test_firebase.py
import logging
from utils import firebase_manager
from core.game_manager import GameManager

logging.basicConfig(level=logging.DEBUG)

# Khởi tạo Firebase
firebase_manager.initialize_firebase()

# Tạo game giả lập để lưu
gm = GameManager(num_players=2)
gm.turn = 0
gm.dice_value = 6

# Lưu game
match_id = firebase_manager.save_game_state(gm)
logging.info(f"MatchID vừa lưu: {match_id}")

# Load lại game
loaded_state = firebase_manager.load_game_state(match_id)
logging.info(f"State vừa load: {loaded_state}")

# Lấy lịch sử
history = firebase_manager.get_match_history()
logging.info(f"Lịch sử: {history}")
