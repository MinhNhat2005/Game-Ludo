import logging
from core.piece import Piece
from core.board import Board
from . import rules
from ai.random_bot import RandomBot
from ai.hard_bot import HardBot
from utils.constants import WIDTH, HEIGHT, CELL
import random
import datetime 
from utils import firebase_manager 

class GameManager:
    def __init__(self, num_players=4, player_types=None, match_id_to_load=None, is_online=False):
        
        # 1. Khởi tạo Firebase
        firebase_manager.initialize_firebase()
        
        self.board = Board(start_x=(WIDTH - CELL*15)//2, start_y=(HEIGHT - CELL*15)//2)
        
        # 2. Thuộc tính lưu/tải (Khởi tạo map ở đây để tránh lỗi Attribute Error)
        self.match_id = match_id_to_load
        self.start_time = datetime.datetime.now()
        self.is_online = is_online
        self.player_map = {} 
        self.active_pids = []
        
        # 3. Logic Khởi tạo / Tải
        if match_id_to_load is not None:
            self.is_loaded_successfully = self._load_game(match_id_to_load)
            if not self.is_loaded_successfully:
                logging.error(f"Không thể tải game MatchID {match_id_to_load}. Bắt đầu game mới.")
                self.setup_game(num_players, player_types)
        else:
            self.setup_game(num_players, player_types)
            
        self.last_move_info = None

    def setup_game(self, num_players, player_types):
        self.num_players = num_players
        self.player_types = player_types or ['human'] * num_players
        self.turn = 0
        self.dice_value = None
        self.winner = None
        
        # --- LOGIC KHỞI TẠO MAP VỊ TRÍ (ĐÃ SỬA VÀ ĐỒNG BỘ) ---
        if num_players == 2:
            self.active_pids = [0, 1] 
            self.player_map = {0: 0, 1: 1} # CHẾ ĐỘ CẠNH NHAU
        elif num_players == 3:
            self.active_pids = [0, 1, 2] 
            self.player_map = {0: 0, 1: 1, 2: 2}
        else:
            self.active_pids = [0, 1, 2, 3] 
            self.player_map = {i: i for i in range(4)}
        
        # --------------------------------------------------------
        
        self.players = self._init_players() # Gọi hàm khởi tạo quân cờ đã sửa
        self.bots = self._init_bots()
        self.match_id = None

    def _init_players(self):
        """Khởi tạo quân cờ sử dụng BOARD ID thực tế."""
        players = []
        
        for slot_id in range(self.num_players):
            # LẤY BOARD ID THỰC TẾ (0 hoặc 1) TỪ MAP
            board_id = self.player_map.get(slot_id, slot_id)
            
            # QUAN TRỌNG: Khởi tạo quân cờ với BOARD ID thực tế
            pieces = [Piece(board_id, piece_id) for piece_id in range(4)]
            
            # Lưu trữ quân cờ theo Slot ID tuần tự (0, 1) trong self.players
            players.append(pieces)
            
        return players

    def _init_bots(self):
        bots = {}
        for pid, ptype in enumerate(self.player_types):
            if ptype == 'bot_easy':
                logging.info(f"Khởi tạo Bot Dễ cho Người chơi {pid + 1}")
                bots[pid] = RandomBot(pid, self) 
            elif ptype == 'bot_hard':
                logging.info(f"Khởi tạo Bot Khó cho Người chơi {pid + 1}")
                bots[pid] = HardBot(pid, self)
        return bots
    
    def is_bot_turn(self):
        return self.turn in self.bots

    # --- HÀM LƯU/TẢI GIỮ NGUYÊN (Cần sửa logic trong _apply_loaded_state) ---
    def save_current_state(self):
        firebase_manager.save_game_state(self, is_loadable=True)

    def finish_game(self, winner_id):
        firebase_manager.save_game_state(self, winner_id=winner_id, is_loadable=False)
        self.match_id = None 

    def _load_game(self, match_id):
        loaded_data = firebase_manager.load_game_state(match_id)
        if loaded_data:
            return self._apply_loaded_state(loaded_data)
        return False
        
    def _apply_loaded_state(self, loaded_data):
        # ... (Tạm thời bỏ qua phần tải game vì nó phức tạp và không liên quan trực tiếp 
        # đến lỗi hiển thị hiện tại. Tuy nhiên, nó cần được sửa sau này.)
        try:
            self.num_players = loaded_data['num_players']
            self.turn = loaded_data['turn']
            self.dice_value = loaded_data['dice_value']
            self.winner = None
            
            self.setup_game(self.num_players, self.player_types) # Thiết lập lại map và types

            loaded_mode = loaded_data.get('mode', 'Offline')
            if loaded_mode == 'Bot':
                bot_count = self.num_players - 1
                self.player_types = ['human'] + ['bot_easy'] * bot_count 
            else: 
                self.player_types = ['human'] * self.num_players
            
            self.players = []
            saved_pieces_state = loaded_data['pieces_state']
            if len(saved_pieces_state) != self.num_players:
                logging.error("Lỗi state quân cờ: sai số lượng người chơi.")
                return False

            for slot_id in range(self.num_players):
                player_pieces_list = []
                for piece_data in saved_pieces_state[slot_id]:
                    # Giả định dữ liệu tải về đã lưu Board ID
                    board_id = self.player_map.get(slot_id, slot_id)
                    p = Piece(board_id, piece_data['id']) 
                    p.path_index = piece_data['path_index']
                    p.finished = piece_data['finished']
                    player_pieces_list.append(p)
                self.players.append(player_pieces_list)
            
            self.bots = self._init_bots()
            
            logging.info(f"Đã khôi phục game thành công. Lượt của P{self.turn + 1}.")
            return True 
            
        except Exception as e:
            logging.exception(f"Lỗi nghiêm trọng khi áp dụng trạng thái đã tải: {e}")
            return False 

    def run_bot_turn(self):
        dice_roll = random.randint(1, 6)
        self.dice_value = dice_roll
        
        bot = self.bots[self.turn]
        piece_to_move = bot.choose_move()
        
        if piece_to_move:
            kicked_piece_obj, just_finished, game_won = self.move_piece(piece_to_move) 
            
            kick_msg = f"Đã đá quân P{kicked_piece_obj.player_id + 1}!" if kicked_piece_obj else None
            
            return ("đã di chuyển", kick_msg, dice_roll, just_finished, game_won)
        else:
            self.last_move_info = {
                "player_id": self.turn,
                "dice": self.dice_value,
                "piece_id": None,
                "action": "cannot move"
            }
            if self.dice_value != 6:
                self.next_turn()
            return ("không thể đi", None, self.dice_value, False, False)

    def next_turn(self):
        self.turn = (self.turn + 1) % self.num_players
        self.dice_value = None

    def _check_for_winner(self, player_id):
        if not (0 <= player_id < len(self.players)):
            return False
        for piece in self.players[player_id]:
            if not piece.finished:
                return False
        self.winner = player_id
        logging.info(f"Người chơi {player_id + 1} đã chiến thắng!")
        self.finish_game(player_id)
        return True

    def get_movable_pieces(self, player_id, dice_value):
        movable = []
        
        # SỬA: Dùng Board ID thực tế để lấy path_len
        player_board_id = self.player_map.get(player_id, player_id) 
        path_len = len(self.board.get_path_for_player(player_board_id)) 
        last_cell_index = path_len - 1

        for piece in self.players[player_id]:
            if piece.finished:
                continue
            
            if piece.path_index == -1 and dice_value == 6:
                movable.append(piece)
            
            elif piece.path_index >= 0:
                destination_index = piece.path_index + dice_value
                if destination_index <= last_cell_index:
                    movable.append(piece)
        return movable

    # --- SỬA LỖI TRỌNG TÂM TRONG MOVE_PIECE (KHẮC PHỤC ÁNH XẠ ĐƯỜNG ĐI) ---
    def move_piece(self, piece_to_move):
        if self.dice_value is None or self.dice_value == -1:
            logging.warning("Move_piece được gọi khi dice_value là None/GameOver")
            return (None, False, False)

        dice_rolled = self.dice_value
        
        # 1. LẤY BOARD ID THỰC TẾ (Board ID: 0 hoặc 1)
        player_board_id = self.player_map.get(piece_to_move.player_id, piece_to_move.player_id)
        
        # 2. Dùng Board ID THỰC TẾ để tính chiều dài đường đi
        path_len = len(self.board.get_path_for_player(player_board_id))
        
        was_finished = piece_to_move.finished
        old_index = piece_to_move.path_index 

        # 3. Thực hiện di chuyển với path_len ĐÚNG
        piece_to_move.move(dice_rolled, path_len) 

        new_index = piece_to_move.path_index 
        just_finished_this_move = (not was_finished and piece_to_move.finished)

        # 4. Truyền map vào hàm đá quân (giữ nguyên logic đã sửa)
        kicked_piece_obj = rules.check_and_kick_opponent(
            moving_piece=piece_to_move,
            all_players_pieces=self.players,
            board=self.board,
            player_board_map=self.player_map
        )

        self.last_move_info = {
            "player_id": piece_to_move.player_id,
            "dice": dice_rolled,
            "piece_id": piece_to_move.id,
            "from_index": old_index,
            "to_index": new_index,
            "action": "moved" if old_index >= 0 else "spawned",
            "kicked_piece": {"player_id": kicked_piece_obj.player_id} if kicked_piece_obj else None, 
            "finished": piece_to_move.finished
        }

        game_has_winner = False
        winner_id = None

        if just_finished_this_move:
            game_has_winner = self._check_for_winner(piece_to_move.player_id)
            if game_has_winner:
                winner_id = piece_to_move.player_id  # <-- Lưu đúng ID người thắng

        # Các điều kiện cho lượt tiếp theo
        if game_has_winner:
            self.dice_value = -1
        elif dice_rolled == 6 or kicked_piece_obj is not None or just_finished_this_move:
            self.dice_value = None
        else:
            self.next_turn()

        return (kicked_piece_obj, just_finished_this_move, winner_id)



    def get_destination_cell(self, piece, dice_value):
        
        # SỬA: Lấy Board ID thực tế của quân cờ
        player_board_id = self.player_map.get(piece.player_id, piece.player_id) 
        
        if piece.path_index == -1 and dice_value == 6:
            return self.board.get_spawn_cell(player_board_id) # SỬA: Dùng Board ID
            
        if piece.path_index >= 0:
            path = self.board.get_path_for_player(player_board_id) # SỬA: Dùng Board ID
            next_index = piece.path_index + dice_value
            if next_index < len(path):
                return path[next_index]
        return None

    def find_piece_for_move(self, player_id, destination_cell):
        """Tìm quân cờ có thể di chuyển đến ô đích."""
        movable_pieces_list = self.get_movable_pieces(player_id, self.dice_value)
        for piece in movable_pieces_list:
            dest = self.get_destination_cell(piece, self.dice_value)
            if dest == destination_cell:
                return piece
        return None

    def find_piece_by_id(self, player_id, piece_id):
        if 0 <= player_id < len(self.players):
            player_pieces = self.players[player_id]
            for piece in player_pieces:
                if piece.id == piece_id:
                    return piece
        return None

    def get_current_bot(self):
        return self.bots.get(self.turn, None)