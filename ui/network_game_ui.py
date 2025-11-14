# ui/network_game_ui.py
import pygame
import sys
import logging 
from network import client 
from ui.components.board_view import BoardView
# Import các hằng số cần thiết
from utils.constants import (
    WIDTH, HEIGHT, CELL, PLAYER_COLORS, BLACK, WHITE, MAX_PLAYERS 
)
# Import tạm thời để khởi tạo BoardView
from core.game_manager import GameManager
from core.board import Board
from core.piece import Piece

class NetworkGameUI:
    def __init__(self, screen, sound_manager): # Thêm sound_manager
        self.screen = screen
        self.sound_manager = sound_manager # Lưu sound_manager
        self.is_running = True
        self.clock = pygame.time.Clock()
        self.next_screen = None # Thêm thuộc tính này
        
        # --- SỬA LỖI Ở ĐÂY ---
        # 1. Sử dụng MAX_PLAYERS đã import
        # 2. Khởi tạo dummy_gm và board_view CHỈ MỘT LẦN
        dummy_gm = GameManager(num_players=MAX_PLAYERS) 
        # 3. Truyền sound_manager vào BoardView
        self.board_view = BoardView(screen, dummy_gm, dummy_gm.players, self.sound_manager)
        # ---------------------
        
        # Font cho thông báo trạng thái
        try:
            self.status_font = pygame.font.Font('assets/fonts/title_font.ttf', 24) 
        except:
            self.status_font = pygame.font.SysFont("Arial", 24)
            
        # Thêm thuộc tính cho nút quay lại (lấy từ board_view)
        self.back_button_rect = self.board_view.back_button_rect
        logging.info("NetworkGameUI initialized.") # Dùng logging

    def handle_events(self, event):
        if not client.is_client_connected():
            if event.type == pygame.MOUSEBUTTONDOWN and self.back_button_rect.collidepoint(event.pos):
                logging.info("NetworkGameUI: Nút Quay Lại (khi mất kết nối) được nhấn!")
                self.is_running = False
                self.next_screen = 'online_lobby'
            return

        game_state = client.get_current_game_state()
        my_player_id = client.get_my_player_id()
        is_my_turn = game_state.get('turn') == my_player_id
        can_roll = game_state.get('dice_value') is None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # --- KIỂM TRA CLICK NÚT QUAY LẠI ---
            if self.back_button_rect.collidepoint(mouse_pos):
                logging.info("NetworkGameUI: Nút Quay Lại được nhấn!")
                client.disconnect_from_server() # Ngắt kết nối
                self.is_running = False
                self.next_screen = 'online_lobby' # Quay về sảnh online
                return # Dừng xử lý
            # ---------------------------------
            
            # Log debug
            logging.debug(f"\n--- Mouse Click ---")
            logging.debug(f"DEBUG: My ID: {my_player_id}, Current Turn: {game_state.get('turn')}, Is My Turn: {is_my_turn}")
            logging.debug(f"DEBUG: Dice Value: {game_state.get('dice_value')}, Can Roll: {can_roll}")

            if is_my_turn:
                # 1. Click vào xúc xắc
                if can_roll:
                    my_dice_view = None
                    if 0 <= my_player_id < len(self.board_view.dices):
                        my_dice_view = self.board_view.dices[my_player_id]
                    
                    if my_dice_view and my_dice_view.clicked(mouse_pos):
                        logging.info("Client: Gửi yêu cầu gieo xúc xắc...")
                        if self.sound_manager: self.sound_manager.play_sfx('dice')
                        client.send_action({"type": client.MSG_TYPE_ROLL_DICE})
                        
                # 2. Click vào ô di chuyển
                elif not can_roll:
                    gx = (mouse_pos[0] - self.board_view.start_x) // CELL
                    gy = (mouse_pos[1] - self.board_view.start_y) // CELL
                    clicked_cell = (gx, gy)
                    piece_id_to_move = None
                    
                    temp_board_logic = Board()
                    my_pieces_data = []
                    players_pieces = game_state.get('players_pieces', [])
                    if my_player_id < len(players_pieces):
                         my_pieces_data = players_pieces[my_player_id]
                    current_dice_value = game_state.get('dice_value')

                    if current_dice_value is not None:
                        for piece_data in my_pieces_data:
                            piece_id = piece_data.get('id')
                            path_idx = piece_data.get('path_index')
                            is_finished = piece_data.get('finished')
                            if is_finished: continue

                            dest = None
                            full_path = temp_board_logic.get_path_for_player(my_player_id)
                            path_len = len(full_path); last_idx = path_len - 1
                            if path_idx == -1 and current_dice_value == 6: dest = temp_board_logic.get_spawn_cell(my_player_id)
                            elif path_idx >= 0:
                                next_index = path_idx + current_dice_value
                                if next_index <= last_idx: dest = full_path[next_index]

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

        # --- PHÁT ÂM THANH TỪ HÀNG ĐỢI ---
        if self.sound_manager:
            sound = client.get_sound_to_play() # Lấy âm thanh từ hàng đợi
            if sound:
                logging.info("NetworkGameUI: Đang phát âm thanh: %s", sound)
                self.sound_manager.play_sfx(sound)
        # -----------------------------------

        game_state = client.get_current_game_state()
        my_player_id = client.get_my_player_id()
        is_my_turn = game_state.get('turn') == my_player_id
        dice_value = game_state.get('dice_value')

        highlight_list = []
        if is_my_turn and dice_value is not None:
             valid_dest_tuples = [tuple(cell) for cell in game_state.get('valid_destinations', [])]
             highlight_list = valid_dest_tuples
        self.board_view.highlight_cells = highlight_list

    def draw(self):
        current_game_state = client.get_current_game_state()
        last_msg = client.get_last_message()
        
        self.board_view.draw_from_state(current_game_state)
        
        status_text = self.status_font.render(last_msg, True, (255, 255, 255))
        text_rect = status_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        self.screen.blit(status_text, text_rect)