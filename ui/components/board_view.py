# ui/components/board_view.py
import pygame
from core import rules
from utils.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, WHITE, BLACK, PLAYER_COLORS, DICE_POSITIONS, FONT
from ui.components.dice_view import DiceView

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
        for pid, color in enumerate(PLAYER_COLORS[:self.gm.num_players]):
            x, y = DICE_POSITIONS[pid]
            self.dices.append(DiceView(x, y, color, pid))

        self.start_x = (WIDTH - CELL * BOARD_SIZE) // 2
        self.start_y = (HEIGHT - CELL * BOARD_SIZE) // 2

        # --- THÊM THUỘC TÍNH CHO NÚT QUAY LẠI ---
        self.back_button_rect = pygame.Rect(WIDTH - 130, HEIGHT - 60, 110, 40)
        try:
            self.back_font = pygame.font.SysFont("Arial", 18, bold=True)
        except pygame.error:
            self.back_font = pygame.font.Font(None, 24)
        # -----------------------------------------

    # ... (Hàm draw_board_layout và draw_path giữ nguyên) ...
    def draw_board_layout(self):
        """Vẽ chuồng 4 màu, vòng tròn chờ, và ô trung tâm 3x3 làm ĐÍCH."""
        self.screen.fill(WHITE)
        sx, sy = self.start_x, self.start_y

        # === 4 chuồng màu (6x6) ===
        homes = [
            (sx, sy, GREEN),
            (sx + 9*CELL, sy, BLUE),
            (sx + 9*CELL, sy + 9*CELL, YELLOW),
            (sx, sy + 9*CELL, RED)
        ]
        for x, y, color in homes:
            pygame.draw.rect(self.screen, color, (x, y, 6*CELL, 6*CELL))
            pygame.draw.rect(self.screen, BLACK, (x, y, 6*CELL, 6*CELL), 4)

        # === 4 vòng tròn trong chuồng (chỗ chờ quân) ===
        offsets = [(1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5)]
        for pid, (ox, oy) in enumerate(offsets):
            color = PLAYER_COLORS[pid]
            for i in range(4):
                px = int(self.start_x + (ox + (i % 2) * 2) * CELL)
                py = int(self.start_y + (oy + (i // 2) * 2) * CELL)
                pygame.draw.circle(self.screen, WHITE, (px, py), 18)
                pygame.draw.circle(self.screen, color, (px, py), 4)

        # === Trung tâm 9 ô (3x3) - vẽ nền và viền trước ===
        cx = sx + 6 * CELL
        cy = sy + 6 * CELL
        for i in range(3):
            for j in range(3):
                rect = pygame.Rect(cx + i*CELL, cy + j*CELL, CELL, CELL)
                pygame.draw.rect(self.screen, WHITE, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)

        # === Vẽ 4 tam giác màu ĐÍCH (ĐÃ CẬP NHẬT MÀU SẮC) ===
        mid_point = (cx + 1.5 * CELL, cy + 1.5 * CELL)
        top_left = (cx, cy); top_right = (cx + 3 * CELL, cy)
        bottom_left = (cx, cy + 3 * CELL); bottom_right = (cx + 3 * CELL, cy + 3 * CELL)
        pygame.draw.polygon(self.screen, BLUE,   [top_left, top_right, mid_point])
        pygame.draw.polygon(self.screen, YELLOW, [top_right, bottom_right, mid_point])
        pygame.draw.polygon(self.screen, RED,    [bottom_right, bottom_left, mid_point])
        pygame.draw.polygon(self.screen, GREEN,  [bottom_left, top_left, mid_point])

    def draw_path(self):
        """Vẽ đường đi và các thành phần trên bàn cờ."""
        sx, sy = self.start_x, self.start_y
        c = CELL
        path_color = (230, 230, 230)
        
        main_path_from_logic = self.gm.board.path_grid
        for gx, gy in main_path_from_logic:
            pygame.draw.rect(self.screen, path_color, (sx + gx*c, sy + gy*c, c, c))
            pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 1)

        home_lanes_from_logic = self.gm.board.home_lanes
        for pid, lane in enumerate(home_lanes_from_logic):
            color = PLAYER_COLORS[pid]
            for gx, gy in lane:
                pygame.draw.rect(self.screen, color, (sx + gx*c, sy + gy*c, c, c))
                pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 2)
        
        for pid in range(self.gm.num_players):
            gx, gy = self.gm.board.get_spawn_cell(pid)
            color = PLAYER_COLORS[pid]
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

    # --- THÊM HÀM VẼ NÚT QUAY LẠI ---
    def _draw_back_button(self):
        """Vẽ nút quay lại (dùng cho cả draw và draw_from_state)."""
        pygame.draw.rect(self.screen, (200, 0, 0), self.back_button_rect, border_radius=5) # Nền đỏ sẫm
        pygame.draw.rect(self.screen, BLACK, self.back_button_rect, 2, border_radius=5) # Viền đen
        back_text = self.back_font.render('QUAY LẠI', True, WHITE)
        text_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, text_rect)
    # ---------------------------------

    def handle_events(self, event):
        """Xử lý sự kiện cho chế độ OFFLINE."""
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # --- KIỂM TRA CLICK NÚT QUAY LẠI ---
            if self.back_button_rect.collidepoint(mx, my):
                print("BoardView (Offline): Nút Quay Lại được nhấn!")
                return 'back' # Trả về tín hiệu
            # ---------------------------------

            current = self.gm.turn

            # --- 1️⃣ Gieo xúc xắc ---
            if self.gm.dice_value is None:
                if 0 <= current < len(self.dices): # Kiểm tra an toàn
                    dice_of_current_player = self.dices[current]
                    if dice_of_current_player.clicked((mx, my)):
                        val = dice_of_current_player.roll()
                        if self.sound_manager: self.sound_manager.play_sfx('dice')
                        self.last_roll = val
                        self.msg = f"Người {current+1} gieo được {val}"
                        self.gm.dice_value = val
                        self.highlight_cells.clear()
                        # ... (logic movable_pieces giữ nguyên) ...
                        movable_pieces = self.gm.get_movable_pieces(current, val)
                        if movable_pieces:
                            self.msg += " → Chọn quân để di chuyển"
                            for piece in movable_pieces:
                                dest_cell = self.gm.get_destination_cell(piece, val)
                                if dest_cell: self.highlight_cells.append(dest_cell)
                        else:
                            self.msg += ". Không có quân nào có thể đi."
                            if val != 6: self.gm.next_turn()
                            else: self.gm.dice_value = None
                        return # Kết thúc xử lý click

            # --- 2️⃣ Bấm chọn ô đã được highlight để di chuyển quân ---
            if self.highlight_cells:
                gx = (mx - self.start_x) // CELL
                gy = (my - self.start_y) // CELL
                if (gx, gy) in self.highlight_cells:
                    piece_to_move = self.gm.find_piece_for_move(current, (gx, gy))
                    if piece_to_move:
                        kick_msg = self.gm.move_piece(piece_to_move)
                        base_msg = f"Người {current+1} đã di chuyển quân."
                        if kick_msg:
                            self.msg = base_msg + kick_msg
                            if self.sound_manager: self.sound_manager.play_sfx('kick')
                        else:
                            self.msg = base_msg
                            if self.sound_manager: self.sound_manager.play_sfx('move')
                        self.highlight_cells.clear()
                        return # Kết thúc xử lý click

    def draw(self):
        """Vẽ cho chế độ OFFLINE."""
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight()
        # ... (code vẽ quân cờ giữ nguyên) ...
        home_offsets = [(1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5)]
        for pid in range(self.gm.num_players):
            pieces_of_player = self.gm.players[pid]; player_color = PLAYER_COLORS[pid]
            for piece in pieces_of_player:
                if piece.finished: continue
                px, py = 0, 0
                if piece.path_index == -1:
                    ox, oy = home_offsets[pid]
                    px = int(self.start_x + (ox + (piece.id % 2) * 2) * CELL)
                    py = int(self.start_y + (oy + (piece.id // 2) * 2) * CELL)
                else:
                    path = self.gm.board.get_path_for_player(pid)
                    if piece.path_index < len(path):
                        gx, gy = path[piece.path_index]
                        px = self.start_x + gx * CELL + CELL // 2
                        py = self.start_y + gy * CELL + CELL // 2
                    else: continue
                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)
                id_font = pygame.font.Font(None, 24); id_text = id_font.render(str(piece.id + 1), True, WHITE)
                text_rect = id_text.get_rect(center=(px, py)); self.screen.blit(id_text, text_rect)

        # --- Vẽ xúc xắc, thông báo, và nút quay lại ---
        for i, dice in enumerate(self.dices):
            dice.active = (i == self.gm.turn); dice.draw(self.screen)
        msg_render = FONT.render(self.msg, True, BLACK)
        self.screen.blit(msg_render, (20, HEIGHT - 40))
        self._draw_back_button() # <-- VẼ NÚT
        pygame.display.flip()
        self.clock.tick(60)


    def update_dice_display(self, player_id, value):
        if 0 <= player_id < len(self.dices):
            self.dices[player_id].set_value(value)

    def draw_from_state(self, game_state):
        """Vẽ cho chế độ ONLINE."""
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight() # <-- ĐÃ THÊM GỌI VẼ HIGHLIGHT

        # ... (code vẽ quân cờ từ state giữ nguyên) ...
        players_pieces_data = game_state.get('players_pieces', [])
        home_offsets = [(1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5)]
        for pid, pieces_data in enumerate(players_pieces_data):
            if pid >= len(PLAYER_COLORS): continue # Tránh lỗi nếu state có nhiều người chơi hơn màu
            player_color = PLAYER_COLORS[pid]
            for piece_data in pieces_data:
                path_index = piece_data.get('path_index', -1); is_finished = piece_data.get('finished', False)
                piece_id = piece_data.get('id', -1)
                if is_finished: continue
                px, py = 0, 0
                if path_index == -1:
                    if pid < len(home_offsets):
                        ox, oy = home_offsets[pid]
                        if piece_id != -1:
                            px = int(self.start_x + (ox + (piece_id % 2) * 2) * CELL)
                            py = int(self.start_y + (oy + (piece_id // 2) * 2) * CELL)
                        else: continue
                else:
                    if self.gm and self.gm.board: # Vẫn dùng dummy board để lấy path
                       path = self.gm.board.get_path_for_player(pid)
                       if path_index < len(path):
                           gx, gy = path[path_index]
                           px = self.start_x + gx * CELL + CELL // 2
                           py = self.start_y + gy * CELL + CELL // 2
                       else: continue
                    else: continue
                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)
                if piece_id != -1:
                    id_font = pygame.font.Font(None, 24); id_text = id_font.render(str(piece_id + 1), True, WHITE)
                    text_rect = id_text.get_rect(center=(px, py)); self.screen.blit(id_text, text_rect)

        # --- Vẽ Xúc Xắc từ state ---
        dice_val = game_state.get('dice_value'); current_turn = game_state.get('turn', -1)
        # Đảm bảo self.dices có đủ số lượng
        while len(self.dices) < game_state.get('num_players', 0):
             pid = len(self.dices)
             x, y = DICE_POSITIONS[pid]; color = PLAYER_COLORS[pid]
             self.dices.append(DiceView(x, y, color, pid))
             
        for i, dice in enumerate(self.dices):
            if i < game_state.get('num_players', 0): # Chỉ vẽ xúc xắc cho người chơi tồn tại
                dice.active = (i == current_turn)
                if i == current_turn and dice_val is not None: dice.set_value(dice_val)
                elif not dice.active: dice.set_value(1)
                dice.draw(self.screen)

        # --- VẼ NÚT QUAY LẠI (CHO ONLINE) ---
        self._draw_back_button()
        # ------------------------------------