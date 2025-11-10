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
        if self.game_manager.winner is not None or self.game_manager.dice_value == -1:
            if "THẮNG CUỘC" not in self.board_view.msg:
                 winner_id = self.game_manager.winner
                 if winner_id is not None:
                     self.board_view.msg = f"Người {winner_id + 1} đã THẮNG CUỘC! Game kết thúc."
            return

        if self.game_manager.is_bot_turn():
            self.bot_turn_timer += time_delta
            if self.bot_turn_timer >= self.bot_turn_delay:
                self.bot_turn_timer = 0
                
                current_bot_turn = self.game_manager.turn 
                
                # --- NHẬN KẾT QUẢ MỚI (5 GIÁ TRỊ) ---
                (base_msg, kick_msg, dice_rolled, 
                 just_finished, game_won) = self.game_manager.run_bot_turn()

                if dice_rolled is not None:
                    self.board_view.update_dice_display(current_bot_turn, dice_rolled)
                    full_message = f"Bot (P{current_bot_turn+1}) gieo được {dice_rolled}."

                    # --- LOGIC ÂM THANH ĐÚNG (KHÔNG CẦN SUY LUẬN) ---
                    if game_won:
                        full_message = f"Bot (P{current_bot_turn+1}) đã THẮNG CUỘC!"
                        if self.sound_manager: self.sound_manager.play_sfx('win')
                    
                    elif kick_msg:
                        full_message += f" {base_msg} {kick_msg}"
                        if self.sound_manager: self.sound_manager.play_sfx('kick')
                    
                    elif just_finished: # Sử dụng giá trị boolean trả về
                         full_message += f" {base_msg} (Đã về 1 quân!)"
                         if self.sound_manager: self.sound_manager.play_sfx('done')
                    
                    elif base_msg == "đã di chuyển.": # Chỉ phát 'move' nếu có di chuyển
                        full_message += f" {base_msg}"
                        if self.sound_manager: self.sound_manager.play_sfx('move')
                    
                    else: # Không di chuyển được
                        full_message += " Không có nước đi."
                    # -----------------------------------------------

                    self.board_view.msg = full_message
                
                else: 
                     self.board_view.msg = f"Bot (P{current_bot_turn+1}) không có nước đi."
    def draw(self):
        self.board_view.draw()