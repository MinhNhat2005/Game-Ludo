# core/game_manager.py
import logging
from core.piece import Piece
from core.board import Board
from . import rules
from ai.random_bot import RandomBot
from ai.hard_bot import HardBot
from utils.constants import WIDTH, HEIGHT, CELL
import random

class GameManager:
    def __init__(self, num_players=4, player_types=None):
        self.num_players = num_players
        self.turn = 0
        self.dice_value = None
        self.winner = None
        self.board = Board(start_x=(WIDTH - CELL*15)//2, start_y=(HEIGHT - CELL*15)//2)

        # Khởi tạo người chơi và bot
        self.player_types = player_types or ['human'] * num_players
        self.players = self._init_players()
        self.bots = self._init_bots()

        # Lưu thông tin lượt vừa chơi
        self.last_move_info = None

    def _init_players(self):
        players = []
        for pid in range(self.num_players):
            pieces = [Piece(pid, piece_id) for piece_id in range(4)]
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

    def run_bot_turn(self):
        self.dice_value = random.randint(1, 6)
        bot = self.bots[self.turn]
        piece_to_move = bot.choose_move()

        if piece_to_move:
            kick_msg, just_finished, game_won = self.move_piece(piece_to_move)
            return ("đã di chuyển", kick_msg, self.dice_value, just_finished, game_won)
        else:
            # Không có quân nào đi được
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
        return True

    def get_movable_pieces(self, player_id, dice_value):
        movable = []
        path_len = len(self.board.get_path_for_player(player_id))
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

    def move_piece(self, piece_to_move):
        if self.dice_value is None or self.dice_value == -1:
            logging.warning("Move_piece được gọi khi dice_value là None/GameOver")
            return (None, False, False)

        dice_rolled = self.dice_value
        path_len = len(self.board.get_path_for_player(piece_to_move.player_id))
        was_finished = piece_to_move.finished
        old_index = piece_to_move.path_index  # vị trí cũ

        piece_to_move.move(dice_rolled, path_len)
        new_index = piece_to_move.path_index  # vị trí mới
        just_finished_this_move = (not was_finished and piece_to_move.finished)

        kicked_piece = rules.check_and_kick_opponent(
            moving_piece=piece_to_move,
            all_players_pieces=self.players,
            board=self.board
        )

        # --- Cập nhật last_move_info chi tiết hơn ---
        self.last_move_info = {
            "player_id": piece_to_move.player_id,
            "player_color": piece_to_move.color if hasattr(piece_to_move, "color") else piece_to_move.player_id,
            "dice": dice_rolled,
            "piece_id": piece_to_move.id,
            "from_index": old_index,
            "to_index": new_index,
            "action": "moved",
            "kicked_piece": {
                "player_id": kicked_piece.player_id,
                "piece_id": kicked_piece.id
            } if kicked_piece else None,
            "finished": piece_to_move.finished
        }

        game_has_winner = False
        if just_finished_this_move:
            game_has_winner = self._check_for_winner(piece_to_move.player_id)

        if game_has_winner:
            self.dice_value = -1
        elif dice_rolled == 6 or kicked_piece is not None or just_finished_this_move:
            self.dice_value = None
        else:
            self.next_turn()

        return (kicked_piece, just_finished_this_move, game_has_winner)


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
