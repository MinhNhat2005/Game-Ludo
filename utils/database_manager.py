# utils/database_manager.py
import sqlite3
import os
import logging
import json # Dùng JSON để lưu trạng thái bàn cờ
from datetime import datetime

DB_DIR = 'data'
DB_FILE = 'game_history.db'
DB_PATH = os.path.join(DB_DIR, DB_FILE)

def setup_database():
    """Khởi tạo CSDL và tạo các bảng (Matches, Actions, SavedGames)."""
    try:
        if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Bảng 1: Thông tin chung của trận đấu (Đã có)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS GameMatches (
            MatchID INTEGER PRIMARY KEY AUTOINCREMENT,
            Mode TEXT NOT NULL, NumPlayers INTEGER NOT NULL,
            StartTime TEXT NOT NULL, EndTime TEXT,
            WinnerPlayerID INTEGER
        );
        ''')

        # Bảng 2: Lịch sử hành động (Đã có)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS GameActions (
            ActionID INTEGER PRIMARY KEY AUTOINCREMENT,
            MatchID INTEGER NOT NULL, PlayerID INTEGER NOT NULL,
            ActionType TEXT NOT NULL, Detail TEXT,
            Timestamp TEXT NOT NULL,
            FOREIGN KEY (MatchID) REFERENCES GameMatches (MatchID)
        );
        ''')

        # --- BẢNG MỚI: LƯU TRẠNG THÁI GAME ---
        # Bảng này sẽ lưu "ảnh chụp" của bàn cờ khi thoát
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SavedGames (
            SavedGameID INTEGER PRIMARY KEY AUTOINCREMENT,
            MatchID INTEGER UNIQUE NOT NULL,
            Turn INTEGER NOT NULL,
            DiceValue INTEGER,
            PiecesState TEXT NOT NULL,
            LastUpdated TEXT NOT NULL,
            FOREIGN KEY (MatchID) REFERENCES GameMatches (MatchID)
        );
        ''')
        # ------------------------------------

        conn.commit()
        conn.close()
        logging.info(f"CSDL đã được khởi tạo/xác minh tại: {DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"Lỗi khi khởi tạo CSDL: {e}", exc_info=True)

class GameLogger:
    """Quản lý việc ghi log cho MỘT trận đấu cụ thể."""
    
    def __init__(self, mode, num_players, match_id_to_load=None):
        self.match_id = None
        self.mode = mode
        self.conn = None
        self.cursor = None
        
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            
            if match_id_to_load is not None:
                # Nếu là tải game, chỉ cần lấy MatchID đã có
                self.match_id = match_id_to_load
                logging.info(f"Tải lại GameLogger cho Trận đấu ID: {self.match_id}")
            else:
                # Nếu là game mới, tạo MatchID mới
                start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.cursor.execute(
                    "INSERT INTO GameMatches (Mode, NumPlayers, StartTime) VALUES (?, ?, ?)",
                    (mode, num_players, start_time)
                )
                self.match_id = self.cursor.lastrowid
                self.conn.commit()
                logging.info(f"Bắt đầu ghi log cho Trận đấu Mới ID: {self.match_id} (Chế độ: {mode})")
        except sqlite3.Error as e:
            logging.error(f"Lỗi GameLogger __init__: {e}", exc_info=True)
            if self.conn: self.conn.close()
            self.conn = None

    def log_action(self, player_id, action_type, detail=""):
        """Ghi lại một hành động (gieo, đi, đá, thắng)."""
        if not self.conn or self.match_id is None: return
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                "INSERT INTO GameActions (MatchID, PlayerID, ActionType, Detail, Timestamp) VALUES (?, ?, ?, ?, ?)",
                (self.match_id, player_id, str(action_type), str(detail), timestamp)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi log hành động (MatchID: {self.match_id}): {e}", exc_info=True)

    def log_game_end(self, winner_player_id):
        """Cập nhật người chiến thắng và XÓA game đã lưu (nếu có)."""
        if not self.conn or self.match_id is None: return
        try:
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                "UPDATE GameMatches SET EndTime = ?, WinnerPlayerID = ? WHERE MatchID = ?",
                (end_time, winner_player_id, self.match_id)
            )
            # --- XÓA GAME ĐÃ LƯU KHI ĐÃ THẮNG ---
            self.cursor.execute("DELETE FROM SavedGames WHERE MatchID = ?", (self.match_id,))
            # ------------------------------------
            self.conn.commit()
            logging.info(f"Kết thúc ghi log cho Trận đấu ID: {self.match_id}. Người thắng: P{winner_player_id + 1}")
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi log kết thúc game (MatchID: {self.match_id}): {e}", exc_info=True)
        finally:
            self.close()

    def close(self):
        """Đóng kết nối CSDL."""
        if self.conn:
            self.conn.close(); self.conn = None
            logging.info(f"Đã đóng kết nối CSDL cho MatchID: {self.match_id}")

    # --- HÀM LƯU GAME MỚI ---
    def save_game_state(self, turn, dice_value, pieces_state_list):
        """Lưu trạng thái hiện tại của game vào SavedGames."""
        if not self.conn or self.match_id is None: return
        
        try:
            pieces_state_json = json.dumps(pieces_state_list) # Chuyển list quân cờ thành JSON
            last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Dùng INSERT OR REPLACE (UPSERT) để ghi đè nếu đã có
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO SavedGames (MatchID, Turn, DiceValue, PiecesState, LastUpdated)
                VALUES (?, ?, ?, ?, ?)
                """,
                (self.match_id, turn, dice_value, pieces_state_json, last_updated)
            )
            self.conn.commit()
            logging.info(f"Đã lưu trạng thái game cho MatchID: {self.match_id}")
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lưu game (MatchID: {self.match_id}): {e}", exc_info=True)

# --- CÁC HÀM LẤY LỊCH SỬ (Giữ nguyên) ---
def get_match_history():
    """Lấy danh sách các trận đấu, KÈM THEO cờ báo có thể tải (is_loadable)."""
    try:
        if not os.path.exists(DB_PATH): return []
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Join 2 bảng để biết trận nào có trong SavedGames (và chưa kết thúc)
        cursor.execute("""
        SELECT 
            m.*, 
            (s.MatchID IS NOT NULL) AS is_loadable
        FROM GameMatches m
        LEFT JOIN SavedGames s ON m.MatchID = s.MatchID
        WHERE m.EndTime IS NULL -- Chỉ lấy các trận chưa kết thúc
        ORDER BY m.StartTime DESC 
        LIMIT 50
        """)
        matches = cursor.fetchall()
        conn.close()
        return [dict(match) for match in matches]
    except sqlite3.Error as e:
        logging.error(f"Lỗi khi lấy lịch sử trận đấu: {e}", exc_info=True)
        return []

def get_action_history(match_id):
    # (Hàm này giữ nguyên như cũ)
    try:
        if not os.path.exists(DB_PATH): return []
        conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM GameActions WHERE MatchID = ? ORDER BY Timestamp ASC", (match_id,))
        actions = cursor.fetchall(); conn.close()
        return [dict(action) for action in actions]
    except sqlite3.Error as e: logging.error(f"Lỗi lấy lịch sử hành động (MatchID: {match_id}): {e}"); return []

# --- HÀM TẢI GAME MỚI ---
def load_game_state(match_id):
    """Tải trạng thái đã lưu của một trận đấu."""
    try:
        if not os.path.exists(DB_PATH): return None
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Lấy thông tin trận đấu (Mode, NumPlayers)
        cursor.execute("SELECT Mode, NumPlayers FROM GameMatches WHERE MatchID = ?", (match_id,))
        match_info = cursor.fetchone()
        if not match_info:
            logging.error(f"Không tìm thấy MatchInfo cho MatchID: {match_id}"); conn.close(); return None

        # Lấy trạng thái đã lưu
        cursor.execute("SELECT Turn, DiceValue, PiecesState FROM SavedGames WHERE MatchID = ?", (match_id,))
        saved_state = cursor.fetchone()
        conn.close()
        
        if not saved_state:
            logging.error(f"Không tìm thấy SavedState cho MatchID: {match_id}"); return None

        # Giải mã JSON
        pieces_state_list = json.loads(saved_state['PiecesState'])
        
        loaded_data = {
            "match_id": match_id,
            "mode": match_info['Mode'],
            "num_players": match_info['NumPlayers'],
            "turn": saved_state['Turn'],
            "dice_value": saved_state['DiceValue'],
            "pieces_state": pieces_state_list
        }
        logging.info(f"Đã tải thành công trạng thái game cho MatchID: {match_id}")
        return loaded_data
        
    except sqlite3.Error as e:
        logging.error(f"Lỗi khi tải game (MatchID: {match_id}): {e}", exc_info=True)
        if conn: conn.close()
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Lỗi giải mã JSON khi tải game (MatchID: {match_id}): {e}", exc_info=True)
        if conn: conn.close()
        return None

# --- Tự động chạy setup khi file này được import ---
setup_database()