# network/server.py
import socket
import threading
import json
import time
import random
import string
import traceback
import logging
from core.game_manager import GameManager
from core.piece import Piece
from network.protocol import *
from utils.constants import MAX_PLAYERS

# --- Cấu hình Logging ---
logging.basicConfig(
    level=logging.DEBUG, # Đặt DEBUG để xem log chi tiết
    format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# -------------------------

# --- Cấu hình Server ---
HOST = '0.0.0.0'
PORT = 65432
ENCODING = 'utf-8'
ROOM_ID_LENGTH = 4

# --- Quản lý Trạng thái Server ---
rooms = {}
clients_room = {}
server_lock = threading.Lock()

# --- Hàm Tiện Ích ---
def generate_room_id():
    while True:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=ROOM_ID_LENGTH))
        with server_lock:
            if room_id not in rooms:
                return room_id

def get_room_details(room_id):
    logging.debug("Bắt đầu get_room_details cho phòng: %s", room_id)
    details = None
    try:
        with server_lock:
            room = rooms.get(room_id)
            if room:
                logging.debug("Tìm thấy phòng trong get_room_details. Clients: %s", room.get("clients", {}).keys())
                player_ids = sorted(list(room["clients"].keys()))
                details = {"room_id": room_id,"host_id": room.get("host_id", -1),"current_players": len(room["clients"]),"max_players": room.get("max_players", 0),"player_ids": player_ids,"game_started": room.get("game_started", False)}
                logging.debug("Tạo dictionary chi tiết phòng thành công.")
            else: logging.warning("Không tìm thấy phòng %s bên trong get_room_details.", room_id)
    except Exception as e: logging.exception("EXCEPTION bên trong get_room_details cho phòng %s", room_id)
    logging.debug("Kết thúc get_room_details, trả về: %s", details)
    return details

# Trong file network/server.py

# !!! BỎ `with server_lock:` KHỎI HÀM NÀY !!!
def serialize_game_state_for_room(room_id):
    """Chuyển đổi trạng thái game của một phòng cụ thể (GIẢ ĐỊNH CALLER ĐÃ GIỮ LOCK)."""
    logging.debug("Bắt đầu serialize_game_state_for_room cho phòng %s (đã có lock)", room_id)
    state = {}
    try:
        # Không cần `with server_lock:` ở đây nữa
        room = rooms.get(room_id)
        if not room:
            logging.warning("serialize: Phòng %s không tồn tại.", room_id)
            return {}

        gm = room.get("game_manager")
        is_started = room.get("game_started", False)
        max_p = room.get("max_players", 0)
        current_p = len(room.get("clients", {}))

        if not gm or not is_started:
            logging.debug("serialize: Game chưa bắt đầu hoặc GM chưa có.")
            # Lấy thông tin cơ bản (hàm get_room_details tự xử lý lock)
            room_details = get_room_details(room_id)
            if room_details:
                 state = {'room_id': room_id, 'num_players': room_details['current_players'],'turn': -1, 'dice_value': None,'players_pieces': [[] for _ in range(max_p)],'required_players': max_p,'game_started': False}
            # else: state = {}

        else: # Game đã bắt đầu và có GM
            logging.debug("serialize: Game đã bắt đầu. Lấy dữ liệu từ GM.")
            serializable_pieces = []
            gm_num_players = getattr(gm, 'num_players', 0)
            gm_turn = getattr(gm, 'turn', -1)
            gm_dice_value = getattr(gm, 'dice_value', None)
            gm_players_list = getattr(gm, 'players', [])
            logging.debug("serialize: gm.num_players=%s, gm.turn=%s, type(gm.players)=%s", gm_num_players, gm_turn, type(gm_players_list).__name__)
            if not isinstance(gm_players_list, list): gm_players_list = []
            while len(gm_players_list) < gm_num_players: gm_players_list.append([])

            logging.debug("serialize: Bắt đầu duyệt gm.players (có %d)...", len(gm_players_list))
            for player_idx, player_pieces in enumerate(gm_players_list):
                if player_idx < gm_num_players:
                    logging.debug("   Serialize cho P%d...", player_idx + 1)
                    pieces_data = []
                    if isinstance(player_pieces, list):
                        for p_idx, p in enumerate(player_pieces):
                            try:
                                piece_info = {'id': p.id, 'player_id': p.player_id, 'path_index': p.path_index, 'finished': p.finished}
                                pieces_data.append(piece_info)
                            except AttributeError as ae: logging.warning("   serialize: P%d item không hợp lệ index %d (thiếu %s): %s", player_idx+1, p_idx, ae, p)
                            except Exception as piece_err: logging.warning("   serialize: Lỗi xử lý quân cờ P%d index %d: %s", player_idx+1, p_idx, piece_err)
                    else: logging.warning("   serialize: gm.players[%d] không phải list: %s", player_idx, player_pieces)
                    serializable_pieces.append(pieces_data)

            logging.debug("serialize: Tạo dictionary state cuối cùng...")
            state = {'room_id': room_id, 'num_players': gm_num_players, 'turn': gm_turn, 'dice_value': gm_dice_value, 'players_pieces': serializable_pieces, 'required_players': max_p, 'game_started': True}
            logging.debug("serialize: Tạo state thành công.")

    except Exception as ser_err:
        logging.exception("LỖI NGHIÊM TRỌNG trong serialize_game_state_for_room cho phòng %s", room_id)
        state = {}

    logging.debug("Kết thúc serialize_game_state_for_room, trả về state.")
    return state

