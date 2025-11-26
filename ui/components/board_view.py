import pygame
from core import rules
from utils.constants import (
    WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, WHITE, BLACK,
    PLAYER_COLORS, DICE_POSITIONS, FONT, CELL
)
from ui.components.dice_view import DiceView

# CELL và BOARD_SIZE
CELL = 50
BOARD_SIZE = 15

class BoardView:
    def __init__(self, screen, game_manager, players, sound_manager):
        self.screen = screen
        self.gm = game_manager
        self.players = players
        self.sound_manager = sound_manager
        self.clock = pygame.time.Clock()
        self.msg = "Click xúc xắc để bắt đầu!"
        self.last_roll = None
        self.highlight_cells = []

        self.dices = []

        # --- KHỞI TẠO FONT ---
        try:
            self.msg_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 18)
        except FileNotFoundError:
            self.msg_font = pygame.font.Font(None, 18)
            
        self.back_font = pygame.font.Font(None, 16) # Font nhỏ hơn cho nút Quay Lại

        # --- DỮ LIỆU ÁNH XẠ VỊ TRÍ ĐƯỢC LẤY TỪ GM (ĐÃ SỬA CHỮA) ---
        # Lấy trực tiếp từ GameManager để đồng bộ
        self.player_map = self.gm.player_map
        self.active_pids = self.gm.active_pids
            
        # --- KHỞI TẠO XÚC XẮC ---
        for i, board_pid in enumerate(self.active_pids):
            if board_pid < len(PLAYER_COLORS) and board_pid in DICE_POSITIONS:
                color = PLAYER_COLORS[board_pid]
                x, y = DICE_POSITIONS[board_pid]
                self.dices.append(DiceView(x, y, color, i)) 
            elif board_pid not in DICE_POSITIONS:
                print(f"Cảnh báo: Không tìm thấy vị trí xúc xắc cho Board ID {board_pid}")
        
        # --- DỊCH CHUYỂN VỊ TRÍ XÚC XẮC (20PX LÊN TRÊN & 15PX VÀO TRONG) ---
        for dice in self.dices:
            self._apply_dice_position_offset(dice)


        self.start_x = (WIDTH - CELL * BOARD_SIZE) // 2
        self.start_y = (HEIGHT - CELL * BOARD_SIZE) // 2

        # --- THUỘC TÍNH NÚT QUAY LẠI (KHẮC PHỤC KÍCH THƯỚC) ---
        self.back_button_rect = pygame.Rect(WIDTH - 130, HEIGHT - 60, 110, 40) 
            
        # --- THUỘC TÍNH VẼ QUÂN CỜ TRONG CHUỒNG ---
        # 0: Top-Left (Green), 1: Top-Right (Blue), 2: Bottom-Right (Yellow), 3: Bottom-Left (Red)
        self.home_base_offsets = [(0, 0), (9*CELL, 0), (9*CELL, 9*CELL), (0, 9*CELL)]
        self.circle_relative_pos = [(2*CELL, 2*CELL), (4*CELL, 2*CELL), 
                                     (2*CELL, 4*CELL), (4*CELL, 4*CELL)]
    
    # --- HÀM PHỤ ÁP DỤNG DỊCH CHUYỂN VỊ TRÍ XÚC XẮC ---
    def _apply_dice_position_offset(self, dice):
        """Áp dụng logic dịch chuyển 20px lên trên và 15px vào trong cho một xúc xắc."""
        MOVE_OFFSET_INWARD = 15 
        MOVE_OFFSET_UP = 20
        CENTER_X = WIDTH / 2
        CENTER_Y = HEIGHT / 2

        # 1. Dịch chuyển 20px lên trên (Chỉ áp dụng cho xúc xắc phía dưới)
        if dice.y > CENTER_Y:
            dice.y -= MOVE_OFFSET_UP
            
        # 2. Dịch chuyển 15px vào trong
        if dice.x < CENTER_X: 
            dice.x += MOVE_OFFSET_INWARD
        else: 
            dice.x -= MOVE_OFFSET_INWARD
        
        if dice.y < CENTER_Y: 
            dice.y += MOVE_OFFSET_INWARD
        elif dice.y > CENTER_Y:
            dice.y -= MOVE_OFFSET_INWARD 

        # 3. Cập nhật Rect (nếu có)
        if hasattr(dice, 'rect') and isinstance(dice.rect, pygame.Rect):
            if dice.rect.centery > CENTER_Y:
                dice.rect.y -= MOVE_OFFSET_UP

            if dice.rect.centerx < CENTER_X: dice.rect.x += MOVE_OFFSET_INWARD
            else: dice.rect.x -= MOVE_OFFSET_INWARD
            
            if dice.rect.centery < CENTER_Y: 
                dice.rect.y += MOVE_OFFSET_INWARD
            elif dice.rect.centery > CENTER_Y - MOVE_OFFSET_UP:
                dice.rect.y -= MOVE_OFFSET_INWARD


    # ==========================================================
    #  VẼ BÀN CỜ
    # ==========================================================

    def draw_board_layout(self):
        """Vẽ 4 chuồng (luôn đầy đủ), 4 vòng tròn (chỉ hoạt động) và 4 ô đích (LUÔN VẼ)."""
        self.screen.fill(WHITE)
        sx, sy = self.start_x, self.start_y

        # === 1. 4 chuồng màu (6x6) - LUÔN VẼ ĐỦ 4 CHUỒNG LỚN ===
        homes = [
            (sx, sy, GREEN, 0),         # pid 0
            (sx + 9*CELL, sy, BLUE, 1), # pid 1
            (sx + 9*CELL, sy + 9*CELL, YELLOW, 2), # pid 2
            (sx, sy + 9*CELL, RED, 3)   # pid 3
        ]
        for x, y, color, pid in homes:
            pygame.draw.rect(self.screen, color, (x, y, 6*CELL, 6*CELL))
            pygame.draw.rect(self.screen, BLACK, (x, y, 6*CELL, 6*CELL), 4)

        # === 2. 4 vòng tròn trong chuồng (VỊ TRÍ ĐỂ QUÂN CHỜ) - CHỈ VẼ CHO PLAYER HOẠT ĐỘNG ===
        for pid, (ox, oy) in enumerate(self.home_base_offsets):
            if pid not in self.active_pids: 
                continue
                
            if pid >= len(PLAYER_COLORS): continue
            color = PLAYER_COLORS[pid]
            for (rx, ry) in self.circle_relative_pos:
                px = int(self.start_x + ox + rx)
                py = int(self.start_y + oy + ry)
                pygame.draw.circle(self.screen, WHITE, (px, py), 18)
                pygame.draw.circle(self.screen, color, (px, py), 4)

        # === 3. Trung tâm và 4 tam giác màu ĐÍCH - LUÔN VẼ ĐẦY ĐỦ 4 MÀU ===
        cx = sx + 6 * CELL
        cy = sy + 6 * CELL

        mid_point = (cx + 1.5 * CELL, cy + 1.5 * CELL)
        top_left = (cx, cy); top_right = (cx + 3 * CELL, cy)
        bottom_left = (cx, cy + 3 * CELL); bottom_right = (cx + 3 * CELL, cy + 3 * CELL)
        
        pygame.draw.polygon(self.screen, BLUE, [top_left, top_right, mid_point])
        pygame.draw.polygon(self.screen, YELLOW, [top_right, bottom_right, mid_point])
        pygame.draw.polygon(self.screen, RED, [bottom_right, bottom_left, mid_point])
        pygame.draw.polygon(self.screen, GREEN, [bottom_left, top_left, mid_point])


    def draw_path(self):
        """Vẽ đường đi, 4 đường về đích (luôn vẽ) và các ô xuất phát (chỉ vẽ cho người chơi hoạt động)."""
        sx, sy = self.start_x, self.start_y
        c = CELL
        path_color = (230, 230, 230)
        
        if not (self.gm and self.gm.board): return

        # 1. Vẽ 52 ô đường đi vòng ngoài
        main_path_from_logic = self.gm.board.path_grid
        for gx, gy in main_path_from_logic:
            if 6 <= gx <= 8 and 6 <= gy <= 8:
                continue
            pygame.draw.rect(self.screen, path_color, (sx + gx*c, sy + gy*c, c, c))
            pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 1)

        # 2. Vẽ 4 đường về đích (HOME LANES) - LUÔN VẼ ĐỦ 4 ĐƯỜNG
        home_lanes_from_logic = self.gm.board.home_lanes
        for pid, lane in enumerate(home_lanes_from_logic):
            if pid >= len(PLAYER_COLORS): continue
            color = PLAYER_COLORS[pid]
            
            # Chỉ vẽ 5 ô đầu tiên của đường về đích
            for i, (gx, gy) in enumerate(lane):
                if i < 5: 
                    pygame.draw.rect(self.screen, color, (sx + gx*c, sy + gy*c, c, c))
                    pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 2)

        # 3. Vẽ 4 ô xuất phát (SPAWN CELL INDICATOR) - CHỈ VẼ CHO PLAYER HOẠT ĐỘNG
        for actual_pid in self.active_pids: 
            gx, gy = self.gm.board.get_spawn_cell(actual_pid)
            color = PLAYER_COLORS[actual_pid]
            center_x = sx + int(gx * c + c / 2); center_y = sy + int(gy * c + c / 2)
            pygame.draw.circle(self.screen, color, (center_x, center_y), 10)
            pygame.draw.circle(self.screen, WHITE, (center_x, center_y), 10, 2)

    def draw_highlight(self):
        """Tô sáng các ô quân có thể di chuyển tới"""
        for gx, gy in self.highlight_cells:
            px = self.start_x + gx * CELL; py = self.start_y + gy * CELL
            rect = pygame.Rect(px, py, CELL, CELL)
            highlight_surface = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            highlight_surface.fill((255, 255, 0, 100))
            self.screen.blit(highlight_surface, (px, py))
            pygame.draw.rect(self.screen, (255, 200, 0), rect, 3)

    def _draw_back_button(self):
        """Vẽ nút quay lại (có icon và căn giữa)."""
        pygame.draw.rect(self.screen, (200, 0, 0), self.back_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.back_button_rect, 2, border_radius=5)

        back_text = self.back_font.render('QUAY LẠI', True, WHITE)
        
        try:
            icon = pygame.image.load("assets/images/back.jpg").convert_alpha()
            icon = pygame.transform.smoothscale(icon, (20, 20)) 
            icon_w, icon_h = icon.get_size()
        except pygame.error:
            icon = None
            icon_w, icon_h = 0, 0

        padding = 5 
        total_width = icon_w + (padding if icon_w > 0 else 0) + back_text.get_width()
        
        center_x = self.back_button_rect.centerx
        center_y = self.back_button_rect.centery
        start_x_for_icon = center_x - (total_width / 2) 

        if icon:
            icon_rect = icon.get_rect(midleft=(start_x_for_icon, center_y))
            self.screen.blit(icon, icon_rect)
            text_start_x = icon_rect.right + padding
        else:
            text_start_x = start_x_for_icon

        text_rect = back_text.get_rect(midleft=(text_start_x, center_y))
        self.screen.blit(back_text, text_rect)

    # ==========================================================
    #  XỬ LÝ SỰ KIỆN (CHO OFFLINE)
    # ==========================================================
    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.back_button_rect.collidepoint(mx, my):
                print("BoardView (Offline): Nút Quay Lại được nhấn!")
                return 'back'

            if self.gm.winner is not None or self.gm.dice_value == -1:
                self.msg = f"Người {self.gm.winner + 1} đã thắng! Game kết thúc."
                return 

            current = self.gm.turn

            # --- 1️⃣ Gieo xúc xắc ---
            if self.gm.dice_value is None:
                if 0 <= current < len(self.dices):
                    dice_of_current_player = self.dices[current]
                    if dice_of_current_player.clicked((mx, my)):
                        val = dice_of_current_player.roll()
                        if self.sound_manager: self.sound_manager.play_sfx('dice')
                        self.last_roll = val; self.msg = f"Người {current+1} gieo được {val}"
                        self.gm.dice_value = val; self.highlight_cells.clear()
                        
                        movable_pieces = self.gm.get_movable_pieces(current, val)
                        if movable_pieces:
                            self.msg += ": Chọn quân để di chuyển."
                            for piece in movable_pieces:
                                dest_cell = self.gm.get_destination_cell(piece, val)
                                if dest_cell: self.highlight_cells.append(dest_cell)
                        else:
                            self.msg += ": Không có nước đi."
                            if val != 6: self.gm.next_turn()
                            else: self.gm.dice_value = None
                        return

            # --- 2️⃣ Bấm chọn ô đã được highlight để di chuyển quân ---
            if self.highlight_cells:
                gx = (mx - self.start_x) // CELL; gy = (my - self.start_y) // CELL
                if (gx, gy) in self.highlight_cells:
                    piece_to_move = self.gm.find_piece_for_move(current, (gx, gy))
                    if piece_to_move:
                        
                        (kick_msg, just_finished, game_won) = self.gm.move_piece(piece_to_move)
                        
                        base_msg = f"Người {current+1} đã di chuyển quân."

                        if game_won:
                            self.msg = f"Người {current+1} THẮNG CUỘC!"
                            if self.sound_manager: self.sound_manager.play_sfx('win')
                        elif kick_msg:
                            kicked_player = getattr(kick_msg, "owner", None)
                            kicked_id = getattr(kick_msg, "id", None)

                            if kicked_player is not None and kicked_id is not None:
                                self.msg = f"{base_msg} → Đá quân của Người {kicked_player+1} (quân {kicked_id+1})"
                            else:
                                self.msg = f"{base_msg} → Đá 1 quân!"

                            if self.sound_manager: 
                                self.sound_manager.play_sfx('kick')

                        elif just_finished:
                            self.msg = base_msg + " (Đã về 1 quân!)"
                            if self.sound_manager: self.sound_manager.play_sfx('done') 
                        else:
                            piece_id = piece_to_move.id if hasattr(piece_to_move, 'id') else '?'
                            self.msg = f"{base_msg} → Quân {piece_id + 1}"
                            if self.sound_manager: 
                                self.sound_manager.play_sfx('move')
                        
                        self.highlight_cells.clear()
                        return
    # ==========================================================
    #  VẼ TOÀN BỘ (CHO OFFLINE)
    # ==========================================================
    def draw(self):
        """Vẽ cho chế độ OFFLINE."""
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight()

        # --- Vẽ quân cờ ---
        for pid in range(self.gm.num_players):
            offset_index = self.player_map.get(pid)
            if offset_index is None:
                continue

            if offset_index >= len(PLAYER_COLORS) or offset_index >= len(self.home_base_offsets):
                continue
            
            pieces_of_player = self.gm.players[pid]
            player_color = PLAYER_COLORS[offset_index]
            ox, oy = self.home_base_offsets[offset_index]

            for piece in pieces_of_player:
                if piece.finished:
                    continue
                px, py = 0, 0

                if piece.path_index == -1:
                    # Vị trí trong chuồng
                    try:
                        rx, ry = self.circle_relative_pos[piece.id]
                        px = int(self.start_x + ox + rx)
                        py = int(self.start_y + oy + ry)
                    except (IndexError, TypeError, AttributeError):
                        px = int(self.start_x + ox + 3*CELL)
                        py = int(self.start_y + oy + 3*CELL)
                else:
                    # Vị trí trên đường đi
                    path = self.gm.board.get_path_for_player(offset_index)
                    if piece.path_index < len(path):
                        gx, gy = path[piece.path_index]
                        px = self.start_x + gx * CELL + CELL // 2
                        py = self.start_y + gy * CELL + CELL // 2
                    else:
                        continue

                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)
                
                id_text = self.msg_font.render(str(piece.id + 1), True, WHITE)
                text_rect = id_text.get_rect(center=(px, py))
                self.screen.blit(id_text, text_rect)

        # --- Vẽ xúc xắc ---
        for i, dice in enumerate(self.dices):
            dice.active = (i == self.gm.turn)
            dice.draw(self.screen)

        # --- Vẽ thông báo msg ---
        if hasattr(self, 'msg') and self.msg:
            msg_render = self.msg_font.render(self.msg, True, BLACK)
            self.screen.blit(msg_render, (12, HEIGHT - 40))

        # --- Nút quay lại ---
        self._draw_back_button()

        pygame.display.flip()
        self.clock.tick(60)


    def update_dice_display(self, player_id, value):
        if 0 <= player_id < len(self.dices):
            self.dices[player_id].set_value(value)

    # ==========================================================
    #  VẼ CHO CHẾ ĐỘ ONLINE
    # ==========================================================
    def draw_from_state(self, game_state):
        """Vẽ cho chế độ ONLINE."""
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight()

        # 2️⃣ Vẽ quân cờ dựa trên game_state
        players_pieces_data = game_state.get('players_pieces', [])
        for pid, pieces_data in enumerate(players_pieces_data):
            # Lấy Board ID thực tế: 0 hoặc 2
            offset_index = self.player_map.get(pid)
            if offset_index is None: continue
            
            player_color = PLAYER_COLORS[offset_index]
            ox, oy = self.home_base_offsets[offset_index] # Lấy tọa độ chuồng (Board ID 0 hoặc 2)

            for piece_data in pieces_data:
                # Trích xuất và gán piece_id ngay tại đây
                piece_id = piece_data.get('id', -1) # <--- SỬA: Đã gán giá trị
                path_index = piece_data.get('path_index', -1)
                is_finished = piece_data.get('finished', False)
                
                if is_finished: continue

                # Khởi tạo px, py trước khi sử dụng
                px, py = 0, 0 
                
                if path_index == -1:
                    # Vị trí trong chuồng
                    try:
                        rx, ry = self.circle_relative_pos[piece_id]
                        px = int(self.start_x + ox + rx) 
                        py = int(self.start_y + oy + ry)
                    except (IndexError, TypeError, AttributeError):
                        px = int(self.start_x + ox + 3*CELL)
                        py = int(self.start_y + oy + 3*CELL)
                else:
                    path = self.gm.board.get_path_for_player(offset_index)
                    if path_index < len(path):
                        gx, gy = path[path_index]
                        px = self.start_x + gx * CELL + CELL // 2
                        py = self.start_y + gy * CELL + CELL // 2
                    else:
                        continue

                # VẼ QUÂN CỜ VÀ ID (Đã nằm trong vòng lặp và sử dụng piece_id)
                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)
                
                if piece_id != -1:
                    id_text = self.msg_font.render(str(piece_id + 1), True, WHITE)
                    text_rect = id_text.get_rect(center=(px, py))
                    self.screen.blit(id_text, text_rect)

        # 3️⃣ Vẽ xúc xắc
        dice_val = game_state.get('dice_value')
        current_turn = game_state.get('turn', -1)
        num_players_in_state = game_state.get('num_players', 0)

        # Đảm bảo self.dices có đủ số lượng cho state hiện tại và áp dụng dịch chuyển
        while len(self.dices) < num_players_in_state:
            new_pid = len(self.dices)
            
            if new_pid < len(self.active_pids):
                actual_pid = self.active_pids[new_pid]
            else:
                break 

            if actual_pid in DICE_POSITIONS and actual_pid < len(PLAYER_COLORS):
                x, y = DICE_POSITIONS[actual_pid]
                color = PLAYER_COLORS[actual_pid]
                new_dice = DiceView(x, y, color, new_pid)
                self._apply_dice_position_offset(new_dice) # Áp dụng dịch chuyển
                self.dices.append(new_dice)
            else:
                break

        for i, dice in enumerate(self.dices):
            if i < num_players_in_state:
                dice.active = (i == current_turn)
                if i == current_turn and dice_val is not None:
                    dice.set_value(dice_val)
                elif not dice.active:
                    dice.set_value(1)
                dice.draw(self.screen)

        # 4️⃣ Vẽ thanh thông báo
        if hasattr(self, 'msg') and self.msg:
            msg_surface = self.msg_font.render(self.msg, True, BLACK)
            self.screen.blit(msg_surface, (20, HEIGHT - 40))

        # 5️⃣ Nút quay lại
        self._draw_back_button()

        pygame.display.flip()
        self.clock.tick(60)