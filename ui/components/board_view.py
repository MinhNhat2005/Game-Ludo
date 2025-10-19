# ui/components/board_view.py
import pygame
from core import rules
from utils.constants import WIDTH, HEIGHT, RED, BLUE, GREEN, YELLOW, WHITE, BLACK, PLAYER_COLORS, DICE_POSITIONS, FONT
from ui.components.dice_view import DiceView

CELL = 50
BOARD_SIZE = 15

class BoardView:
    def __init__(self, screen, game_manager, players):
        self.screen = screen
        self.gm = game_manager
        self.players = players
        self.clock = pygame.time.Clock()
        self.msg = "Click xúc xắc để bắt đầu!"
        self.last_roll = None
        self.highlight_cells = []  # 🌟 danh sách ô cần tô sáng

        # khởi tạo xúc xắc
        self.dices = []
        for pid, color in enumerate(PLAYER_COLORS[:self.gm.num_players]):
            x, y = DICE_POSITIONS[pid]
            self.dices.append(DiceView(x, y, color, pid))

        self.start_x = (WIDTH - CELL * BOARD_SIZE) // 2
        self.start_y = (HEIGHT - CELL * BOARD_SIZE) // 2

    # ==========================================================
    #  VẼ BÀN CỜ
    # ==========================================================
    # Trong file: ui/components/board_view.py

    def draw_board_layout(self):
        """Vẽ chuồng 4 màu, vòng tròn chờ, và ô trung tâm 3x3 làm ĐÍCH."""
        self.screen.fill(WHITE)
        sx, sy = self.start_x, self.start_y

        # === 4 chuồng màu (6x6) === (Không thay đổi)
        homes = [
            (sx, sy, GREEN),
            (sx + 9*CELL, sy, BLUE),
            (sx + 9*CELL, sy + 9*CELL, YELLOW),
            (sx, sy + 9*CELL, RED)
        ]
        for x, y, color in homes:
            pygame.draw.rect(self.screen, color, (x, y, 6*CELL, 6*CELL))
            pygame.draw.rect(self.screen, BLACK, (x, y, 6*CELL, 6*CELL), 4)

        # === 4 vòng tròn trong chuồng (chỗ chờ quân) === (Không thay đổi)
        offsets = [(1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5)]
        for pid, (ox, oy) in enumerate(offsets):
            color = PLAYER_COLORS[pid]
            for i in range(4):
                px = int(self.start_x + (ox + (i % 2) * 2) * CELL)
                py = int(self.start_y + (oy + (i // 2) * 2) * CELL)
                pygame.draw.circle(self.screen, WHITE, (px, py), 18)
                pygame.draw.circle(self.screen, color, (px, py), 4)

        # === Trung tâm 9 ô (3x3) - vẽ nền và viền trước === (Không thay đổi)
        cx = sx + 6 * CELL
        cy = sy + 6 * CELL
        for i in range(3):
            for j in range(3):
                rect = pygame.Rect(cx + i*CELL, cy + j*CELL, CELL, CELL)
                pygame.draw.rect(self.screen, WHITE, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)

        # === Vẽ 4 tam giác màu ĐÍCH (ĐÃ CẬP NHẬT MÀU SẮC) ===
        mid_point = (cx + 1.5 * CELL, cy + 1.5 * CELL)
        top_left = (cx, cy)
        top_right = (cx + 3 * CELL, cy)
        bottom_left = (cx, cy + 3 * CELL)
        bottom_right = (cx + 3 * CELL, cy + 3 * CELL)

        # Hướng về đích mới:
        # - Trên -> Dưới: BLUE
        # - Phải -> Trái: YELLOW
        # - Dưới -> Lên: RED
        # - Trái -> Phải: GREEN
        pygame.draw.polygon(self.screen, BLUE,   [top_left, top_right, mid_point])
        pygame.draw.polygon(self.screen, YELLOW, [top_right, bottom_right, mid_point])
        pygame.draw.polygon(self.screen, RED,    [bottom_right, bottom_left, mid_point])
        pygame.draw.polygon(self.screen, GREEN,  [bottom_left, top_left, mid_point])

    def draw_path(self):
        """
        Vẽ đường đi và các thành phần trên bàn cờ.
        Tất cả tọa độ được lấy từ self.gm.board để đảm bảo đồng bộ.
        """
        sx, sy = self.start_x, self.start_y
        c = CELL
        path_color = (230, 230, 230)
        
        # Lấy đường đi 52 ô CHUẨN từ logic để vẽ
        main_path_from_logic = self.gm.board.path_grid
        for gx, gy in main_path_from_logic:
            pygame.draw.rect(self.screen, path_color, (sx + gx*c, sy + gy*c, c, c))
            pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 1)

        # Lấy 4 đường về đích CHUẨN từ logic để vẽ
        home_lanes_from_logic = self.gm.board.home_lanes
        for pid, lane in enumerate(home_lanes_from_logic):
            color = PLAYER_COLORS[pid]
            for gx, gy in lane:
                pygame.draw.rect(self.screen, color, (sx + gx*c, sy + gy*c, c, c))
                pygame.draw.rect(self.screen, BLACK, (sx + gx*c, sy + gy*c, c, c), 2)
        
        # Lấy 4 ô xuất phát CHUẨN từ logic để vẽ
        for pid in range(self.gm.num_players):
            gx, gy = self.gm.board.get_spawn_cell(pid)
            color = PLAYER_COLORS[pid]
            center_x = sx + int(gx * c + c / 2)
            center_y = sy + int(gy * c + c / 2)
            pygame.draw.circle(self.screen, color, (center_x, center_y), 10)
            pygame.draw.circle(self.screen, WHITE, (center_x, center_y), 10, 2)

    # ==========================================================
    #  TÔ SÁNG Ô KHẢ THI
    # ==========================================================
    def draw_highlight(self):
        """Tô sáng các ô quân có thể di chuyển tới"""
        for gx, gy in self.highlight_cells:
            px = self.start_x + gx * CELL
            py = self.start_y + gy * CELL
            rect = pygame.Rect(px, py, CELL, CELL)
            # Dùng surface để vẽ highlight bán trong suốt
            highlight_surface = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            highlight_surface.fill((255, 255, 0, 100)) # Vàng, 100/255 độ trong suốt
            self.screen.blit(highlight_surface, (px, py))
            pygame.draw.rect(self.screen, (255, 200, 0), rect, 3)  # viền vàng đậm

   # Trong file: ui/components/board_view.py

    # ==========================================================
    #  XỬ LÝ SỰ KIỆN
    # ==========================================================
    def handle_events(self, event): # <--- THÊM 'event' VÀO ĐÂY
        # Vòng lặp "for e in pygame.event.get():" đã được XÓA
        # vì bây giờ chúng ta xử lý từng sự kiện được truyền vào.
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos # Sử dụng trực tiếp 'event.pos'
            current = self.gm.turn

            # --- 1️⃣ Gieo xúc xắc ---
            if self.gm.dice_value is None:
                dice_of_current_player = self.dices[current]
                if dice_of_current_player.clicked((mx, my)):
                    val = dice_of_current_player.roll()
                    self.last_roll = val
                    self.msg = f"Người {current+1} gieo được {val}"
                    self.gm.dice_value = val
                    self.highlight_cells.clear()

                    movable_pieces = self.gm.get_movable_pieces(current, val)

                    if movable_pieces:
                        self.msg += " → Chọn quân để di chuyển"
                        for piece in movable_pieces:
                            dest_cell = self.gm.get_destination_cell(piece, val)
                            if dest_cell:
                                self.highlight_cells.append(dest_cell)
                    else:
                        self.msg += ". Không có quân nào có thể đi."
                        if val != 6:
                            self.gm.next_turn()
                        else:
                            self.gm.dice_value = None
                    return

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
                        else:
                            self.msg = base_msg
                        
                        self.highlight_cells.clear()
                        return

    # ==========================================================
    #  VẼ TOÀN BỘ
    # ==========================================================
    def draw(self):
        self.draw_board_layout()
        self.draw_path()
        self.draw_highlight()

        # --- Vẽ quân cờ ---
        # Tọa độ offset cho các vị trí trong chuồng, giống trong draw_board_layout
        home_offsets = [(1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5)]

        for pid in range(self.gm.num_players):
            pieces_of_player = self.gm.players[pid]
            player_color = PLAYER_COLORS[pid]

            for piece in pieces_of_player:
                if piece.finished:
                    continue  # Bỏ qua các quân đã về đích

                px, py = 0, 0 # Khởi tạo tọa độ pixel

                if piece.path_index == -1:
                    # TRƯỜNG HỢP 1: Quân cờ đang ở trong chuồng
                    ox, oy = home_offsets[pid]
                    # Giả định piece có thuộc tính .id (từ 0 đến 3)
                    px = int(self.start_x + (ox + (piece.id % 2) * 2) * CELL)
                    py = int(self.start_y + (oy + (piece.id // 2) * 2) * CELL)
                else:
                    # TRƯỜNG HỢP 2: Quân cờ đang ở trên đường đi
                    path = self.gm.board.get_path_for_player(pid)
                    if piece.path_index < len(path):
                        gx, gy = path[piece.path_index]
                        # Tính tọa độ tâm của ô cờ để vẽ hình tròn
                        px = self.start_x + gx * CELL + CELL // 2
                        py = self.start_y + gy * CELL + CELL // 2
                    else:
                        continue # Safeguard, bỏ qua nếu path_index không hợp lệ

                # Bây giờ tiến hành vẽ quân cờ với tọa độ đã tính toán
                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)

                # (Tùy chọn) Vẽ số thứ tự lên quân cờ cho dễ phân biệt
                id_font = pygame.font.Font(None, 24)
                id_text = id_font.render(str(piece.id + 1), True, WHITE)
                text_rect = id_text.get_rect(center=(px, py))
                self.screen.blit(id_text, text_rect)


        # --- Vẽ các thành phần khác ---
        # Xúc xắc
        for i, dice in enumerate(self.dices):
            dice.active = (i == self.gm.turn)
            dice.draw(self.screen)

        # Thông báo trạng thái
        msg_render = FONT.render(self.msg, True, BLACK)
        self.screen.blit(msg_render, (20, HEIGHT - 40))

        pygame.display.flip()
        self.clock.tick(60)


    def update_dice_display(self, player_id, value):
        """Cập nhật giao diện của một viên xúc xắc cụ thể."""
        if 0 <= player_id < len(self.dices):
            self.dices[player_id].set_value(value)


    def draw_from_state(self, game_state):
        """Vẽ bàn cờ và quân cờ dựa trên dictionary game_state."""
        
        # --- Vẽ Layout Bàn Cờ và Đường Đi ---
        # Những phần này không đổi dựa trên game_state, nên gọi hàm cũ
        self.draw_board_layout()
        self.draw_path()
        # self.draw_highlight() # Logic highlight có thể cần phối hợp server sau

        # --- Vẽ Quân Cờ dựa trên game_state ---
        players_pieces_data = game_state.get('players_pieces', [])
        home_offsets = [(1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5)] # Giữ logic này

        for pid, pieces_data in enumerate(players_pieces_data):
            player_color = PLAYER_COLORS[pid]
            for piece_data in pieces_data:
                path_index = piece_data.get('path_index', -1)
                is_finished = piece_data.get('finished', False)
                piece_id = piece_data.get('id', -1) # Lấy ID quân cờ

                if is_finished:
                    continue # Bỏ qua quân đã về đích

                px, py = 0, 0
                if path_index == -1:
                    # Quân cờ trong chuồng
                    if pid < len(home_offsets): # Kiểm tra an toàn
                        ox, oy = home_offsets[pid]
                        if piece_id != -1: # Đảm bảo ID hợp lệ
                            px = int(self.start_x + (ox + (piece_id % 2) * 2) * CELL)
                            py = int(self.start_y + (oy + (piece_id // 2) * 2) * CELL)
                        else: continue # Bỏ qua nếu ID không hợp lệ
                else:
                    # Quân cờ trên đường đi hoặc đường về đích
                    # Chúng ta cần logic của Board, truy cập qua GameManager nếu có
                    # Hoặc, tốt hơn, server gửi thẳng tọa độ pixel
                    # Hiện tại, giả sử có thể lấy path từ một instance board cục bộ
                    # PHẦN NÀY KHÁ PHỨC TẠP nếu không tái cấu trúc nhiều hơn.
                    # Có thể cần một board cục bộ tạm thời, hoặc server gửi tọa độ.
                    # Thử lấy path từ instance board dùng chung/tạm:
                    if self.gm and self.gm.board: # Kiểm tra gm và board có tồn tại
                       path = self.gm.board.get_path_for_player(pid)
                       if path_index < len(path):
                           gx, gy = path[path_index]
                           px = self.start_x + gx * CELL + CELL // 2
                           py = self.start_y + gy * CELL + CELL // 2
                       else: continue # path_index không hợp lệ
                    else: continue # Không thể xác định vị trí

                # Vẽ quân cờ
                pygame.draw.circle(self.screen, player_color, (px, py), 18)
                pygame.draw.circle(self.screen, BLACK, (px, py), 18, 2)
                # Tùy chọn: Vẽ ID quân cờ
                if piece_id != -1:
                    id_font = pygame.font.Font(None, 24)
                    id_text = id_font.render(str(piece_id + 1), True, WHITE)
                    text_rect = id_text.get_rect(center=(px, py))
                    self.screen.blit(id_text, text_rect)

        # --- Vẽ Xúc Xắc dựa trên game_state ---
        dice_val = game_state.get('dice_value')
        current_turn = game_state.get('turn', -1)

        for i, dice in enumerate(self.dices):
            dice.active = (i == current_turn) # Highlight xúc xắc đúng
            if i == current_turn and dice_val is not None:
                dice.set_value(dice_val) # Đặt giá trị từ server
            elif not dice.active:
                 dice.set_value(1) # Reset xúc xắc không hoạt động (tùy chọn)

            dice.draw(self.screen) # Vẽ xúc xắc

        # --- Vẽ Thông Báo Trạng Thái ---
        # Thông báo giờ được xử lý chính bởi vòng lặp client
        # msg_render = FONT.render(self.msg, True, BLACK)
        # self.screen.blit(msg_render, (20, HEIGHT - 40))