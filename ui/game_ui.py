# ui/game_ui.py
import pygame
from core.game_manager import GameManager
from ui.components.board_view import BoardView

class GameUI:
    def __init__(self, screen, num_players, player_types, sound_manager):
        self.screen = screen
        self.sound_manager = sound_manager
        self.is_running = True
        self.next_screen = None # Tín hiệu để báo cho gui.py
        self.game_manager = GameManager(num_players=num_players, player_types=player_types)
        self.board_view = BoardView(screen, self.game_manager, self.game_manager.players, self.sound_manager)
        self.bot_turn_timer = 0
        self.bot_turn_delay = 1.0 # 1 giây chờ trước khi bot đi

    def handle_events(self, event):
        result = None # Biến để hứng kết quả từ board_view
        
        # Chỉ cho phép người chơi tương tác nếu đến lượt của họ
        if not self.game_manager.is_bot_turn():
            result = self.board_view.handle_events(event)

        # --- KIỂM TRA TÍN HIỆU QUAY LẠI ---
        if result == 'back':
            print("GameUI: Nhận tín hiệu Back, quay về menu...")
            self.is_running = False # Dừng màn hình này
            self.next_screen = 'mode_select' # Báo cho gui.py chuyển về màn hình chọn chế độ
        # ---------------------------------

    def update(self, time_delta):
        # Tự động chạy lượt của bot
        if self.game_manager.is_bot_turn():
            self.bot_turn_timer += time_delta
            if self.bot_turn_timer >= self.bot_turn_delay:
                self.bot_turn_timer = 0
                
                current_bot_turn = self.game_manager.turn 
                base_msg, kick_msg, dice_value = self.game_manager.run_bot_turn()

                if dice_value is not None:
                    self.board_view.update_dice_display(current_bot_turn, dice_value)
                    
                    full_message = f"Bot gieo được {dice_value}. {base_msg}"
                    if kick_msg:
                        full_message += kick_msg
                        if self.sound_manager: self.sound_manager.play_sfx('kick') # Bot đá quân
                    else:
                         if self.sound_manager: self.sound_manager.play_sfx('move') # Bot di chuyển
                         
                    self.board_view.msg = full_message
                # else: Bot không có nước đi, msg đã được cập nhật bởi run_bot_turn

    def draw(self):
        self.board_view.draw()