# ui/game_ui.py
import pygame
from core.game_manager import GameManager
from ui.components.board_view import BoardView

class GameUI:
    def __init__(self, screen, num_players, player_types):
        self.screen = screen
        self.is_running = True
        self.game_manager = GameManager(num_players=num_players, player_types=player_types)
        self.board_view = BoardView(screen, self.game_manager, self.game_manager.players)
        self.bot_turn_timer = 0
        self.bot_turn_delay = 1.0 # 1 giây chờ trước khi bot đi

    def handle_events(self, event):
        # Chỉ cho phép người chơi tương tác nếu đến lượt của họ
        if not self.game_manager.is_bot_turn():
            self.board_view.handle_events(event)

    def update(self, time_delta):
        # Tự động chạy lượt của bot
        if self.game_manager.is_bot_turn():
            self.bot_turn_timer += time_delta
            if self.bot_turn_timer >= self.bot_turn_delay:
                self.bot_turn_timer = 0
                
                # Lưu lại lượt của bot trước khi có thể bị thay đổi
                current_bot_turn = self.game_manager.turn 
                base_msg, kick_msg, dice_value = self.game_manager.run_bot_turn()

                if dice_value is not None:
                    # --- DÒNG QUAN TRỌNG NHẤT ---
                    # Cập nhật lại giao diện của viên xúc xắc trên màn hình
                    self.board_view.update_dice_display(current_bot_turn, dice_value)
                    
                    # Cập nhật lại chuỗi thông báo
                    full_message = f"Bot gieo được {dice_value}. {base_msg}"
                    if kick_msg:
                        full_message += kick_msg
                    self.board_view.msg = full_message

    def draw(self):
        self.board_view.draw()