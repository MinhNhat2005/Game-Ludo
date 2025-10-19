# core/rules.py

# === CÁC Ô AN TOÀN (Ô XUẤT PHÁT) ===
# Quân cờ đứng trên các ô này sẽ không bị đá.
# Dữ liệu được lấy từ file board_view.py đã được xác nhận của bạn.
SAFE_CELLS = [
    (1, 6),   # 0: GREEN's spawn
    (8, 1),   # 1: BLUE's spawn
    (13, 8),  # 2: YELLOW's spawn
    (6, 13)   # 3: RED's spawn
]

def check_and_kick_opponent(moving_piece, all_players_pieces, board):
    """
    Kiểm tra và thực hiện đá quân nếu có thể.
    - moving_piece: Quân cờ vừa thực hiện nước đi.
    - all_players_pieces: Danh sách tất cả quân cờ trong game (ví dụ: self.gm.players).
    - board: Đối tượng Board để lấy tọa độ.

    Trả về: Một chuỗi thông báo nếu có quân bị đá, ngược lại trả về None.
    """
    # 1. Lấy tọa độ ô đích của quân cờ vừa di chuyển
    full_path = board.get_path_for_player(moving_piece.player_id)
    destination_cell = full_path[moving_piece.path_index]

    # 2. Nếu ô đích là ô an toàn, không thực hiện đá
    if destination_cell in SAFE_CELLS:
        return None

    # 3. Lặp qua tất cả quân cờ của các đối thủ
    for opponent_pid, opponent_pieces in enumerate(all_players_pieces):
        # Bỏ qua, không tự đá quân của mình
        if opponent_pid == moving_piece.player_id:
            continue

        for opponent_piece in opponent_pieces:
            # Bỏ qua các quân đang ở trong chuồng hoặc đã về đích
            if opponent_piece.path_index < 0 or opponent_piece.finished:
                continue

            # Lấy tọa độ của quân cờ đối thủ
            opponent_path = board.get_path_for_player(opponent_pid)
            opponent_cell = opponent_path[opponent_piece.path_index]

            # 4. Nếu tìm thấy quân đối thủ trên ô đích -> Thực hiện đá
            if opponent_cell == destination_cell:
                # Reset trạng thái của quân bị đá
                opponent_piece.path_index = -1 
                
                # Trả về thông báo để hiển thị
                msg = f"  bada' Nguoi` {opponent_pid + 1}!"
                return msg

    # 5. Nếu không có quân nào bị đá
    return None