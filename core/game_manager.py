# core/game_manager.py
import logging
from core.piece import Piece
from core.board import Board
from . import rules
from ai.random_bot import RandomBot 
from ai.hard_bot import HardBot
from utils.constants import WIDTH, HEIGHT, CELL

class GameManager:
    def __init__(self, num_players=4, player_types=None):
        self.num_players = num_players
        self.turn = 0
        self.dice_value = None
        self.winner = None # Thêm thuộc tính winner
        self.board = Board(start_x=(WIDTH - CELL*15)//2, start_y=(HEIGHT - CELL*15)//2)
        
        # Khởi tạo người chơi và bot
        self.player_types = player_types or ['human'] * num_players
        self.players = self._init_players()
        self.bots = self._init_bots()

    def _init_players(self):
        players = []
        for pid in range(self.num_players):
            pieces = [Piece(pid, piece_id) for piece_id in range(4)]
            players.append(pieces)
        return players
        
    def _init_bots(self):
        bots = {}
        for pid, ptype in enumerate(self.player_types):
            if ptype == 'bot_easy': # Nếu là bot dễ
                logging.info(f"Khởi tạo Bot Dễ cho Người chơi {pid + 1}")
                bots[pid] = RandomBot(pid, self)
            elif ptype == 'bot_hard': # Nếu là bot khó
                logging.info(f"Khởi tạo Bot Khó cho Người chơi {pid + 1}")
                bots[pid] = HardBot(pid, self)
        return bots

    def is_bot_turn(self):
        return self.turn in self.bots

    def run_bot_turn(self):
        """
        Thực thi lượt của bot. (Hàm mới)
        Trả về: (base_msg, kick_msg, dice_rolled, just_finished, game_won)
        """
        if not self.is_bot_turn():
            return (None, None, None, False, False)

        bot = self.bots[self.turn]
        piece_to_move = bot.choose_move() # Hàm này tự gieo và đặt self.dice_value
        
        dice_value_rolled = self.dice_value # Lưu lại số đã gieo

        if piece_to_move:
            # move_piece trả về (kick_msg, just_finished, game_won)
            (kick_msg, just_finished, game_won) = self.move_piece(piece_to_move)
            base_msg = "đã di chuyển."
            return (base_msg, kick_msg, dice_value_rolled, just_finished, game_won)
        else:
            # Bot không có nước đi
            base_msg = "không thể đi."
            # Tự động chuyển lượt nếu không phải 6
            if self.dice_value != 6:
                self.next_turn()
            else:
                 self.dice_value = None # Cho gieo lại ở lượt sau (nếu vẫn là bot)
            return (base_msg, None, dice_value_rolled, False, False)

    def next_turn(self):
        self.turn = (self.turn + 1) % self.num_players
        self.dice_value = None

    def _check_for_winner(self, player_id):
        """Kiểm tra xem người chơi player_id đã thắng chưa."""
        if not (0 <= player_id < len(self.players)): return False
        for piece in self.players[player_id]:
            if not piece.finished:
                return False # Còn ít nhất 1 quân chưa về đích
        self.winner = player_id
        logging.info(f"Người chơi {player_id + 1} đã chiến thắng!")
        return True

    def get_movable_pieces(self, player_id, dice_value):
        """Trả về danh sách các quân cờ có thể di chuyển."""
        movable = []
        path_len = len(self.board.get_path_for_player(player_id)) # 57 ô
        last_cell_index = path_len - 1 # index 56
        
        for piece in self.players[player_id]:
            if piece.finished: continue
            if piece.path_index == -1 and dice_value == 6:
                movable.append(piece)
            elif piece.path_index >= 0:
                destination_index = piece.path_index + dice_value
                if destination_index <= last_cell_index:
                    movable.append(piece)
        return movable

    def move_piece(self, piece_to_move):
        """
        Di chuyển, kiểm tra thắng/đá/về đích, xử lý lượt. (Hàm mới)
        Trả về: (kick_message, just_finished_this_move, game_has_winner)
        """
        # Kiểm tra phòng khi gieo, không phải khi di chuyển
        if self.dice_value is None or self.dice_value == -1: 
            logging.warning("Move_piece được gọi khi dice_value là None/GameOver")
            # Trả về tuple 3 giá trị để không crash
            return (None, False, False) 

        dice_rolled = self.dice_value
        path_len = len(self.board.get_path_for_player(piece_to_move.player_id))
        was_finished = piece_to_move.finished 
        
        piece_to_move.move(dice_rolled, path_len) 
        
        just_finished_this_move = (not was_finished and piece_to_move.finished)
        kick_message = rules.check_and_kick_opponent(
            moving_piece=piece_to_move,
            all_players_pieces=self.players,
            board=self.board
        )

        game_has_winner = False
        if just_finished_this_move:
             game_has_winner = self._check_for_winner(piece_to_move.player_id)

        if game_has_winner:
             self.dice_value = -1 # Cờ báo Game Over
        elif dice_rolled == 6 or kick_message is not None or just_finished_this_move:
            self.dice_value = None # Thêm lượt
        else:
            self.next_turn() # Tự động set dice_value = None

        return (kick_message, just_finished_this_move, game_has_winner)

    def get_destination_cell(self, piece, dice_value):
        """Trả về tọa độ (grid) của ô đích."""
        if piece.path_index == -1 and dice_value == 6:
            return self.board.get_spawn_cell(piece.player_id)
        
        if piece.path_index >= 0:
            path = self.board.get_path_for_player(piece.player_id)
            next_index = piece.path_index + dice_value
            if next_index < len(path):
                return path[next_index]
        return None

    def find_piece_for_move(self, player_id, destination_cell):
        """Tìm quân cờ có thể di chuyển tới ô đích đã cho."""
        # Lấy danh sách quân đi được trước
        movable_pieces_list = self.get_movable_pieces(player_id, self.dice_value)
        
        for piece in movable_pieces_list: # Chỉ duyệt các quân đi được
             dest = self.get_destination_cell(piece, self.dice_value)
             if dest == destination_cell:
                 return piece
        return None

    def find_piece_by_id(self, player_id, piece_id):
        """Tìm đối tượng Piece dựa vào ID người chơi và ID quân cờ. (Hàm mới)"""
        if 0 <= player_id < len(self.players):
            player_pieces = self.players[player_id]
            for piece in player_pieces:
                if piece.id == piece_id:
                    return piece
        return None