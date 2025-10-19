# ai/bot_logic.py
import random

class BotPlayer:
    def __init__(self, player_id, game_manager):
        self.player_id = player_id
        self.gm = game_manager

    def choose_move(self):
        """
        Chiến lược AI đơn giản: chọn một nước đi hợp lệ một cách ngẫu nhiên.
        """
        # Gieo xúc xắc (giả lập)
        dice_value = random.randint(1, 6)
        print(f"Bot (Người {self.player_id + 1}) gieo được: {dice_value}")
        self.gm.dice_value = dice_value

        # Lấy danh sách các quân cờ có thể di chuyển
        movable_pieces = self.gm.get_movable_pieces(self.player_id, dice_value)

        if not movable_pieces:
            print("Bot không có nước đi nào.")
            return None # Không có nước đi nào hợp lệ
        
        # Chọn một quân cờ ngẫu nhiên từ danh sách có thể đi
        chosen_piece = random.choice(movable_pieces)
        print(f"Bot chọn di chuyển quân cờ số: {chosen_piece.id + 1}")
        return chosen_piece