# Trong file network/server.py

# Trong file network/server.py

def broadcast_to_room(room_id, message_data, exclude_pid=None):
    """Gửi thông điệp cho tất cả client trong một phòng (Tối ưu hóa lock)."""
    logging.debug("Bắt đầu broadcast_to_room cho phòng %s (loại: %s)", room_id, message_data.get('type'))
    message_json = ""
    try:
        message_json = json.dumps(message_data) + '\n'
        message_bytes = message_json.encode(ENCODING)
        logging.debug("   Đã mã hóa JSON.")
    except Exception as encode_err:
        logging.exception("   LỖI MÃ HÓA JSON ĐỂ BROADCAST")
        return

    clients_to_send = {} # Dictionary {pid: conn} để gửi
    # *** Chỉ giữ lock để lấy danh sách client ***
    with server_lock:
        room = rooms.get(room_id)
        if not room:
            logging.warning("broadcast: Phòng %s không tồn tại khi lấy client list.", room_id)
            return
        # Lấy bản sao danh sách client cần gửi
        for pid, conn in room["clients"].items():
            if pid != exclude_pid:
                clients_to_send[pid] = conn
        logging.debug("   Broadcast: Lấy được %d client để gửi.", len(clients_to_send))
    # *** Lock đã được nhả ra ***

    # --- Gửi tin nhắn NGOÀI LOCK ---
    disconnected_pids = [] # Chỉ lưu pid bị lỗi
    if not clients_to_send:
        logging.debug("   Broadcast: Không có client nào để gửi.")
        return
        
    logging.debug("   Broadcast: Bắt đầu vòng lặp gửi (ngoài lock)...")
    for pid, conn in clients_to_send.items():
        logging.debug("   Broadcast: Đang gửi đến P%d...", pid + 1)
        try:
            conn.sendall(message_bytes)
            logging.debug("      -> Broadcast: Gửi thành công đến P%d.", pid + 1)
        except (BrokenPipeError, ConnectionResetError) as send_err:
            logging.warning("   Broadcast: Lỗi kết nối khi gửi đến P%d: %s. Đánh dấu.", pid + 1, send_err)
            disconnected_pids.append(pid) # Chỉ lưu pid
        except Exception as e:
            logging.exception("   Broadcast: Lỗi không xác định khi gửi đến P%d", pid + 1)
            disconnected_pids.append(pid) # Chỉ lưu pid

    # --- Xử lý ngắt kết nối (ngoài lock) ---
    if disconnected_pids:
        logging.info("Broadcast: Xử lý %d client ngắt kết nối sau khi gửi.", len(disconnected_pids))
        for pid in disconnected_pids:
            # Lấy conn mới nhất từ dict toàn cục (có thể đã bị đóng)
            # Hoặc tìm conn dựa trên pid trong rooms (cần lock lại)
            # Cách đơn giản: Gọi handle_client_disconnected chỉ với pid
            # Nhưng hàm đó cần conn -> cần sửa lại handle_client_disconnected hoặc tìm conn
            
            # Tạm thời: tìm lại conn (cần lock) - có thể gây deadlock nếu handle_client_disconnected lại gọi broadcast
            # Cách an toàn hơn: Tạo 1 list (pid, room_id) rồi xử lý riêng
            conn_to_close = None
            with server_lock:
                 room = rooms.get(room_id)
                 if room and pid in room["clients"]:
                      conn_to_close = room["clients"].get(pid) # Lấy socket để đóng
                 
            if conn_to_close:
                 handle_client_disconnected(conn_to_close, room_id, pid, "lỗi gửi broadcast")
            else:
                 logging.warning("Không tìm thấy kết nối của P%d trong phòng %s để xử lý ngắt kết nối.", pid+1, room_id)


    logging.debug("Kết thúc broadcast_to_room cho phòng %s", room_id)

