# ai/hard_bot.py
import random
import logging
from core import rules # Cần import rules để biết các ô an toàn

class HardBot:
    def __init__(self, player_id, game_manager):
        self.player_id = player_id
        self.gm = game_manager

    def _evaluate_move(self, piece, new_path_index):
        """
        Hàm đánh giá (heuristic) - "Bộ não" của bot.
        Chấm điểm cho một nước đi giả lập.
        """
        score = 0
        path_len = len(self.gm.board.get_path_for_player(self.player_id)) # 57
        last_index = path_len - 1 # 56
        
        # 1. Ưu tiên về đích
        if new_path_index == last_index:
            score += 1000 # Điểm tuyệt đối
            
        # 2. Ưu tiên đá quân đối thủ
        destination_cell = self.gm.board.get_path_for_player(self.player_id)[new_path_index]
        if destination_cell not in rules.SAFE_CELLS: # Không đá được ở ô an toàn
            for opponent_pid, opponent_pieces in enumerate(self.gm.players):
                if opponent_pid == self.player_id: continue
                for opp_piece in opponent_pieces:
                    if opp_piece.path_index < 0 or opp_piece.finished: continue
                    opp_cell = self.gm.board.get_path_for_player(opponent_pid)[opp_piece.path_index]
                    if opp_cell == destination_cell:
                        score += 500 # Điểm rất cao cho việc đá quân
                        
        # 3. Ưu tiên đi vào đường về đích (home lane)
        # 51 là index bắt đầu của đường về đích (nếu 51 ô ngoài + 6 ô trong)
        if new_path_index >= 51 and piece.path_index < 51:
            score += 100 
            
        # 4. Ưu tiên ra quân (nếu đang ở chuồng)
        if piece.path_index == -1:
            score += 50
            
        # 5. Ưu tiên tiến lên phía trước
        score += (new_path_index - piece.path_index) * 2
        
        # 6. Ưu tiên đi đến ô an toàn (ô xuất phát)
        if destination_cell in rules.SAFE_CELLS:
            score += 30

        # 7. Tránh đi vào ô có thể bị đá bởi đối thủ (logic phức tạp hơn - có thể thêm sau)
        
        return score

    def choose_move(self):
        """
        Gieo xúc xắc và chọn nước đi có điểm cao nhất.
        """
        dice_value = random.randint(1, 6)
        self.gm.dice_value = dice_value
        logging.info(f"Bot Khó (Người {self.player_id + 1}) gieo được: {dice_value}")

        movable_pieces = self.gm.get_movable_pieces(self.player_id, dice_value)
        
        if not movable_pieces:
            logging.info(f"Bot Khó (Người {self.player_id + 1}) không có nước đi.")
            return None

        # --- Logic chọn lựa ---
        best_move = None
        best_score = -float('inf') # Khởi tạo điểm thấp nhất

        for piece in movable_pieces:
            # Tính toán vị trí đích
            new_path_index = -1
            if piece.path_index == -1 and dice_value == 6:
                new_path_index = 0 # Ra quân
            elif piece.path_index >= 0:
                new_path_index = piece.path_index + dice_value
            
            if new_path_index == -1: continue # Bỏ qua nếu không hợp lệ

            # Chấm điểm cho nước đi này
            move_score = self._evaluate_move(piece, new_path_index)
            
            logging.debug(f"Bot Khó: Quân {piece.id+1} đi tới {new_path_index} được {move_score} điểm.")

            if move_score > best_score:
                best_score = move_score
                best_move = piece
        
        logging.info(f"Bot Khó chọn di chuyển quân: {best_move.id + 1} (Điểm: {best_score})")
        return best_move