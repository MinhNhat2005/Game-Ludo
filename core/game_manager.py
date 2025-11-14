# core/game_manager.py
import logging
import random
import json
from utils.database_manager import GameLogger, load_game_state
from core.piece import Piece
from core.board import Board
from . import rules
# Import Bot một cách an toàn
try:
    from ai.random_bot import RandomBot 
    from ai.hard_bot import HardBot
    BOTS_ENABLED = True
except ImportError:
    logging.warning("Không tìm thấy file Bot (random_bot.py, hard_bot.py). Chế độ Bot sẽ không hoạt động.")
    BOTS_ENABLED = False
    
from utils.constants import WIDTH, HEIGHT, CELL

class GameManager:
    def __init__(self, num_players=4, player_types=None, match_id_to_load=None):
        self.num_players = num_players
        self.turn = 0
        self.dice_value = None
        self.winner = None
        self.board = Board(start_x=(WIDTH - CELL*15)//2, start_y=(HEIGHT - CELL*15)//2)
        
        self.player_types = player_types or ['human'] * num_players
        self.players = []
        self.bots = {}
        self.logger = None

        if match_id_to_load:
            logging.info(f"Đang tải trạng thái game từ MatchID: {match_id_to_load}")
            loaded_data = load_game_state(match_id_to_load)
            
            # --- SỬA LỖI LOGIC TẢI ---
            # 1. Kiểm tra xem tải có thành công KHÔNG
            if loaded_data and self._apply_loaded_state(loaded_data):
                # 2. Tải thành công: Khởi tạo logger với ID cũ
                self.logger = GameLogger(mode=loaded_data['mode'], num_players=loaded_data['num_players'], match_id_to_load=match_id_to_load)
                logging.info(f"Đã tải thành công GameLogger cho MatchID: {match_id_to_load}")
            else:
                # 3. Tải thất bại: Tạo game mới
                logging.error(f"Không thể tải MatchID: {match_id_to_load}. Tạo game mới thay thế.")
                self._initialize_new_game(num_players, player_types)
            # ---------------------------
        else:
            # --- TẠO GAME MỚI ---
            self._initialize_new_game(num_players, player_types)

    def _initialize_new_game(self, num_players, player_types):
        """Hàm helper để tạo một game mới."""
        self.num_players = num_players
        self.player_types = player_types or ['human'] * num_players
        self.players = self._init_players()
        self.bots = self._init_bots()
        self.turn = 0 
        self.dice_value = None
        self.winner = None
        mode = "Bot" if any(pt.startswith('bot') for pt in self.player_types) else "Offline"
        self.logger = GameLogger(mode=mode, num_players=self.num_players)
        logging.info("GameManager đã khởi tạo game MỚI.")

    def _apply_loaded_state(self, loaded_data):
        """
        Áp dụng trạng thái đã tải vào GameManager.
        Trả về True nếu thành công, False nếu thất bại.
        """
        try:
            logging.debug("Bắt đầu áp dụng state đã tải: %s", loaded_data)
            self.num_players = loaded_data['num_players']
            self.turn = loaded_data['turn']
            self.dice_value = loaded_data['dice_value']
            self.winner = None
            
            # --- KHÔI PHỤC player_types (ĐÃ SỬA) ---
            loaded_mode = loaded_data.get('mode', 'Offline')
            if loaded_mode == 'Bot':
                 # Giả định P1 là human, các P còn lại là bot
                 bot_count = self.num_players - 1
                 # (Đây là giả định, logic lưu/tải player_types chính xác sẽ phức tạp hơn)
                 self.player_types = ['human'] + ['bot_easy'] * bot_count 
            else: # Offline
                 self.player_types = ['human'] * self.num_players
            logging.debug("Đã khôi phục player_types: %s", self.player_types)
            # ------------------------------------
            
            # --- Khôi phục quân cờ ---
            self.players = []
            saved_pieces_state = loaded_data['pieces_state']
            if not isinstance(saved_pieces_state, list) or len(saved_pieces_state) != self.num_players:
                 logging.error("Lỗi state quân cờ: không phải list hoặc sai số lượng người chơi.")
                 return False # Báo tải thất bại

            logging.debug("Bắt đầu khôi phục quân cờ...")
            for pid in range(self.num_players):
                player_pieces_list = []
                if not (pid < len(saved_pieces_state) and isinstance(saved_pieces_state[pid], list)):
                     logging.error(f"Lỗi state quân cờ cho P{pid}: không phải list.")
                     return False # Báo tải thất bại
                     
                for piece_data in saved_pieces_state[pid]:
                    p = Piece(piece_data['player_id'], piece_data['id'])
                    p.path_index = piece_data['path_index']
                    p.finished = piece_data['finished']
                    player_pieces_list.append(p)
                self.players.append(player_pieces_list)
            
            # Khôi phục bots
            self.bots = self._init_bots()
            
            logging.info(f"Đã khôi phục game thành công. Lượt của P{self.turn + 1}.")
            return True # BÁO TẢI THÀNH CÔNG
            
        except Exception as e:
            logging.exception(f"Lỗi nghiêm trọng khi áp dụng trạng thái đã tải: {e}")
            return False # BÁO TẢI THẤT BẠI

    def _serialize_pieces(self):
        """Chuyển đổi self.players thành list các dict có thể lưu JSON."""
        serializable_pieces = []
        for player_pieces in self.players:
            pieces_data = []
            for p in player_pieces:
                pieces_data.append({
                    'id': p.id, 
                    'player_id': p.player_id, 
                    'path_index': p.path_index, 
                    'finished': p.finished
                })
            serializable_pieces.append(pieces_data)
        return serializable_pieces

    def save_game_on_quit(self):
        """Lưu trạng thái game hiện tại vào CSDL khi thoát."""
        if not self.logger or not self.logger.conn: # Kiểm tra logger và kết nối CSDL
            logging.error("Không thể lưu game: Logger chưa được khởi tạo hoặc đã đóng.")
            return
            
        if self.winner is None and self.dice_value != -1: # Chỉ lưu game đang dở
            try:
                pieces_state = self._serialize_pieces()
                dice_to_save = self.dice_value 
                self.logger.save_game_state(self.turn, dice_to_save, pieces_state)
            except Exception as e:
                logging.exception(f"Lỗi khi lưu game: {e}")
        else:
             logging.info("Game đã kết thúc, không cần lưu.")
        
        self.logger.close() # Luôn đóng logger khi thoát

    def _init_players(self):
        players = []
        for pid in range(self.num_players):
            pieces = [Piece(pid, piece_id) for piece_id in range(4)]
            players.append(pieces)
        return players
        
    def _init_bots(self):
        bots = {}
        if not BOTS_ENABLED: return bots
        
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

    def run_bot_turn(self):
        if not self.is_bot_turn() or not BOTS_ENABLED:
            return (None, None, None, False, False)
        bot = self.bots.get(self.turn)
        if not bot: 
             logging.error(f"Lỗi: Đến lượt P{self.turn+1} (Bot) nhưng không tìm thấy đối tượng Bot.")
             self.next_turn()
             return ("Lỗi Bot", None, self.dice_value, False, False)

        piece_to_move = bot.choose_move()
        dice_value_rolled = self.dice_value
        
        if self.logger: self.logger.log_action(self.turn, "roll", f"Gieo được: {dice_value_rolled}")

        if piece_to_move:
            (kick_msg, just_finished, game_won) = self.move_piece(piece_to_move)
            base_msg = "đã di chuyển."
            return (base_msg, kick_msg, dice_value_rolled, just_finished, game_won)
        else:
            base_msg = "không thể đi."
            if self.dice_value != 6: self.next_turn()
            else: self.dice_value = None
            if self.logger: self.logger.log_action(self.turn, "no_move", f"Gieo {dice_value_rolled}, không đi được.")
            return (base_msg, None, dice_value_rolled, False, False)

    def next_turn(self):
        self.turn = (self.turn + 1) % self.num_players; self.dice_value = None

    def _check_for_winner(self, player_id):
        if not (0 <= player_id < len(self.players)): return False
        for piece in self.players[player_id]:
            if not piece.finished: return False
        self.winner = player_id
        logging.info(f"Người chơi {player_id + 1} đã chiến thắng!")
        return True

    def get_movable_pieces(self, player_id, dice_value):
        movable = []; path_len = len(self.board.get_path_for_player(player_id)); last_cell_index = path_len - 1
        if not (0 <= player_id < len(self.players)): return [] 
        for piece in self.players[player_id]:
            if piece.finished: continue
            if piece.path_index == -1 and dice_value == 6: movable.append(piece)
            elif piece.path_index >= 0:
                if piece.path_index + dice_value <= last_cell_index: movable.append(piece)
        return movable

    def move_piece(self, piece_to_move):
        if self.dice_value is None or self.dice_value == -1: return (None, False, False)
        dice_rolled = self.dice_value; path_len = len(self.board.get_path_for_player(piece_to_move.player_id))
        was_finished = piece_to_move.finished
        
        move_type = "Ra quân" if piece_to_move.path_index == -1 else "Di chuyển"
        if self.logger: self.logger.log_action(self.turn, move_type, f"Quân {piece_to_move.id + 1}")
        
        piece_to_move.move(dice_rolled, path_len)
        
        just_finished_this_move = (not was_finished and piece_to_move.finished)
        kick_message = rules.check_and_kick_opponent(moving_piece=piece_to_move, all_players_pieces=self.players, board=self.board)
        
        game_has_winner = False
        if just_finished_this_move:
             game_has_winner = self._check_for_winner(piece_to_move.player_id)
             if self.logger:
                 if game_has_winner:
                     self.logger.log_action(self.turn, "win", f"Quân {piece_to_move.id + 1} về đích. THẮNG!")
                     self.logger.log_game_end(self.turn)
                 else: self.logger.log_action(self.turn, "done_piece", f"Quân {piece_to_move.id + 1} về đích.")

        if game_has_winner: self.dice_value = -1
        elif dice_rolled == 6 or kick_message is not None or just_finished_this_move:
            self.dice_value = None
            if kick_message and self.logger: self.logger.log_action(self.turn, "kick", kick_message.strip())
        else: self.next_turn()
        return (kick_message, just_finished_this_move, game_has_winner)

    def get_destination_cell(self, piece, dice_value):
        if piece.path_index == -1 and dice_value == 6: return self.board.get_spawn_cell(piece.player_id)
        if piece.path_index >= 0:
            path = self.board.get_path_for_player(piece.player_id); next_index = piece.path_index + dice_value
            if next_index < len(path): return path[next_index]
        return None

    def find_piece_for_move(self, player_id, destination_cell):
        movable_pieces_list = self.get_movable_pieces(player_id, self.dice_value)
        for piece in movable_pieces_list:
             dest = self.get_destination_cell(piece, self.dice_value)
             if dest == destination_cell: return piece
        return None

    def find_piece_by_id(self, player_id, piece_id):
        if 0 <= player_id < len(self.players):
            player_pieces = self.players[player_id]
            for piece in player_pieces:
                if piece.id == piece_id: return piece
        return None