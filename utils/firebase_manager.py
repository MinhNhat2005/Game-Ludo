# utils/firebase_manager.py
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import datetime
from pathlib import Path

db = None
_IS_INITIALIZED = False

def initialize_firebase():
    global db, _IS_INITIALIZED
    if _IS_INITIALIZED:
        return
    try:
        CURRENT_DIR = Path(__file__).parent
        PROJECT_ROOT = CURRENT_DIR.parent
        KEY_FILE_PATH = PROJECT_ROOT / 'firebase_key.json'
        cred = credentials.Certificate(str(KEY_FILE_PATH))
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        _IS_INITIALIZED = True
        logging.info("✅ Firebase Firestore khởi tạo thành công.")
    except Exception as e:
        logging.critical(f"❌ Lỗi khởi tạo Firebase: {e}")
        db = None

def _get_match_document(match_id):
    if not db: return None
    return db.collection('ludo_matches').document(str(match_id))

def save_game_state(gm, winner_id=None, is_loadable=True):
    """
    Lưu trạng thái game lên Firebase.
    - gm: GameManager
    - winner_id: ID người thắng (nếu game kết thúc)
    - is_loadable: True nếu game có thể resume (Offline/Bot)
    """
    if not db:
        logging.warning("Firebase chưa kết nối!")
        return None

    logging.info("Bắt đầu lưu trạng thái game...")

    # Chuyển trạng thái quân cờ
    pieces_state = {}
    for pid, player_pieces in enumerate(gm.players):
        pieces_state[f'player_{pid}'] = [
            {
                'piece_id': p.id,
                'path_index': p.path_index,
                'finished': p.finished
            }
            for p in player_pieces
        ]

    current_state = {
        'num_players': gm.num_players,
        'turn': gm.turn,
        'dice_value': gm.dice_value,
        'mode': 'Bot' if any('bot' in str(t).lower() for t in gm.player_types) else 'Offline',
        'pieces_state': pieces_state
    }

    match_data = {
        'FinalState': current_state,
        'is_loadable': is_loadable,
        'NumPlayers': gm.num_players,
        'Mode': current_state['mode'],
        'StartTime': gm.start_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if winner_id is not None:
        match_data['WinnerPlayerID'] = winner_id
        match_data['EndTime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if gm.match_id is None:
            doc_ref = db.collection('ludo_matches').document()
            doc_ref.set(match_data)
            gm.match_id = doc_ref.id
            logging.info(f"Đã lưu game mới với MatchID: {gm.match_id}")
        else:
            doc_ref = db.collection('ludo_matches').document(gm.match_id)
            doc_ref.update(match_data)
            logging.info(f"Đã cập nhật game MatchID: {gm.match_id}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu game vào Firebase: {e}")

    logging.debug(f"Data đang lưu:\n{match_data}")
    return gm.match_id

def load_game_state(match_id):
    """
    Load FinalState từ Firebase (chỉ dùng cho Offline/Bot)
    """
    if not db:
        logging.warning("Firebase chưa kết nối.")
        return None
    doc_ref = _get_match_document(match_id)
    if not doc_ref:
        return None
    try:
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            logging.info(f"Đã tải MatchID {match_id} từ Firebase.")
            final_state = data.get('FinalState')
            # Chỉ load Offline/Bot
            if final_state and final_state.get('mode') in ['Offline', 'Bot']:
                return final_state
            return None
        else:
            logging.warning(f"Không tìm thấy MatchID {match_id}.")
            return None
    except Exception as e:
        logging.error(f"Lỗi khi tải từ Firebase: {e}")
        return None

def get_match_history(limit=50):
    if not db:
        logging.warning("Firebase chưa kết nối.")
        return []
    try:
        matches_stream = db.collection('ludo_matches') \
            .order_by('StartTime', direction=firestore.Query.DESCENDING) \
            .limit(limit).stream()
    except Exception as e:
        logging.error(f"Lỗi khi lấy lịch sử: {e}")
        return []

    history = []
    for doc in matches_stream:
        data = doc.to_dict()
        history.append({
            'MatchID': doc.id,
            'StartTime': data.get('StartTime'),
            'EndTime': data.get('EndTime'),
            'NumPlayers': data.get('NumPlayers'),
            'Mode': data.get('Mode'),
            'WinnerPlayerID': data.get('WinnerPlayerID'),
            'is_loadable': data.get('is_loadable', False)
        })
    return history
