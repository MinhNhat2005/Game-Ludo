# ui/components/board_view.py
import pygame
from core import rules
from utils.constants import (
    WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, WHITE, BLACK,
    PLAYER_COLORS, DICE_POSITIONS, FONT, CELL
)
from ui.components.dice_view import DiceView

# CELL và BOARD_SIZE có thể đã được định nghĩa trong constants,
# nhưng chúng ta giữ lại ở đây nếu bạn đang dùng chúng cục bộ.
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
        # Đảm bảo gm.num_players không vượt quá số lượng màu/vị trí
        num_players_to_init = min(self.gm.num_players, len(PLAYER_COLORS), len(DICE_POSITIONS))
        for pid, color in enumerate(PLAYER_COLORS[:num_players_to_init]):
            if pid in DICE_POSITIONS: # Kiểm tra xem pid có tồn tại trong DICE_POSITIONS không
                x, y = DICE_POSITIONS[pid]
                self.dices.append(DiceView(x, y, color, pid))
            else:
                print(f"Cảnh báo: Không tìm thấy vị trí xúc xắc cho player ID {pid}")


        self.start_x = (WIDTH - CELL * BOARD_SIZE) // 2
        self.start_y = (HEIGHT - CELL * BOARD_SIZE) // 2

        # --- THUỘC TÍNH NÚT QUAY LẠI ---
        self.back_button_rect = pygame.Rect(WIDTH - 130, HEIGHT - 60, 110, 40)
        try:
            self.back_font = pygame.font.SysFont("Arial", 18, bold=True)
        except pygame.error:
            self.back_font = pygame.font.Font(None, 24)
            
        # --- THUỘC TÍNH VẼ QUÂN CỜ TRONG CHUỒNG (ĐÃ CĂN GIỮA) ---
        # Tọa độ offset GỐC của 4 chuồng
        self.home_base_offsets = [(0, 0), (9*CELL, 0), (9*CELL, 9*CELL), (0, 9*CELL)]
        # Tọa độ TƯƠNG ĐỐI của 4 quân cờ trong chuồng (cân giữa)
        # Ánh xạ piece.id (0, 1, 2, 3) tới các vị trí này
        self.circle_relative_pos = [(2*CELL, 2*CELL), (4*CELL, 2*CELL), 
                                    (2*CELL, 4*CELL), (4*CELL, 4*CELL)]

    # ==========================================================
    #  VẼ BÀN CỜ
    # ==========================================================

    def draw_board_layout(self):
        """Vẽ chuồng 4 màu, vòng tròn chờ (cân giữa), và ô trung tâm (không sọc)."""
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

        # === 4 vòng tròn trong chuồng (ĐÃ CĂN LẠI CHÍNH GIỮA) ===
        for pid, (ox, oy) in enumerate(self.home_base_offsets):
            if pid >= len(PLAYER_COLORS): continue
            color = PLAYER_COLORS[pid]
            for (rx, ry) in self.circle_relative_pos:
                px = int(self.start_x + ox + rx)
                py = int(self.start_y + oy + ry)
                pygame.draw.circle(self.screen, WHITE, (px, py), 18)
                pygame.draw.circle(self.screen, color, (px, py), 4)

        # === Trung tâm (khối 3x3) - ĐÃ BỎ SỌC & VIỀN ---
        cx = sx + 6 * CELL
        cy = sy + 6 * CELL

        # --- ĐÃ XÓA CODE VẼ 9 Ô VUÔNG VÀ VIỀN 3x3 ---
        # 1. (Đã xóa) Vẽ nền trắng lót
        # 2. (Đã xóa) Vẽ viền đen xung quanh

        # === Vẽ 4 tam giác màu ĐÍCH (Giữ nguyên) ===
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
        
        if not (self.gm and self.gm.board): return

        # 1. Vẽ 52 ô đường đi vòng ngoài (Giữ nguyên logic bỏ qua trung tâm)
        main_path_from_logic = self.gm.board.path_grid
        for gx, gy in main_path_from_logic:
            if 6 <= gx <= 8 and 6 <= gy <= 8:
                continue
            pygame.draw.rect(self.screen, path_color, (sx + gx*c, sy + gy*c, c, c))
            pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 1)

        # 2. Vẽ 4 đường về đích (ĐÃ SỬA LẠI)
        home_lanes_from_logic = self.gm.board.home_lanes
        for pid, lane in enumerate(home_lanes_from_logic):
            if pid >= len(PLAYER_COLORS): continue
            color = PLAYER_COLORS[pid]
            
            # --- LOGIC SỬA LỖI: Chỉ vẽ 5 ô đầu tiên của đường về đích ---
            # Bỏ qua ô cuối cùng (là ô nằm trong trung tâm)
            for i, (gx, gy) in enumerate(lane):
                if i < 5: # Chỉ vẽ 5 ô đầu (index 0 đến 4)
                    pygame.draw.rect(self.screen, color, (sx + gx*c, sy + gy*c, c, c))
                    pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 2)
            # -----------------------------------------------------------

        # 3. Vẽ 4 ô xuất phát (Giữ nguyên)
        for pid in range(self.gm.num_players):
            if pid >= len(PLAYER_COLORS): continue
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

    def _draw_back_button(self):
        """Vẽ nút quay lại (dùng cho cả draw và draw_from_state)."""
        pygame.draw.rect(self.screen, (200, 0, 0), self.back_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.back_button_rect, 2, border_radius=5)
        back_text = self.back_font.render('QUAY LẠI', True, WHITE)
        text_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, text_rect)

    # ==========================================================
    #  XỬ LÝ SỰ KIỆN (CHO OFFLINE)
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

            # --- KIỂM TRA GAME OVER ---
            if self.gm.winner is not None or self.gm.dice_value == -1:
                self.msg = f"Người {self.gm.winner + 1} đã thắng! Game kết thúc."
                return # Không cho chơi nữa
            # --------------------------

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
                            self.msg += " → Chọn quân để di chuyển"
                            for piece in movable_pieces:
                                dest_cell = self.gm.get_destination_cell(piece, val)
                                if dest_cell: self.highlight_cells.append(dest_cell)
                        else:
                            self.msg += ". Không có quân nào có thể đi."
                            if val != 6: self.gm.next_turn()
                            else: self.gm.dice_value = None
                        return

            # --- 2️⃣ Bấm chọn ô đã được highlight để di chuyển quân ---
            if self.highlight_cells:
                gx = (mx - self.start_x) // CELL; gy = (my - self.start_y) // CELL
                if (gx, gy) in self.highlight_cells:
                    piece_to_move = self.gm.find_piece_for_move(current, (gx, gy))
                    if piece_to_move:
                        
                        # --- ĐÃ SỬA LỖI Ở ĐÂY ---
                        # 1. Giải nén tuple 3 giá trị
                        (kick_msg, just_finished, game_won) = self.gm.move_piece(piece_to_move)
                        
                        base_msg = f"Người {current+1} đã di chuyển quân."

                        # 2. Xử lý âm thanh và thông báo theo thứ tự ưu tiên
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
                            self.msg = base_msg
                            if self.sound_manager: self.sound_manager.play_sfx('move')
                        # -------------------------
                        
                        self.highlight_cells.clear()
                        return
    # ==========================================================
    #  VẼ TOÀN BỘ (CHO OFFLINE)
    # ==========================================================
    def draw(self):
        """Vẽ cho chế độ OFFLINE."""
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight()

        # --- Vẽ quân cờ ---
        for pid in range(self.gm.num_players):
            if pid >= len(PLAYER_COLORS) or pid >= len(self.home_base_offsets): continue
            pieces_of_player = self.gm.players[pid]
            player_color = PLAYER_COLORS[pid]
            ox, oy = self.home_base_offsets[pid] # Lấy offset gốc của chuồng

            for piece in pieces_of_player:
                if piece.finished: continue
                px, py = 0, 0

                if piece.path_index == -1:
                    # --- LOGIC CĂN GIỮA MỚI (ĐÃ SỬA) ---
                    try:
                        rx, ry = self.circle_relative_pos[piece.id] 
                        px = int(self.start_x + ox + rx)
                        py = int(self.start_y + oy + ry)
                    except (IndexError, TypeError, AttributeError) as e:
                        px = int(self.start_x + ox + 3*CELL); py = int(self.start_y + oy + 3*CELL)
                        print(f"Lỗi: piece id không hợp lệ (player {pid}, piece {piece.id}): {e}")
                    # --- KẾT THÚC LOGIC MỚI ---
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

        # --- Vẽ các thành phần khác ---
        for i, dice in enumerate(self.dices):
            dice.active = (i == self.gm.turn); dice.draw(self.screen)
        msg_render = FONT.render(self.msg, True, BLACK)
        self.screen.blit(msg_render, (20, HEIGHT - 40))
        self._draw_back_button()
        pygame.display.flip()
        self.clock.tick(60)


    def update_dice_display(self, player_id, value):
        if 0 <= player_id < len(self.dices):
            self.dices[player_id].set_value(value)

    # ==========================================================
    #  VẼ CHO CHẾ ĐỘ ONLINE
    # ==========================================================
    def draw_from_state(self, game_state):
        """Vẽ cho chế độ ONLINE, bao gồm thanh thông báo."""
        # 1️⃣ Vẽ bàn cờ
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight()

        # 2️⃣ Vẽ quân cờ dựa trên game_state
        players_pieces_data = game_state.get('players_pieces', [])
        for pid, pieces_data in enumerate(players_pieces_data):
            if pid >= len(PLAYER_COLORS) or pid >= len(self.home_base_offsets): 
                continue
            player_color = PLAYER_COLORS[pid]
            ox, oy = self.home_base_offsets[pid]

            for piece_data in pieces_data:
                path_index = piece_data.get('path_index', -1)
                is_finished = piece_data.get('finished', False)
                piece_id = piece_data.get('id', -1)
                if is_finished: 
                    continue

                px, py = 0, 0
                if path_index == -1:
                    try:
                        rx, ry = self.circle_relative_pos[piece_id]
                        px = int(self.start_x + ox + rx)
                        py = int(self.start_y + oy + ry)
                    except (IndexError, TypeError, AttributeError):
                        px = int(self.start_x + ox + 3*CELL)
                        py = int(self.start_y + oy + 3*CELL)
                else:
                    if self.gm and self.gm.board:
                        path = self.gm.board.get_path_for_player(pid)
                        if path_index < len(path):
                            gx, gy = path[path_index]
                            px = self.start_x + gx * CELL + CELL // 2
                            py = self.start_y + gy * CELL + CELL // 2
                        else:
                            continue

                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)
                if piece_id != -1:
                    id_font = pygame.font.Font(None, 24)
                    id_text = id_font.render(str(piece_id + 1), True, WHITE)
                    text_rect = id_text.get_rect(center=(px, py))
                    self.screen.blit(id_text, text_rect)

        # 3️⃣ Vẽ xúc xắc từ state
        dice_val = game_state.get('dice_value')
        current_turn = game_state.get('turn', -1)
        num_players_in_state = game_state.get('num_players', 0)

        # Tạo dice nếu chưa đủ
        while len(self.dices) < num_players_in_state:
            new_pid = len(self.dices)
            if new_pid in DICE_POSITIONS and new_pid < len(PLAYER_COLORS):
                x, y = DICE_POSITIONS[new_pid]
                color = PLAYER_COLORS[new_pid]
                self.dices.append(DiceView(x, y, color, new_pid))
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

        # 4️⃣ Vẽ thanh thông báo phía dưới
        if hasattr(self, 'msg') and self.msg:
            msg_surface = FONT.render(self.msg, True, BLACK)
            self.screen.blit(msg_surface, (20, HEIGHT - 40))

        # 5️⃣ Vẽ nút quay lại
        self._draw_back_button()

        # 6️⃣ Cập nhật màn hình
        pygame.display.flip()
        self.clock.tick(60)


        # --- VẼ NÚT QUAY LẠI (CHO ONLINE) ---
        self._draw_back_button()