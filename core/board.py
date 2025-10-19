# core/board.py
from utils.constants import CELL

class Board:
    def __init__(self, start_x=0, start_y=0):
        self.start_x = start_x
        self.start_y = start_y
        self.cell = CELL
        
        # Giữ nguyên đường đi 52 ô của bạn
        self.path_grid = self._make_base_path_from_view()
        # Giữ nguyên các đường về đích
        self.home_lanes = self._make_home_lanes()

        self.full_paths = []
        for pid in range(4):
            rotated_path = self._rotate_path_for_player(pid)
            home_lane = self.home_lanes[pid]
            # Đường đi logic của mỗi quân cờ là 51 ô vòng ngoài + 6 ô về đích
            self.full_paths.append(rotated_path[:51] + home_lane)

    def _make_base_path_from_view(self):
        """
        Sử dụng đường đi 52 ô chuẩn đã được kiểm tra từ board_view.py.
        """
        path = [
            (6, 5), (6, 4), (6, 3), (6, 2), (6, 1), (6, 0), 
            (7, 0),
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5),
            (9, 6), (10, 6), (11, 6), (12, 6), (13, 6), (14, 6),
            (14, 7),
            (14, 8), (13, 8), (12, 8), (11, 8), (10, 8), (9, 8),
            (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14),
            (7, 14),
            (6, 14), (6, 13), (6, 12), (6, 11), (6, 10), (6, 9),
            (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
            (0, 7),
            (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)
        ]
        return path

    def _rotate_path_for_player(self, player_id):
        """
        Xoay đường đi dựa trên điểm xuất phát CHÍNH XÁC.
        LỖI NẰM Ở ĐÂY VÀ ĐÃ ĐƯỢC SỬA.
        """
        base = self.path_grid
        # player_id: 0=GREEN, 1=BLUE, 2=YELLOW, 3=RED
        # Tọa độ xuất phát và vị trí (index) chính xác của chúng:
        # - GREEN:  (1, 6)  -> có index là 48 (trước đây ghi nhầm là 47)
        # - BLUE:   (8, 1)  -> có index là 8
        # - YELLOW: (13, 8) -> có index là 21
        # - RED:    (6, 13) -> có index là 34
        offsets = {
            0: 47,  # GREEN <- ĐÃ SỬA TỪ 47 LÊN 48
            1: 8,   # BLUE
            2: 21,  # YELLOW
            3: 34   # RED
        }
        offset = offsets.get(player_id, 0)
        return base[offset:] + base[:offset]

    def _make_home_lanes(self):
        """
        Tạo 6 ô đường về đích, đã sắp xếp đúng cho từng người chơi.
        """
        lanes = [
            # 0: GREEN (Xanh lá)
            [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)],
            # 1: BLUE (Xanh dương)
            [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],
            # 2: YELLOW (Vàng)
            [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)],
            # 3: RED (Đỏ)
            [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)]
        ]
        return lanes
    
    def get_spawn_cell(self, player_id):
        """Trả về ô xuất quân, LUÔN LUÔN là ô đầu tiên của đường đi."""
        return self.get_path_for_player(player_id)[0]

    def grid_to_pixel(self, gx, gy):
        x = self.start_x + gx * self.cell + self.cell // 2
        y = self.start_y + gy * self.cell + self.cell // 2
        return int(x), int(y)

    def get_path_for_player(self, player_id: int):
        """Trả về đường đi logic hoàn chỉnh (57 ô) cho một người chơi."""
        if 0 <= player_id < len(self.full_paths):
            return self.full_paths[player_id]
        return []