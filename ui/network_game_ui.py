# ui/network_game_ui.py
import pygame
import logging
from network import client
from ui.components.board_view import BoardView
from utils.constants import WIDTH, HEIGHT, CELL, MAX_PLAYERS
from core.game_manager import GameManager

class NetworkGameUI:
    def __init__(self, screen, sound_manager):
        self.screen = screen
        self.sound_manager = sound_manager
        self.is_running = True
        self.clock = pygame.time.Clock()
        self.next_screen = None

        # Khởi tạo BoardView với GameManager dummy
        dummy_gm = GameManager(num_players=MAX_PLAYERS)
        self.board_view = BoardView(screen, dummy_gm, dummy_gm.players, self.sound_manager)

        # Font hiển thị thông báo
        try:
            self.status_font = pygame.font.Font('assets/fonts/title_font.ttf', 24)
        except:
            self.status_font = pygame.font.SysFont("Arial", 24)

        # Lưu nút quay lại
        self.back_button_rect = self.board_view.back_button_rect

        # Lưu trạng thái online để draw
        self.online_state = None

        logging.info("NetworkGameUI initialized.")

    def handle_events(self, event):
        if not client.is_client_connected():
            if event.type == pygame.MOUSEBUTTONDOWN and self.back_button_rect.collidepoint(event.pos):
                logging.info("NetworkGameUI: Nút Quay Lại (khi mất kết nối) được nhấn!")
                self.is_running = False
                self.next_screen = 'online_lobby'
            return

        game_state = client.get_current_game_state()
        self.online_state = game_state   # <-- Lưu trạng thái mới
        my_player_id = client.get_my_player_id()
        is_my_turn = game_state.get('turn') == my_player_id
        can_roll = game_state.get('dice_value') is None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Kiểm tra nút quay lại
            if self.back_button_rect.collidepoint(mouse_pos):
                logging.info("NetworkGameUI: Nút Quay Lại được nhấn!")
                client.disconnect_from_server()
                self.is_running = False
                self.next_screen = 'online_lobby'
                return

            logging.debug(f"\n--- Mouse Click ---")
            logging.debug(f"DEBUG: My ID: {my_player_id}, Current Turn: {game_state.get('turn')}, Is My Turn: {is_my_turn}")
            logging.debug(f"DEBUG: Dice Value: {game_state.get('dice_value')}, Can Roll: {can_roll}")

            if is_my_turn:
                # Click vào xúc xắc
                if can_roll:
                    my_dice_view = None
                    if 0 <= my_player_id < len(self.board_view.dices):
                        my_dice_view = self.board_view.dices[my_player_id]

                    if my_dice_view and my_dice_view.clicked(mouse_pos):
                        logging.info("Client: Gửi yêu cầu gieo xúc xắc...")
                        if self.sound_manager:
                            self.sound_manager.play_sfx('dice')
                        client.send_action({"type": client.MSG_TYPE_ROLL_DICE})

                # Click vào ô di chuyển
                elif not can_roll:
                    gx = (mouse_pos[0] - self.board_view.start_x) // CELL
                    gy = (mouse_pos[1] - self.board_view.start_y) // CELL
                    clicked_cell = (gx, gy)
                    piece_id_to_move = None

                    temp_board_logic = self.board_view.board  # Sử dụng board có sẵn
                    my_pieces_data = game_state.get('players_pieces', [])[my_player_id] if my_player_id < len(game_state.get('players_pieces', [])) else []
                    current_dice_value = game_state.get('dice_value')

                    if current_dice_value is not None:
                        for piece_data in my_pieces_data:
                            piece_id = piece_data.get('id')
                            path_idx = piece_data.get('path_index')
                            is_finished = piece_data.get('finished')
                            if is_finished:
                                continue

                            dest = None
                            full_path = temp_board_logic.get_path_for_player(my_player_id)
                            last_idx = len(full_path) - 1

                            if path_idx == -1 and current_dice_value == 6:
                                dest = temp_board_logic.get_spawn_cell(my_player_id)
                            elif path_idx >= 0:
                                next_index = path_idx + current_dice_value
                                if next_index <= last_idx:
                                    dest = full_path[next_index]

                            if dest == clicked_cell:
                                piece_id_to_move = piece_id
                                break

                    if piece_id_to_move is not None:
                        logging.info(f"Client: Gửi yêu cầu di chuyển quân {piece_id_to_move + 1}...")
                        client.send_action({"type": client.MSG_TYPE_MOVE_PIECE, "payload": {"piece_id": piece_id_to_move}})
                    else:
                        logging.warning(f"Client: Click vào ô {clicked_cell} không phải nước đi hợp lệ.")

            elif not is_my_turn:
                logging.debug("DEBUG: Clicked, but it's not your turn.")

    def update(self, time_delta):
        if not client.is_client_connected() and self.is_running:
            logging.info("NetworkGameUI: Mất kết nối, quay về sảnh chờ...")
            self.is_running = False
            self.next_screen = 'online_lobby'
            return

        game_state = client.get_current_game_state()
        self.online_state = game_state   # <-- Cập nhật trạng thái mới

        my_player_id = client.get_my_player_id()
        is_my_turn = game_state.get('turn') == my_player_id
        dice_value = game_state.get('dice_value')

        # Highlight các ô hợp lệ
        highlight_list = []
        if is_my_turn and dice_value is not None:
            valid_dest_tuples = [tuple(cell) for cell in game_state.get('valid_destinations', [])]
            highlight_list = valid_dest_tuples
        self.board_view.highlight_cells = highlight_list

    def draw(self):
        # Vẽ board
        if hasattr(self, 'online_state') and self.online_state:
            self.board_view.draw_from_state(self.online_state)
            status_msg = self.online_state.get('last_message', "Click xúc xắc để bắt đầu")
        else:
            self.board_view.draw()
            status_msg = "Click xúc xắc để bắt đầu"

        # Vẽ thông báo trạng thái
        status_text = self.status_font.render(status_msg, True, (255, 255, 255))
        text_rect = status_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        self.screen.blit(status_text, text_rect)