def send_to_client(conn, message_data):
    if not conn: return False
    try:
        message_json = json.dumps(message_data) + '\n'; message_bytes = message_json.encode(ENCODING)
        conn.sendall(message_bytes); return True
    except Exception as e: logging.warning("Lỗi gửi trực tiếp đến client: %s", e); return False

# --- HÀM BỊ THIẾU ĐƯỢC THÊM LẠI Ở ĐÂY ---
def handle_client_disconnected(conn, room_id, player_id, reason=""):
     """Xử lý khi client ngắt kết nối."""
     logging.info("Người chơi %s phòng %s ngắt kết nối (%s).", player_id + 1 if player_id != -1 else '?', room_id if room_id else 'N/A', reason)
     room_existed = False
     remaining_clients = 0
     room_was_ingame = False
     with server_lock:
          # Xóa client khỏi danh sách chung
          if conn in clients_room: del clients_room[conn]
          # Xóa client khỏi phòng cụ thể
          room = rooms.get(room_id)
          if room:
                room_existed = True
                room_was_ingame = room.get("game_started", False)
                if player_id in room["clients"]:
                    del room["clients"][player_id]
                    logging.info("Đã xóa P%d khỏi phòng %s.", player_id + 1, room_id)
                    remaining_clients = len(room["clients"])
                if remaining_clients == 0:
                    logging.info("Phòng %s rỗng, đang xóa...", room_id)
                    del rooms[room_id]
                else:
                     broadcast_to_room(room_id, {"type": MSG_TYPE_PLAYER_LEFT, "payload": get_room_details(room_id)}) # Gửi lại room details mới
                     if room_was_ingame:
                          logging.info("Game phòng %s kết thúc do người chơi thoát.", room_id)
                          room["game_started"] = False
                          room["game_manager"] = None
                          broadcast_to_room(room_id, {"type": MSG_TYPE_ERROR, "payload": {"message": f"Người chơi {player_id+1} thoát. Game kết thúc."}})
          else:
               if room_id is None and player_id == -1: logging.info("Client %s ngắt kết nối trước khi vào phòng.", conn.getpeername() if conn else "N/A")
               else: logging.warning("Phòng %s không tồn tại khi xử lý ngắt kết nối P%d.", room_id, player_id + 1)
     try: conn.close()
     except: pass
# ----------------------------------------------

# Trong file network/server.py

# ... (Các hàm và import khác giữ nguyên) ...

