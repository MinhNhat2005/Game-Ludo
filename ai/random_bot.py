# ai/bot_logic.py
import random
import logging # Thêm logging

class RandomBot:
    def __init__(self, player_id, game_manager):
        self.player_id = player_id
        self.gm = game_manager # gm là GameManager

    def choose_move(self):
        """
        Chiến lược AI đơn giản: gieo xúc xắc và chọn một nước đi hợp lệ ngẫu nhiên.
        """
        # Gieo xúc xắc
        dice_value = random.randint(1, 6)
        
        # --- DÒNG QUAN TRỌNG BỊ THIẾU ---
        # Gán giá trị xúc xắc cho GameManager để các hàm khác biết
        self.gm.dice_value = dice_value 
        # ------------------------------
        
        logging.info(f"Bot (Người {self.player_id + 1}) gieo được: {dice_value}")

        # Lấy danh sách các quân cờ có thể di chuyển
        movable_pieces = self.gm.get_movable_pieces(self.player_id, dice_value)

        if not movable_pieces:
            logging.info(f"Bot (Người {self.player_id + 1}) không có nước đi nào.")
            return None # Không có nước đi nào hợp lệ
        
        # Chọn một quân cờ ngẫu nhiên từ danh sách có thể đi
        chosen_piece = random.choice(movable_pieces)
        logging.info(f"Bot chọn di chuyển quân cờ số: {chosen_piece.id + 1}")
        return chosen_piece