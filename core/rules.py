SAFE_CELLS = [
    (1, 6),
    (8, 1),
    (13, 8),
    (6, 13)
]

# --- HÀM CŨ NẰM TRONG core/rules.py ---
def check_and_kick_opponent(moving_piece, all_players_pieces, board, player_board_map):
    """
    Kiểm tra và đá quân đối thủ nếu nó đang đứng trên ô đích.
    SỬA: Sử dụng player_board_map để ánh xạ vị trí đúng trong chế độ 2 người.
    """

    moving_player_slot_id = moving_piece.player_id
    # Lấy Board ID thực tế của quân đang di chuyển (ví dụ: 0 hoặc 2)
    moving_player_board_id = player_board_map.get(moving_player_slot_id, moving_player_slot_id)

    # 1. Lấy ô đích (sử dụng Board ID)
    full_path = board.get_path_for_player(moving_player_board_id) # SỬA: Dùng Board ID
    destination_cell = full_path[moving_piece.path_index]

    # 2. Ô an toàn cố định -> không bị đá
    if destination_cell in SAFE_CELLS:
        return None
    
    # --- BỔ SUNG LOGIC KHÔNG CHO CHỒNG QUÂN VÀ CHỈ ĐÁ MỘT QUÂN ---
    # Logic Ludo chuẩn: Một ô chỉ có thể chứa 1 quân đối phương.
    # Nếu đã có quân mình, quân đối phương không thể vào.
    
    # Kiểm tra số lượng quân mình tại ô đích (Nếu > 0, không được đá)
    # Tuy nhiên, trong logic của bạn, quân cờ của bạn luôn di chuyển thành công trước khi đá.
    # Ta chỉ cần kiểm tra quân đối thủ.
    
    # 3. Kiểm tra tất cả quân đối thủ
    for opponent_pid_slot, opponent_pieces in enumerate(all_players_pieces):

        if opponent_pid_slot == moving_piece.player_id:
            continue  # không đá quân mình

        # Lấy Board ID thực tế của đối thủ (ví dụ: 2 hoặc 0)
        opponent_board_id = player_board_map.get(opponent_pid_slot, opponent_pid_slot) 
        
        # Đếm số lượng quân đối thủ đang đứng tại ô đích
        opponents_on_destination = []
        
        for opponent_piece in opponent_pieces:

            if opponent_piece.path_index < 0 or opponent_piece.finished:
                continue

            # Lấy đường đi đối thủ (sử dụng Board ID của đối thủ)
            opponent_path = board.get_path_for_player(opponent_board_id) # SỬA: Dùng Board ID đối thủ
            
            # Kiểm tra an toàn: Quân đã vào đường về đích không bị đá
            # Giả định đường về đích bắt đầu sau 51 ô trên đường chính.
            if opponent_piece.path_index > len(board.path_grid) - 1:
                 continue
                 
            opponent_cell = opponent_path[opponent_piece.path_index]

            # 4. Nếu trùng ô
            if opponent_cell == destination_cell:
                opponents_on_destination.append(opponent_piece)
        
        # --- BỔ SUNG QUY TẮC CHỒNG QUÂN (Stacking Rule) ---
        
        # Nếu quân đối thủ >= 2 quân đang đứng cùng ô -> Ô đó an toàn (Không đá được)
        if len(opponents_on_destination) >= 2:
             # Đây là một "tháp" quân, không thể bị đá
             return None 
        
        # Nếu có 1 quân đối thủ đứng ở đó -> Đá quân đó
        if len(opponents_on_destination) == 1:
            kicked_piece = opponents_on_destination[0]
            
            # Reset quân bị đá về chuồng
            kicked_piece.path_index = -1
            kicked_piece.finished = False

            return kicked_piece

    # 5. Không có quân nào bị đá
    return None