def handle_client_thread(conn, addr):
    """Luồng chính xử lý giao tiếp với một client."""
    current_room_id = None
    my_player_id = -1
    client_addr_str = f"{addr[0]}:{addr[1]}"
    threading.current_thread().name = f"Client-{client_addr_str}"
    logging.info("Bắt đầu luồng xử lý cho %s", client_addr_str)

    try:
        buffer = ""
        while True:
            # --- Nhận dữ liệu ---
            try:
                data = conn.recv(1024)
                if not data:
                    logging.info("Client %s đóng kết nối (không có dữ liệu).", client_addr_str)
                    handle_client_disconnected(conn, current_room_id, my_player_id, "kết nối đóng")
                    break
            except (ConnectionResetError, BrokenPipeError):
                 logging.warning("Client %s ngắt kết nối (lỗi recv).", client_addr_str)
                 handle_client_disconnected(conn, current_room_id, my_player_id, "lỗi kết nối (recv)")
                 break
            except socket.timeout:
                 logging.debug("Client %s timeout.", client_addr_str)
                 continue
            except Exception as e:
                 logging.error("Lỗi recv() từ %s: %s", client_addr_str, e, exc_info=True)
                 handle_client_disconnected(conn, current_room_id, my_player_id, "lỗi recv()")
                 break

            # --- Xử lý Buffer và JSON ---
            buffer += data.decode(ENCODING)
            while '\n' in buffer:
                message_json, buffer = buffer.split('\n', 1)
                if not message_json: continue

                try:
                    action = json.loads(message_json)
                    action_type = action.get("type")
                    payload = action.get("payload", {})
                    logging.debug("Nhận từ P%d Room %s: %s", my_player_id + 1, current_room_id, action_type)

                    # --- Xử lý Tạo Phòng ---
                    if action_type == "create_room":
                         if current_room_id: logging.warning("P%d đã ở phòng %s, bỏ qua create_room.", my_player_id+1, current_room_id); continue
                         max_p = payload.get("max_players", 2); max_p = max_p if max_p in [2,4] else 2
                         room_id = generate_room_id()
                         my_player_id = 0
                         with server_lock:
                              rooms[room_id] = {"game_manager": None, "clients": {my_player_id: conn}, "max_players": max_p, "host_id": my_player_id, "game_started": False}
                              clients_room[conn] = room_id
                         current_room_id = room_id
                         threading.current_thread().name = f"P{my_player_id+1}-R{current_room_id}"
                         logging.info("P%d (%s) tạo phòng %s [%d người].", my_player_id+1, client_addr_str, room_id, max_p)
                         send_to_client(conn, {"type": "room_created", "payload": get_room_details(room_id)})

                    # --- Xử lý Vào Phòng ---
                    elif action_type == "join_room":
                         if current_room_id: logging.warning("P%d đã ở phòng %s, bỏ qua join_room.", my_player_id+1, current_room_id); continue
                         req_room_id = payload.get("room_id", "").strip().upper()
                         logging.info("Nhận yêu cầu vào phòng: %s từ %s", req_room_id, client_addr_str)
                         if not req_room_id: logging.warning("Yêu cầu join_room thiếu room_id."); continue

                         join_success, assigned_player_id, room_details_after_join, error_message = False, -1, None, None
                         max_players_for_room = 0

                         with server_lock:
                              room = rooms.get(req_room_id)
                              logging.info("Tìm thấy phòng %s (trong lock): %s", req_room_id, room is not None)
                              if room:
                                   is_started = room.get("game_started")
                                   current_num = len(room["clients"])
                                   max_num = room.get("max_players", 0)
                                   max_players_for_room = max_num
                                   logging.info("Trạng thái phòng %s (trong lock): Started=%s, Players=%d/%d", req_room_id, is_started, current_num, max_num)
                                   if is_started: error_message = "Game đã bắt đầu."
                                   elif current_num >= max_num: error_message = "Phòng đã đầy."
                                   else:
                                        existing_ids = room["clients"].keys()
                                        for i in range(max_num):
                                             if i not in existing_ids: assigned_player_id = i; break
                                        logging.info("Tìm được ID trống (trong lock): %d", assigned_player_id)
                                        if assigned_player_id != -1:
                                             room["clients"][assigned_player_id] = conn
                                             clients_room[conn] = req_room_id
                                             current_room_id = req_room_id
                                             my_player_id = assigned_player_id
                                             threading.current_thread().name = f"P{my_player_id+1}-R{current_room_id}"
                                             join_success = True
                                             logging.info("Gán P%d vào room dict thành công (trong lock).", assigned_player_id+1)
                                        else: error_message = "Lỗi server khi tìm ID."; logging.error("Lỗi tìm ID trống phòng %s (trong lock).", req_room_id)
                              else: error_message = "Phòng không tồn tại."

                         if join_success:
                              logging.info("Người chơi %d (%s) vào phòng %s.", my_player_id+1, client_addr_str, current_room_id)
                              try:
                                   logging.info("Lấy thông tin phòng chi tiết (ngoài lock)...")
                                   room_details_after_join = get_room_details(current_room_id)
                                   if room_details_after_join is None: raise ValueError("Phòng không còn tồn tại sau khi lấy chi tiết.")
                                   logging.info("Chi tiết phòng mới: %s", room_details_after_join)

                                   join_payload = room_details_after_join.copy(); join_payload["player_id"] = my_player_id
                                   logging.info("--> Gửi joined_room cho P%d.", my_player_id+1)
                                   if not send_to_client(conn, {"type": "joined_room", "payload": join_payload}): raise ConnectionError("Gửi joined_room thất bại")
                                   logging.info("   Gửi joined_room thành công.")

                                   logging.info("--> Broadcast player_joined cho phòng %s (trừ P%d).", current_room_id, my_player_id+1)
                                   broadcast_to_room(current_room_id, {"type": MSG_TYPE_PLAYER_JOINED, "payload": room_details_after_join}, exclude_pid=my_player_id)
                                   logging.info("   Broadcast player_joined xong.")

                                   current_players_now = room_details_after_join["current_players"]
                                   logging.info("--> Kiểm tra đủ người: %d/%d", current_players_now, max_players_for_room)
                                   if current_players_now == max_players_for_room:
                                        logging.info("--> Đủ người, chuẩn bị bắt đầu game...")
                                        game_started_successfully = False
                                        with server_lock:
                                             room_to_start = rooms.get(current_room_id)
                                             if room_to_start and not room_to_start.get("game_started") and len(room_to_start["clients"]) == room_to_start["max_players"]:
                                                  logging.info("   Khởi tạo GameManager...")
                                                  room_to_start["game_manager"] = GameManager(num_players=max_players_for_room)
                                                  room_to_start["game_started"] = True
                                                  game_started_successfully = True
                                        if game_started_successfully:
                                             logging.info("   Serialize trạng thái game ban đầu...")
                                             initial_state = serialize_game_state_for_room(current_room_id)
                                             logging.info("   Chuẩn bị broadcast GAME_STATE...")
                                             broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_STATE, "payload": initial_state})
                                             logging.info("   Broadcast GAME_STATE xong.")
                                             time.sleep(0.1)
                                             turn_player = -1
                                             with server_lock:
                                                  room = rooms.get(current_room_id)
                                                  if room and room.get("game_manager"): turn_player = room["game_manager"].turn
                                             if turn_player != -1:
                                                  logging.info("   Chuẩn bị broadcast YOUR_TURN (Lượt P%d)...", turn_player + 1)
                                                  broadcast_to_room(current_room_id, {"type": MSG_TYPE_YOUR_TURN, "payload": {"player_id": turn_player}})
                                                  logging.info("   Broadcast YOUR_TURN xong.")
                                                  logging.info("   Khởi động game thành công!")
                                             else: logging.error("   Không lấy được lượt đi đầu tiên!"); broadcast_to_room(current_room_id, {"type": MSG_TYPE_ERROR, "payload": {"message": "Lỗi server."}})
                                        else: logging.warning("Không thể bắt đầu game phòng %s sau khi kiểm tra lại.", current_room_id)
                              except Exception as join_process_err:
                                   logging.exception("Lỗi trong quá trình xử lý sau khi P%d vào phòng %s", my_player_id+1, current_room_id)
                                   handle_client_disconnected(conn, current_room_id, my_player_id, "lỗi sau khi join")
                                   continue
                         elif error_message:
                              logging.warning("Từ chối P%d (%s) vào phòng %s: %s", my_player_id+1 if my_player_id != -1 else '?', client_addr_str, req_room_id, error_message)
                              send_to_client(conn, {"type": MSG_TYPE_ERROR, "payload": {"message": error_message}})

                    # --- Xử lý Bắt Đầu Game từ Host ---
                    elif action_type == "start_game":
                         if not current_room_id: logging.warning("P%d gửi start_game khi chưa vào phòng.", my_player_id+1); continue
                         logging.info("P%d yêu cầu bắt đầu game phòng %s.", my_player_id+1, current_room_id)
                         game_started_successfully = False
                         with server_lock:
                              room_to_start = rooms.get(current_room_id)
                              if (room_to_start and room_to_start.get("host_id") == my_player_id and
                                  len(room_to_start["clients"]) == room_to_start.get("max_players") and
                                  not room_to_start.get("game_started")):
                                    try:
                                        logging.info("   (Host Check OK) Khởi tạo GameManager...")
                                        room_to_start["game_manager"] = GameManager(num_players=room_to_start["max_players"])
                                        room_to_start["game_started"] = True
                                        game_started_successfully = True # Đánh dấu để gửi tin nhắn sau
                                    except Exception as start_err: logging.exception("   LỖI NGHIÊM TRỌNG KHI HOST BẮT ĐẦU GAME PHÒNG %s", current_room_id); broadcast_to_room(current_room_id, {"type": MSG_TYPE_ERROR, "payload": {"message": "Lỗi server."}})
                              else: # Gửi lỗi nếu không đủ điều kiện
                                   reason = "Không phải host."
                                   if not room_to_start: reason = "Phòng không tồn tại."
                                   elif room_to_start.get("game_started"): reason = "Game đã bắt đầu rồi."
                                   elif room_to_start.get("host_id") != my_player_id: reason = "Chỉ host mới bắt đầu được." # Rõ ràng hơn
                                   elif len(room_to_start["clients"]) != room_to_start.get("max_players"): reason = "Chưa đủ người chơi."
                                   logging.warning("P%d không thể bắt đầu game phòng %s: %s", my_player_id+1, current_room_id, reason)
                                   send_to_client(conn, {"type": MSG_TYPE_MOVE_INVALID, "payload": {"reason": f"Không thể bắt đầu: {reason}"}})

                         # Gửi tin nhắn sau khi nhả lock (nếu bắt đầu thành công)
                         if game_started_successfully:
                              logging.info("   Serialize trạng thái game ban đầu...")
                              initial_state = serialize_game_state_for_room(current_room_id)
                              logging.info("   Chuẩn bị broadcast GAME_STATE...")
                              broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_STATE, "payload": initial_state})
                              logging.info("   Broadcast GAME_STATE xong.")
                              time.sleep(0.1)
                              turn_player = -1
                              with server_lock: # Lấy lượt đi đầu (cần lock lại)
                                   room = rooms.get(current_room_id)
                                   if room and room.get("game_manager"): turn_player = room["game_manager"].turn
                              if turn_player != -1:
                                   logging.info("   Chuẩn bị broadcast YOUR_TURN (Lượt P%d)...", turn_player + 1)
                                   broadcast_to_room(current_room_id, {"type": MSG_TYPE_YOUR_TURN, "payload": {"player_id": turn_player}})
                                   logging.info("   Khởi động game thành công theo yêu cầu của Host!")
                              else: logging.error("   Không lấy được lượt đi đầu tiên!"); broadcast_to_room(current_room_id, {"type": MSG_TYPE_ERROR, "payload": {"message": "Lỗi server."}})

                    # --- Xử lý hành động trong game (Roll, Move) ---
                    elif current_room_id:
                        room_state, gm_instance = None, None
                        # Chỉ cần lấy gm_instance trong lock, không cần giữ lock lâu
                        with server_lock:
                            room_state = rooms.get(current_room_id)
                            if room_state and room_state.get("game_started"):
                                gm_instance = room_state.get("game_manager")

                        if gm_instance:
                            current_turn = gm_instance.turn # Đọc lượt đi (an toàn ngoài lock)
                            if current_turn == my_player_id:
                                # --- Xử lý Gieo Xúc Xắc ---
                                if action_type == MSG_TYPE_ROLL_DICE:
                                    logging.info("--> BẮT ĐẦU XỬ LÝ ROLL_DICE")
                                    if gm_instance.dice_value is not None:
                                        logging.warning("   Từ chối roll: Đã gieo rồi."); send_to_client(conn, {"type": MSG_TYPE_MOVE_INVALID, "payload": {"reason": "Đã gieo rồi."}}); continue

                                    try:
                                        dice_roll = random.randint(1, 6); gm_instance.dice_value = dice_roll
                                        logging.info("   Room %s - P%d gieo %d", current_room_id, my_player_id + 1, dice_roll)

                                        # --- TÍNH TOÁN NƯỚC ĐI HỢP LỆ ---
                                        valid_destinations = []
                                        movable_pieces_with_dest = [] # Lưu cả quân cờ và ô đích
                                        movable_pieces = gm_instance.get_movable_pieces(my_player_id, dice_roll)
                                        if movable_pieces:
                                             logging.info("   Tìm thấy %d nước đi hợp lệ.", len(movable_pieces))
                                             for piece in movable_pieces:
                                                  # Sử dụng get_destination_cell để lấy tọa độ ô đích
                                                  dest_cell = gm_instance.get_destination_cell(piece, dice_roll)
                                                  if dest_cell:
                                                       valid_destinations.append(list(dest_cell)) # Chuyển tuple thành list để gửi JSON
                                                       movable_pieces_with_dest.append({"piece_id": piece.id, "dest_cell": list(dest_cell)})
                                             logging.debug("   Danh sách ô đích hợp lệ: %s", valid_destinations)
                                        else:
                                             logging.info("   Không có nước đi hợp lệ.")
                                        # --------------------------------

                                        logging.info("   Chuẩn bị gửi GAME_STATE (sau gieo)...")
                                        current_state = serialize_game_state_for_room(current_room_id)
                                        # --- THÊM valid_destinations VÀO STATE ---
                                        current_state["valid_destinations"] = valid_destinations
                                        # -----------------------------------------
                                        if not current_state: raise ValueError("Serialize sau khi gieo trả về state rỗng!")
                                        broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_STATE, "payload": current_state})
                                        logging.info("   Gửi GAME_STATE (sau gieo) xong.")

                                        # Xử lý tự động chuyển lượt nếu không có nước đi
                                        if not movable_pieces:
                                            # (Giữ nguyên logic chuyển lượt / reset xúc xắc như trước)
                                            if dice_roll != 6:
                                                logging.info("   Không phải 6, chuẩn bị chuyển lượt...")
                                                gm_instance.next_turn(); time.sleep(0.5)
                                                state_after_next = serialize_game_state_for_room(current_room_id)
                                                if not state_after_next: raise ValueError("Serialize sau next_turn rỗng!")
                                                broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_STATE, "payload": state_after_next}) # Gửi state mới (dice=None)
                                                time.sleep(0.1)
                                                next_turn_player = gm_instance.turn
                                                broadcast_to_room(current_room_id, {"type": MSG_TYPE_YOUR_TURN, "payload": {"player_id": next_turn_player}})
                                            else:
                                                 logging.info("   Gieo 6 không đi được, reset xúc xắc...")
                                                 gm_instance.dice_value = None
                                                 state_after_reset = serialize_game_state_for_room(current_room_id)
                                                 if not state_after_reset: raise ValueError("Serialize sau reset dice rỗng!")
                                                 broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_STATE, "payload": state_after_reset}) # Gửi state mới (dice=None)
                                                 time.sleep(0.1)
                                                 broadcast_to_room(current_room_id, {"type": MSG_TYPE_YOUR_TURN, "payload": {"player_id": my_player_id}}) # Vẫn lượt người này

                                    except Exception as roll_err:
                                         logging.exception("   LỖI NGHIÊM TRỌNG KHI XỬ LÝ ROLL_DICE TỪ P%d", my_player_id+1)
                                         send_to_client(conn, {"type": MSG_TYPE_ERROR, "payload": {"message": "Lỗi server khi gieo."}})

                                    logging.info("<-- KẾT THÚC XỬ LÝ ROLL_DICE")

                                # --- Xử lý Di Chuyển Quân ---
                                elif action_type == MSG_TYPE_MOVE_PIECE:
                                    logging.info("--> BẮT ĐẦU XỬ LÝ MOVE_PIECE") # Log mới
                                    # Kiểm tra đã gieo chưa (an toàn ngoài lock)
                                    current_dice_value_move = gm_instance.dice_value 
                                    if current_dice_value_move is None:
                                        logging.warning("   Từ chối move: Cần gieo trước.") # Log mới
                                        send_to_client(conn, {"type": MSG_TYPE_MOVE_INVALID, "payload": {"reason": "Cần gieo trước."}}); continue
                                    
                                    piece_id = payload.get("piece_id");
                                    if piece_id is None: logging.warning("   Từ chối move: Thiếu piece_id."); continue
                                    
                                    logging.info("   Tìm kiếm quân cờ P%d ID %d...", my_player_id+1, piece_id) # Log mới
                                    # find_piece_by_id chỉ đọc, an toàn ngoài lock
                                    piece_to_move = gm_instance.find_piece_by_id(my_player_id, piece_id) 
                                    if not piece_to_move: logging.warning("   Không tìm thấy quân cờ."); continue
                                    logging.info("   Tìm thấy quân cờ.") # Log mới

                                    logging.info("   Kiểm tra nước đi hợp lệ...") # Log mới
                                    # get_movable_pieces chỉ đọc, an toàn ngoài lock
                                    movable_pieces = gm_instance.get_movable_pieces(my_player_id, current_dice_value_move) 
                                    if piece_to_move not in movable_pieces:
                                        logging.warning("   Quân cờ không hợp lệ để di chuyển.") # Log mới
                                        send_to_client(conn, {"type": MSG_TYPE_MOVE_INVALID, "payload": {"reason": f"Không thể di chuyển quân {piece_id+1}."}}); continue
                                    logging.info("   Nước đi hợp lệ.") # Log mới

                                    kick_message = None
                                    next_turn_after_move = -1
                                    dice_reset_after_move = False
                                    game_has_winner = False # Biến mới
                                    winner_id = -1 # Biến mới
                                    # --- Thực hiện di chuyển và kiểm tra thắng (cần lock) ---
                                    with server_lock:
                                         room_check = rooms.get(current_room_id)
                                         if room_check and room_check.get("game_manager"):
                                              gm_now = room_check["game_manager"]
                                              if gm_now.turn == my_player_id and gm_now.dice_value == current_dice_value_move:
                                                   logging.info("   Thực hiện move_piece...")
                                                   kick_message = gm_now.move_piece(piece_to_move) # move_piece tự xử lý lượt / reset dice
                                                   next_turn_after_move = gm_now.turn
                                                   dice_reset_after_move = (gm_now.dice_value is None)
                                                   
                                                   # --- KIỂM TRA THẮNG NGAY SAU KHI ĐI ---
                                                   # (Hàm move_piece đã tự gọi _check_for_winner và cập nhật gm_now.winner)
                                                   if gm_now.winner is not None:
                                                        game_has_winner = True
                                                        winner_id = gm_now.winner
                                                        room_check["game_started"] = False # Đánh dấu game kết thúc
                                                   # -----------------------------------
                                                   
                                                   logging.info("   move_piece xong. Kick: %s, NextTurn: %d, DiceReset: %s, Winner: %s", 
                                                                bool(kick_message), next_turn_after_move+1, dice_reset_after_move, game_has_winner)
                                              else:
                                                   logging.warning("   Trạng thái game thay đổi trước khi kịp move!"); send_to_client(conn, {"type": MSG_TYPE_MOVE_INVALID, "payload": {"reason": "Trạng thái game đã thay đổi."}}); continue
                                         else: raise ValueError("Phòng/GM mất khi chuẩn bị thực hiện move")
                                    # --- Lock released ---

                                    logging.info("   Chuẩn bị gửi GAME_STATE (sau move)...")
                                    state_after_move = serialize_game_state_for_room(current_room_id)
                                    if not state_after_move: raise ValueError("Serialize sau move trả về state rỗng!")
                                    broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_STATE, "payload": state_after_move})
                                    logging.info("   Gửi GAME_STATE (sau move) xong.")

                                    # --- XỬ LÝ KẾT THÚC GAME HOẶC CHUYỂN LƯỢT ---
                                    if game_has_winner:
                                         # Gửi thông báo GAME_OVER
                                         logging.info("   GAME OVER! Người chiến thắng là P%d.", winner_id + 1)
                                         broadcast_to_room(current_room_id, {"type": MSG_TYPE_GAME_OVER, "payload": {"winner_id": winner_id}})
                                         # (Không cần gửi YOUR_TURN nữa)
                                    elif next_turn_after_move != current_turn or dice_reset_after_move:
                                        # Gửi thông báo lượt tiếp theo
                                        time.sleep(0.1)
                                        logging.info("   Chuẩn bị gửi YOUR_TURN (Lượt P%d)...", next_turn_after_move + 1)
                                        broadcast_to_room(current_room_id, {"type": MSG_TYPE_YOUR_TURN, "payload": {"player_id": next_turn_after_move}})
                                        logging.info("   Gửi YOUR_TURN xong.")
                                    
                                    logging.info("<-- KẾT THÚC XỬ LÝ MOVE_PIECE")

                                else: logging.warning("Hành động không hợp lệ khi đến lượt từ P%d: %s", my_player_id+1, action_type)
                            else: send_to_client(conn, {"type": MSG_TYPE_MOVE_INVALID, "payload": {"reason": "Không phải lượt của bạn."}})
                        else: pass # Phòng không tồn tại hoặc game chưa bắt đầu
                    else: logging.warning("Hành động không xác định hoặc client chưa vào phòng từ %s: %s", client_addr_str, action_type)

                except json.JSONDecodeError: logging.error("Lỗi JSON từ %s: %s", client_addr_str, message_json)
                except Exception as e: logging.exception("Lỗi xử lý hành động từ %s", client_addr_str)

    except Exception as e:
        logging.exception("Lỗi nghiêm trọng trong luồng client %s", client_addr_str)
        handle_client_disconnected(conn, current_room_id, my_player_id, "lỗi nghiêm trọng")

    logging.info("Đã đóng luồng cho %s.", client_addr_str)

