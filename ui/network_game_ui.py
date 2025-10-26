# ui/network_game_ui.py
import pygame
import sys
import logging
# Import client để gửi hành động và lấy trạng thái
from network import client 
# Import BoardView để vẽ bàn cờ
from ui.components.board_view import BoardView
# Import các hằng số cần thiết
from utils.constants import WIDTH, HEIGHT, CELL, PLAYER_COLORS, BLACK, WHITE
# Import tạm thời để khởi tạo BoardView
from core.game_manager import GameManager
from core.board import Board
from core.piece import Piece
from utils.constants import WIDTH, HEIGHT, CELL, PLAYER_COLORS, BLACK, WHITE, MAX_PLAYERS # Thêm MAX_PLAYERS

class NetworkGameUI:
    def __init__(self, screen):
        self.screen = screen
        self.is_running = True
        self.clock = pygame.time.Clock() # Thêm clock
        self.back_button_rect = self.board_view.back_button_rect
        # Sử dụng MAX_PLAYERS đã import
        dummy_gm = GameManager(num_players=MAX_PLAYERS) 
        self.board_view = BoardView(screen, dummy_gm, dummy_gm.players)
        
        # Font cho thông báo trạng thái
        try:
            self.status_font = pygame.font.Font('assets/fonts/title_font.ttf', 24) 
        except:
            self.status_font = pygame.font.SysFont("Arial", 24)

        print("NetworkGameUI initialized.")

    # Trong file ui/network_game_ui.py

    def handle_events(self, event):
        
        # Chỉ xử lý input nếu client đang kết nối
        if not client.is_client_connected():
            # In ra nếu không kết nối được
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                print("DEBUG: Clicked but not connected.")
                
                if self.back_button_rect.collidepoint(mouse_pos):
                    print("NetworkGameUI: Nút Quay Lại được nhấn!")
                    client.disconnect_from_server() # Ngắt kết nối
                    self.is_running = False
                    self.next_screen = 'online_lobby' # Quay về sảnh online
                    return # Dừng xử lý
            return

        game_state = client.get_current_game_state()
        my_player_id = client.get_my_player_id()
        is_my_turn = game_state.get('turn') == my_player_id
        can_roll = game_state.get('dice_value') is None

        # --- THÊM LOG KIỂM TRA ĐIỀU KIỆN ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            print(f"\n--- Mouse Click ---")
            print(f"DEBUG: My ID: {my_player_id}, Current Turn: {game_state.get('turn')}, Is My Turn: {is_my_turn}")
            print(f"DEBUG: Dice Value: {game_state.get('dice_value')}, Can Roll: {can_roll}")
        # -----------------------------------

        if is_my_turn and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # 1. Click vào xúc xắc (chỉ khi chưa gieo)
            if can_roll:
                 my_dice_view = None
                 if 0 <= my_player_id < len(self.board_view.dices):
                      my_dice_view = self.board_view.dices[my_player_id]

                 # --- THÊM LOG KIỂM TRA CLICK XÚC XẮC ---
                 if my_dice_view:
                     print(f"DEBUG: Checking dice click at {mouse_pos}. Dice rect: {my_dice_view.rect}")
                     dice_was_clicked = my_dice_view.clicked(mouse_pos)
                     print(f"DEBUG: Dice clicked result: {dice_was_clicked}")
                 else:
                     print(f"DEBUG: Cannot find dice view for player {my_player_id}")
                 # ---------------------------------------

                 if my_dice_view and dice_was_clicked: # Sử dụng biến đã kiểm tra
                    print("Client: Gửi yêu cầu gieo xúc xắc...") # Log này bạn đã có
                    client.send_action({"type": client.MSG_TYPE_ROLL_DICE})
                    print("--------------------") # Thêm dòng phân cách
                
            # 2. Click vào ô di chuyển (chỉ khi đã gieo)
            elif not can_roll:
                gx = (mouse_pos[0] - self.board_view.start_x) // CELL
                gy = (mouse_pos[1] - self.board_view.start_y) // CELL
                clicked_cell = (gx, gy)
                print(f"DEBUG: Clicked on grid cell: {clicked_cell}") # Log ô được click
                piece_id_to_move = None
                
                # ... (phần logic tìm piece_id_to_move giữ nguyên) ...
                temp_board_logic = Board()
                my_pieces_data = []
                players_pieces = game_state.get('players_pieces', [])
                if my_player_id < len(players_pieces):
                     my_pieces_data = players_pieces[my_player_id]
                current_dice_value = game_state.get('dice_value')

                if current_dice_value is not None:
                    print(f"DEBUG: Checking possible moves for dice {current_dice_value}...") # Log kiểm tra nước đi
                    for piece_data in my_pieces_data:
                        # ... (logic tính dest giữ nguyên) ...
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

                        print(f"DEBUG:   Piece {piece_id+1} at index {path_idx} can move to {dest}") # Log nước đi khả thi
                        if dest == clicked_cell:
                             piece_id_to_move = piece_id
                             break

                if piece_id_to_move is not None:
                    print(f"Client: Gửi yêu cầu di chuyển quân {piece_id_to_move + 1}...") # Log này bạn đã có
                    client.send_action({"type": client.MSG_TYPE_MOVE_PIECE, "payload": {"piece_id": piece_id_to_move}})
                else:
                     print(f"Client: Click vào ô {clicked_cell} không phải nước đi hợp lệ.") # Log này bạn đã có
                print("--------------------") # Thêm dòng phân cách
        
        # Thêm log nếu không phải lượt hoặc không phải click chuột
        elif event.type == pygame.MOUSEBUTTONDOWN and not is_my_turn:
             print("DEBUG: Clicked, but it's not your turn.")
             print("--------------------")

    # ... (các hàm update, draw giữ nguyên) ...

    def update(self, time_delta):
        if not client.is_client_connected() and self.is_running:
             logging.info("NetworkGameUI: Mất kết nối, quay về sảnh chờ...")
             self.is_running = False
             self.next_screen = 'online_lobby'
             return # Dừng update nếu mất kết nối

        # Lấy trạng thái game mới nhất
        game_state = client.get_current_game_state()
        my_player_id = client.get_my_player_id()
        is_my_turn = game_state.get('turn') == my_player_id
        dice_value = game_state.get('dice_value')

        # --- CẬP NHẬT HIGHLIGHT CHO BOARDVIEW ---
        highlight_list = [] # Mặc định là rỗng
        # Chỉ highlight nếu đến lượt mình VÀ đã gieo xúc xắc
        if is_my_turn and dice_value is not None:
             valid_dest_tuples = [tuple(cell) for cell in game_state.get('valid_destinations', [])] # Chuyển list [x,y] thành tuple (x,y)
             highlight_list = valid_dest_tuples

        # Cập nhật danh sách highlight của BoardView
        self.board_view.highlight_cells = highlight_list
        # ---------------------------------------

    def draw(self):
        current_game_state = client.get_current_game_state()
        last_msg = client.get_last_message()

        # BoardView giờ sẽ tự vẽ highlight dựa trên self.board_view.highlight_cells
        self.board_view.draw_from_state(current_game_state)

        # Vẽ thông báo trạng thái
        status_text = self.status_font.render(last_msg, True, (255, 255, 255))
        text_rect = status_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        self.screen.blit(status_text, text_rect)