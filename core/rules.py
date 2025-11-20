SAFE_CELLS = [
    (1, 6),
    (8, 1),
    (13, 8),
    (6, 13)
]

def check_and_kick_opponent(moving_piece, all_players_pieces, board):
    """
    Kiểm tra và đá quân đối thủ nếu nó đang đứng trên ô đích.
    Trả về: OBJECT Piece bị đá, hoặc None.
    """

    # 1. Lấy ô đích
    full_path = board.get_path_for_player(moving_piece.player_id)
    destination_cell = full_path[moving_piece.path_index]

    # 2. Ô an toàn -> không bị đá
    if destination_cell in SAFE_CELLS:
        return None

    # 3. Kiểm tra tất cả quân đối thủ
    for opponent_pid, opponent_pieces in enumerate(all_players_pieces):

        if opponent_pid == moving_piece.player_id:
            continue  # không đá quân mình

        for opponent_piece in opponent_pieces:

            if opponent_piece.path_index < 0 or opponent_piece.finished:
                continue

            opponent_path = board.get_path_for_player(opponent_pid)
            opponent_cell = opponent_path[opponent_piece.path_index]

            # 4. Nếu trùng ô -> đá
            if opponent_cell == destination_cell:

                # Reset quân bị đá về chuồng
                opponent_piece.path_index = -1
                opponent_piece.finished = False

                # ❗❗ TRẢ VỀ OBJECT quân bị đá, không phải string
                return opponent_piece

    # 5. Không có quân nào bị đá
    return None
