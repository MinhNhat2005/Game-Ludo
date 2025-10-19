# network/protocol.py

# --- Các Loại Thông Điệp (Message Types) ---
# Client -> Server
MSG_TYPE_ROLL_DICE = "roll_dice"
MSG_TYPE_MOVE_PIECE = "move_piece"
MSG_TYPE_JOIN_GAME = "join_game" # (Có thể thêm sau)

# Server -> Client
MSG_TYPE_YOUR_ID = "your_id"
MSG_TYPE_GAME_STATE = "game_state"
MSG_TYPE_YOUR_TURN = "your_turn"
MSG_TYPE_MOVE_INVALID = "move_invalid"
MSG_TYPE_GAME_OVER = "game_over"
MSG_TYPE_PLAYER_JOINED = "player_joined"
MSG_TYPE_PLAYER_LEFT = "player_left"
MSG_TYPE_ERROR = "error"


# --- Cấu trúc dữ liệu mẫu (sử dụng JSON) ---

# Client -> Server: Yêu cầu gieo xúc xắc
# { "type": MSG_TYPE_ROLL_DICE }

# Client -> Server: Yêu cầu di chuyển quân
# { "type": MSG_TYPE_MOVE_PIECE, "payload": { "piece_id": 2 } }

# Server -> Client: Gửi ID cho người chơi mới
# { "type": MSG_TYPE_YOUR_ID, "payload": { "player_id": 1 } }

# Server -> Client: Gửi trạng thái game đầy đủ
# {
#   "type": MSG_TYPE_GAME_STATE,
#   "payload": {
#     "num_players": 4,
#     "turn": 0,
#     "dice_value": 5,
#     "players_pieces": [
#       [ {"id": 0, "path_index": 10, "finished": false}, ... ], # Player 0 pieces
#       [ {"id": 0, "path_index": -1, "finished": false}, ... ], # Player 1 pieces
#       ...
#     ]
#     # Thêm thông tin khác nếu cần, ví dụ: last_action_msg
#   }
# }

# Server -> Client: Thông báo đến lượt
# { "type": MSG_TYPE_YOUR_TURN }

# Server -> Client: Thông báo nước đi không hợp lệ
# { "type": MSG_TYPE_MOVE_INVALID, "payload": { "reason": "Không phải lượt của bạn" } }

# Server -> Client: Thông báo game kết thúc
# { "type": MSG_TYPE_GAME_OVER, "payload": { "winner_id": 0 } }

# Server -> Client: Thông báo lỗi chung
# { "type": MSG_TYPE_ERROR, "payload": { "message": "Phòng đã đầy" } }