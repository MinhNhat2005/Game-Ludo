# ui/game_ui.py
import pygame
import logging
from core.game_manager import GameManager
from ui.components.board_view import BoardView
# Import logging (nếu chưa có)
import logging 

class GameUI:
    # 1. Thêm match_id_to_load=None vào hàm khởi tạo
    def __init__(self, screen, num_players, player_types, sound_manager, match_id_to_load=None):
        self.screen = screen
        self.sound_manager = sound_manager
        self.is_running = True
        self.next_screen = None 
        
        # 2. Truyền match_id_to_load vào GameManager
        # GameManager sẽ tự xử lý việc tải game hoặc tạo game mới
        self.game_manager = GameManager(
            num_players=num_players, 
            player_types=player_types, 
            match_id_to_load=match_id_to_load
        )
        
        self.board_view = BoardView(screen, self.game_manager, self.game_manager.players, self.sound_manager)
        self.bot_turn_timer = 0
        self.bot_turn_delay = 1.0

    def handle_events(self, event):
        result = None # Biến để hứng kết quả từ board_view
        
        # Chỉ cho phép người chơi tương tác (click) nếu không phải lượt bot
        # VÀ game chưa kết thúc
        if (not self.game_manager.is_bot_turn() and 
            self.game_manager.winner is None and 
            self.game_manager.dice_value != -1):
            
            # Bắt lấy kết quả trả về (có thể là 'back' hoặc None)
            result = self.board_view.handle_events(event)

        # --- KIỂM TRA TÍN HIỆU QUAY LẠI (ĐÂY LÀ PHẦN SỬA LỖI) ---
        if result == 'back':
            logging.info("GameUI: Nhận tín hiệu Back, lưu game và quay về...")
            
            # Gọi hàm lưu game (nếu game chưa thắng)
            # GameManager sẽ tự kiểm tra và đóng logger
            self.game_manager.save_game_on_quit()
            
            self.is_running = False # Dừng màn hình này
            self.next_screen = 'mode_select' # Báo cho gui.py chuyển về
        # ----------------------------------------------------

    def update(self, time_delta):
        # --- KIỂM TRA GAME OVER TRƯỚC TIÊN ---
        if self.game_manager.winner is not None or self.game_manager.dice_value == -1:
            if "THẮNG CUỘC" not in self.board_view.msg:
                 winner_id = self.game_manager.winner
                 if winner_id is not None:
                     self.board_view.msg = f"Người {winner_id + 1} đã THẮNG CUỘC! Game kết thúc."
                     # Đảm bảo logger đã được đóng (GameManager sẽ tự gọi khi thắng)
                     # self.game_manager.logger.close() 
            return # Dừng hàm update

        # Tự động chạy lượt của bot (nếu game chưa kết thúc)
        if self.game_manager.is_bot_turn():
            self.bot_turn_timer += time_delta
            if self.bot_turn_timer >= self.bot_turn_delay:
                self.bot_turn_timer = 0
                current_bot_turn = self.game_manager.turn 
                (base_msg, kick_msg, dice_rolled, 
                 just_finished, game_won) = self.game_manager.run_bot_turn()

                if dice_rolled is not None:
                    self.board_view.update_dice_display(current_bot_turn, dice_rolled)
                    full_message = f"Bot (P{current_bot_turn+1}) gieo được {dice_rolled}."

                    if game_won:
                        full_message = f"Bot (P{current_bot_turn+1}) đã THẮNG CUỘC!"
                        if self.sound_manager: self.sound_manager.play_sfx('win')
                    elif kick_msg:
                        full_message += f" {base_msg} {kick_msg}"
                        if self.sound_manager: self.sound_manager.play_sfx('kick')
                    elif just_finished:
                         full_message += f" {base_msg} (Đã về 1 quân!)"
                         if self.sound_manager: self.sound_manager.play_sfx('done')
                    elif base_msg == "đã di chuyển.":
                        full_message += f" {base_msg}"
                        if self.sound_manager: self.sound_manager.play_sfx('move')
                    else:
                        full_message += " Không có nước đi."
                    self.board_view.msg = full_message
                else: 
                     self.board_view.msg = f"Bot (P{current_bot_turn+1}) không có nước đi."

    def draw(self):
        self.board_view.draw()