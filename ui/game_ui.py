import pygame
import random
import logging
from core.game_manager import GameManager
from ui.components.board_view import BoardView
from network.client import get_current_game_state

class GameUI:
    def __init__(self, screen, num_players, player_types, sound_manager):
        self.screen = screen
        self.sound_manager = sound_manager
        self.is_running = True
        self.next_screen = None
        self.online_state = None  # lưu trạng thái online từ server
        self.game_manager = GameManager(num_players=num_players, player_types=player_types, is_online=False)
        self.board_view = BoardView(screen, self.game_manager, self.game_manager.players, self.sound_manager)

        self.bot_turn_timer = 0
        self.bot_turn_delay = 1.0  # 1 giây chờ bot đi

    # --- Xử lý sự kiện ---
    def handle_events(self, event):
        # Xử lý nút Quay Lại
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.board_view.back_button_rect.collidepoint(mouse_pos):
                logging.info("Người chơi nhấn nút Quay Lại, lưu game...")
                from utils import firebase_manager

                # Lưu trạng thái game lên Firebase
                # is_loadable = True chỉ khi chế độ Offline hoặc Bot
                mode = 'Offline' if not self.game_manager.is_online else 'Online'
                firebase_manager.save_game_state(
                    self.game_manager,
                    is_loadable=(mode in ['Offline', 'Bot'])
                )
                logging.info(f"Game đã được lưu. MatchID: {self.game_manager.match_id}, Mode: {mode}")

                # Quay về màn hình trước (ví dụ menu hoặc mode_select)
                self.is_running = False
                self.next_screen = 'mode_select'
                return

        # Xử lý các sự kiện bình thường (offline/online)
        if not self.game_manager.is_bot_turn():
            result = self.board_view.handle_events(event)
            if result == 'back':
                self.is_running = False
                self.next_screen = 'mode_select'


    # --- Cập nhật mỗi frame ---
    def update(self, time_delta):
        # --- OFFLINE: Bot đi tự động ---
        if self.game_manager.is_bot_turn():
            self.bot_turn_timer += time_delta
            if self.bot_turn_timer >= self.bot_turn_delay:
                self.bot_turn_timer = 0
                bot = self.game_manager.get_current_bot()
                chosen_piece = bot.choose_move()
                dice_rolled = self.game_manager.dice_value

                if dice_rolled is not None:
                    for _ in range(5):
                        fake_value = random.randint(1, 6)
                        self.board_view.update_dice_display(self.game_manager.turn, fake_value)
                        pygame.time.delay(50)
                    self.board_view.update_dice_display(self.game_manager.turn, dice_rolled)

                if chosen_piece is not None:
                    kick_msg, just_finished, game_won = self.game_manager.move_piece(chosen_piece)
                    msg = f"Bot (P{self.game_manager.turn + 1}) gieo được {dice_rolled}." if dice_rolled else f"Bot (P{self.game_manager.turn + 1}) chưa gieo."
                    if game_won:
                        msg = f"Bot (P{self.game_manager.turn + 1}) đã THẮNG CUỘC!"
                        if self.sound_manager: self.sound_manager.play_sfx('win')
                    elif kick_msg:
                        msg += f" Đã di chuyển. {kick_msg}"
                        if self.sound_manager: self.sound_manager.play_sfx('kick')
                    elif just_finished:
                        msg += " Đã về 1 quân!"
                        if self.sound_manager: self.sound_manager.play_sfx('done')
                    else:
                        msg += " Đã di chuyển."
                else:
                    msg = f"Bot (P{self.game_manager.turn + 1}) gieo được {dice_rolled} nhưng không có nước đi." if dice_rolled else f"Bot (P{self.game_manager.turn + 1}) không có nước đi."
                    self.game_manager.next_turn()
                self.board_view.msg = msg

        # --- ONLINE: Lấy trạng thái từ server ---
        state = get_current_game_state()
        if state.get('room_id') is not None:
            self.update_game_state(state)  # cập nhật online_state, msg, dice, GameManager

    # --- Vẽ mỗi frame ---
    def draw(self):
        if self.online_state:
            self.board_view.draw_from_state(self.online_state)
        else:
            self.board_view.draw()


    # --- Cập nhật trạng thái game từ server ---
    def update_game_state(self, state):
        """Cập nhật trạng thái game online từ server vào game_manager và board_view."""
        self.online_state = state  # Lưu state ngay

        # --- Cập nhật lượt và giá trị xúc xắc ---
        current_turn = state.get('current_turn', self.gm.turn)
        dice_value = state.get('dice_value', None)
        self.gm.turn = current_turn
        self.gm.dice_value = dice_value

        # --- Cập nhật trạng thái quân cờ từng người ---
        server_players = state.get('players', None)
        if server_players:
            # Giả sử self.gm.players là list[list[Piece]]
            for i, player_pieces_state in enumerate(server_players):
                for j, piece_state in enumerate(player_pieces_state):
                    piece = self.gm.players[i][j]
                    piece.path_index = piece_state.get('path_index', piece.path_index)
                    piece.finished = piece_state.get('finished', piece.finished)

        # --- Cập nhật hiển thị xúc xắc ---
        if dice_value is not None:
            if hasattr(self.board_view, 'update_dice_display'):
                self.board_view.update_dice_display(current_turn, dice_value)

        # --- Cập nhật message hiển thị trên board ---
        server_msg = state.get('last_move_info') or state.get('last_message')
        if server_msg:
            self.board_view.msg = server_msg
        else:
            movable = state.get('movable_pieces', [])
            if movable:
                self.board_view.msg = f"Lượt P{current_turn + 1}, gieo được {dice_value}." if dice_value else f"Lượt P{current_turn + 1} chưa gieo xúc xắc."
            else:
                self.board_view.msg = f"Lượt P{current_turn + 1}, gieo được {dice_value} nhưng không có nước đi." if dice_value else f"Lượt P{current_turn + 1} chưa gieo xúc xắc."
