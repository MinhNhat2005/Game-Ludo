import pygame
import random
import logging
from core.game_manager import GameManager
from ui.components.board_view import BoardView
from network.client import get_current_game_state
from utils import firebase_manager

class GameUI:
    def __init__(self, screen, num_players, player_types, sound_manager):
        self.screen = screen
        self.sound_manager = sound_manager
        self.is_running = True
        self.next_screen = None
        self.online_state = None  # lưu trạng thái online từ server

        # Khởi tạo game manager
        self.game_manager = GameManager(num_players=num_players, player_types=player_types, is_online=False)
        self.board_view = BoardView(screen, self.game_manager, self.game_manager.players, self.sound_manager)

        self.bot_turn_timer = 0
        self.bot_turn_delay = 1.0  # 1 giây chờ bot đi

        try:
            self.font_small = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 20)
            self.font_medium = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 30)
        except:
            self.font_small = pygame.font.Font(None, 20)
            self.font_medium = pygame.font.Font(None, 30)

    # --- Xử lý sự kiện ---
    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.board_view.back_button_rect.collidepoint(mouse_pos):
                logging.info("Người chơi nhấn nút Quay Lại, lưu game...")

                # Chỉ lưu Offline/Bot
                is_loadable = not self.game_manager.is_online
                firebase_manager.save_game_state(
                    self.game_manager,
                    winner_id=None,
                    is_loadable=is_loadable
                )

                logging.info(f"Game đã lưu. MatchID: {self.game_manager.match_id}")
                self.is_running = False
                self.next_screen = 'mode_select'
                return

        # Sự kiện bình thường cho game
        if not self.game_manager.is_bot_turn():
            self.board_view.handle_events(event)

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

                # Hiệu ứng gieo xúc xắc
                if dice_rolled is not None:
                    for _ in range(5):
                        fake_value = random.randint(1, 6)
                        self.board_view.update_dice_display(self.game_manager.turn, fake_value)
                        pygame.time.delay(50)
                    self.board_view.update_dice_display(self.game_manager.turn, dice_rolled)

                if chosen_piece is not None:
                    kicked_piece, just_finished, winner_id = self.game_manager.move_piece(chosen_piece)

                    if winner_id is not None:
                        # --- Trận đấu kết thúc ---
                        msg = f"P{winner_id + 1} đã THẮNG CUỘC!"
                        if self.sound_manager:
                            self.sound_manager.play_sfx('win')  # Phát âm thanh kết thúc
                        # Lưu ngay kết thúc game
                        firebase_manager.save_game_state(
                            self.game_manager,
                            winner_id=winner_id,
                            is_loadable=False
                        )
                    else:
                        # --- Lượt bình thường ---
                        msg = f"Bot (P{self.game_manager.turn + 1}) gieo được {dice_rolled}."
                        if kicked_piece:
                            msg += f" Đã đá quân P{kicked_piece.player_id + 1}!"
                            if self.sound_manager: self.sound_manager.play_sfx('kick')
                        elif just_finished:
                            msg += " Đã về 1 quân!"
                            if self.sound_manager: self.sound_manager.play_sfx('done')
                        else:
                            piece_id = chosen_piece.id if hasattr(chosen_piece, 'id') else '?'
                            msg += f" Đã di chuyển quân {piece_id + 1}."
                            if self.sound_manager: self.sound_manager.play_sfx('move')
                else:
                    msg = f"Bot (P{self.game_manager.turn + 1}) gieo được {dice_rolled} : không có nước đi." \
                        if dice_rolled else f"Bot (P{self.game_manager.turn + 1}) không có nước đi."
                    self.game_manager.next_turn()
                self.board_view.msg = msg

        # --- NGƯỜI CHƠI: Xử lý tương tự (nếu cần) ---
        # Nếu bạn có luồng người chơi thật, bạn cũng nên xử lý winner_id và sound tương tự
        # Ví dụ khi gọi self.game_manager.move_piece(piece_to_move)
        
        # --- ONLINE: Lấy trạng thái từ server ---
        state = get_current_game_state()
        if state.get('room_id') is not None:
            self.update_game_state(state)


    # --- Vẽ mỗi frame ---
    def draw(self):
        if self.online_state:
            self.board_view.draw_from_state(self.online_state)
        else:
            self.board_view.draw()

    # --- Cập nhật trạng thái game từ server ---
    def update_game_state(self, state):
        self.online_state = state

        current_turn = state.get('current_turn', self.game_manager.turn)
        dice_value = state.get('dice_value', None)
        self.game_manager.turn = current_turn
        self.game_manager.dice_value = dice_value

        server_players = state.get('players', None)
        if server_players:
            for i, player_pieces_state in enumerate(server_players):
                for j, piece_state in enumerate(player_pieces_state):
                    piece = self.game_manager.players[i][j]
                    piece.path_index = piece_state.get('path_index', piece.path_index)
                    piece.finished = piece_state.get('finished', piece.finished)

        if dice_value is not None and hasattr(self.board_view, 'update_dice_display'):
            self.board_view.update_dice_display(current_turn, dice_value)

        server_msg = state.get('last_move_info') or state.get('last_message')
        if server_msg:
            self.board_view.msg = server_msg
        else:
            movable = state.get('movable_pieces', [])
            if movable:
                self.board_view.msg = f"Lượt P{current_turn + 1}, gieo được {dice_value}." if dice_value else f"Lượt P{current_turn + 1} chưa gieo xúc xắc."
            else:
                self.board_view.msg = f"Lượt P{current_turn + 1}, gieo được {dice_value} : không có nước đi." if dice_value else f"Lượt P{current_turn + 1} chưa gieo xúc xắc."