# ... (Vòng lặp Server chính giữ nguyên) ...


# --- Vòng lặp Server chính ---
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: # Thêm try-except cho bind
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logging.info("✅ Server đang lắng nghe trên cổng %d...", PORT)

    while True: # Vòng lặp chấp nhận kết nối
        try:
            conn, addr = server_socket.accept()
            logging.info("Kết nối mới từ %s", addr[0])
            thread = threading.Thread(target=handle_client_thread, args=(conn, addr), daemon=True)
            thread.start()
        except OSError as e: # Bắt lỗi khi server socket bị đóng (ví dụ khi Ctrl+C)
             logging.warning("Lỗi accept: %s. Có thể server đang tắt.", e)
             break # Thoát vòng lặp accept
        except Exception as e:
             logging.exception("Lỗi không mong muốn khi accept kết nối")

except KeyboardInterrupt: logging.info("\nĐang tắt server...")
except Exception as e: logging.exception("Lỗi nghiêm trọng ở vòng lặp server chính")
finally:
    logging.info("Đang đóng các kết nối client...")
    with server_lock: all_conns = list(clients_room.keys())
    for c in all_conns:
        try: c.close()
        except: pass
    logging.info("Đang đóng socket server...")
    server_socket.close()
    logging.info("Server đã tắt.")
    