# core/game_manager.py
from core.piece import Piece
from core.board import Board
from . import rules
from ai.bot_logic import BotPlayer
from utils.constants import WIDTH, HEIGHT, CELL

class GameManager:
    def __init__(self, num_players=4, player_types=None):
        self.num_players = num_players
        self.turn = 0
        self.dice_value = None
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
            if ptype == 'bot':
                bots[pid] = BotPlayer(pid, self)
        return bots

    def is_bot_turn(self):
        return self.turn in self.bots

    def run_bot_turn(self):
        """Thực thi một lượt hoàn chỉnh cho bot và trả về kết quả."""
        if not self.is_bot_turn():
            return None, None, None # Trả về 3 giá trị để tránh lỗi

        bot = self.bots[self.turn]
        piece_to_move = bot.choose_move()
        
        # Lấy giá trị xúc xắc mà bot vừa gieo
        dice_value_rolled = self.dice_value

        if piece_to_move:
            kick_message = self.move_piece(piece_to_move)
            base_msg = f"Bot (Người {self.turn + 1}) đã di chuyển."
            # Trả về cả giá trị xúc xắc
            return base_msg, kick_message, dice_value_rolled
        else:
            # Nếu bot không có nước đi, chuyển lượt (trừ khi gieo được 6)
            if self.dice_value != 6:
                self.next_turn()
            base_msg = f"Bot (Người {self.turn + 1}) không thể đi."
            return base_msg, None, dice_value_rolled

    def next_turn(self):
        self.turn = (self.turn + 1) % self.num_players
        self.dice_value = None

    def get_movable_pieces(self, player_id, dice_value):
        movable = []
        path_len = len(self.board.get_path_for_player(player_id))
        last_cell_index = path_len - 1

        for piece in self.players[player_id]:
            if piece.finished: continue
            if piece.path_index == -1 and dice_value == 6:
                movable.append(piece)
            elif piece.path_index >= 0 and (piece.path_index + dice_value) <= last_cell_index:
                movable.append(piece)
        return movable

    def move_piece(self, piece_to_move):
        if self.dice_value is None: return None

        dice_rolled = self.dice_value
        piece_to_move.move(dice_rolled)
        kick_message = rules.check_and_kick_opponent(piece_to_move, self.players, self.board)

        if dice_rolled == 6 or kick_message is not None:
            self.dice_value = None
        else:
            self.next_turn()
        return kick_message

    def get_destination_cell(self, piece, dice_value):
        if piece.path_index == -1 and dice_value == 6:
            return self.board.get_spawn_cell(piece.player_id)
        if piece.path_index >= 0:
            path = self.board.get_path_for_player(piece.player_id)
            next_index = piece.path_index + dice_value
            if next_index < len(path):
                return path[next_index]
        return None

    def find_piece_for_move(self, player_id, destination_cell):
        for piece in self.players[player_id]:
            dest = self.get_destination_cell(piece, self.dice_value)
            if dest == destination_cell:
                return piece
        return None
    
    def find_piece_by_id(self, player_id, piece_id):
        """Tìm đối tượng Piece dựa vào ID người chơi và ID quân cờ."""
        if 0 <= player_id < len(self.players):
            player_pieces = self.players[player_id]
            for piece in player_pieces:
                if piece.id == piece_id:
                    return piece
        return None # Không tìm thấy