# network/client.py
import socket
import threading
import json
import time # Thêm time
from network.protocol import *
import logging
# Import các lớp logic cần thiết để tái tạo trạng thái (nếu cần)
from core.piece import Piece
from core.board import Board

# --- Cấu hình Client ---
SERVER_IP = '192.168.1.7' # Sẽ được cập nhật từ OnlineLobbyView
SERVER_PORT = 65433
ENCODING = 'utf-8'

# --- Trạng thái Client (Toàn cục trong module này) ---
client_socket = None
receive_thread = None
is_connected = False
running = False # Chỉ trạng thái của luồng nhận
my_player_id = -1
game_state = {} # Lưu trạng thái game nhận từ server
sound_to_play_queue = [] # Hàng đợi âm thanh
last_message = "Chưa kết nối"

# Khóa để bảo vệ truy cập game_state từ nhiều luồng (nếu cần)
state_lock = threading.Lock()

# --- Hàm Giao tiếp Mạng ---
def connect_to_server(server_ip_addr):
    """Cố gắng kết nối đến server và bắt đầu luồng nhận."""
    global client_socket, receive_thread, last_message, is_connected, running, SERVER_IP, my_player_id, game_state
    
    # Cập nhật IP server
    SERVER_IP = server_ip_addr
    
    # Đảm bảo đóng kết nối cũ nếu có
    disconnect_from_server() 
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5.0) # Đặt timeout 5 giây cho kết nối
        client_socket.connect((SERVER_IP, SERVER_PORT))
        client_socket.settimeout(None) # Xóa timeout sau khi kết nối thành công
        
        print(f"✅ Đã kết nối đến server {SERVER_IP}:{SERVER_PORT}")
        last_message = "Đã kết nối! Chờ người chơi khác..."
        is_connected = True
        running = True # Bắt đầu chạy luồng nhận
        my_player_id = -1 # Reset ID
        game_state = {} # Reset trạng thái

        receive_thread = threading.Thread(target=receive_updates, args=(client_socket,), daemon=True)
        receive_thread.start()
        return True
        
    except socket.timeout:
        last_message = f"Lỗi: Hết thời gian chờ kết nối đến {SERVER_IP}."
        print(last_message)
        client_socket = None
        is_connected = False
        return False
    except ConnectionRefusedError:
        last_message = f"Lỗi: Không thể kết nối. Server tại {SERVER_IP} chưa chạy?"
        print(last_message)
        client_socket = None
        is_connected = False
        return False
    except Exception as e:
        last_message = f"Lỗi kết nối không xác định: {e}"
        print(last_message)
        client_socket = None
        is_connected = False
        return False

def disconnect_from_server():
    """Đóng kết nối và dừng luồng nhận."""
    global client_socket, receive_thread, running, is_connected, last_message
    running = False # Dừng luồng nhận
    is_connected = False
    last_message = "Đã ngắt kết nối."
    
    if client_socket:
        try:
            client_socket.shutdown(socket.SHUT_RDWR) # Thông báo đóng kết nối
        except OSError:
            pass # Bỏ qua lỗi nếu socket đã đóng
        finally:
             client_socket.close()
             client_socket = None
             print("Đã đóng kết nối socket.")
             
def receive_updates(sock):
    """Luồng riêng để nhận và xử lý cập nhật từ server."""
    global game_state, my_player_id, running, last_message, is_connected
    buffer = ""
    while running:
        try:
            data = sock.recv(4096)
            if not data:
                logging.info("Mất kết nối (server đóng hoặc không gửi dữ liệu).")
                last_message = "Mất kết nối đến server."
                running = False; is_connected = False; break
            buffer += data.decode(ENCODING)

            while '\n' in buffer:
                message_json, buffer = buffer.split('\n', 1)
                if not message_json: continue
                try:
                    message = json.loads(message_json)
                    msg_type = message.get("type")
                    payload = message.get("payload", {})
                    logging.info(">>> ĐÃ NHẬN TIN NHẮN LOẠI: %s <<<", msg_type) # Log message type

                    # Prioritize error handling
                    if msg_type == MSG_TYPE_ERROR:
                        error_msg = payload.get("message", "Lỗi từ server.")
                        logging.error("Lỗi Server: %s", error_msg)
                        last_message = error_msg
                        if "đầy" in error_msg or "bắt đầu" in error_msg or "từ chối" in error_msg or "không tồn tại" in error_msg:
                            disconnect_from_server()
                        continue

                    if msg_type == MSG_TYPE_MOVE_INVALID:
                        reason = payload.get("reason", "Nước đi không hợp lệ.")
                        logging.warning("Server báo: %s", reason)
                        last_message = reason
                        continue

                    # --- Process Status Messages ---
                    with state_lock:
                        if msg_type == MSG_TYPE_YOUR_ID:
                            new_id = payload.get("player_id", -1)
                            if my_player_id == -1:
                                my_player_id = new_id
                                logging.info("*** Bạn được gán ID Người chơi %d (từ YOUR_ID) ***", my_player_id + 1)

                        # --- HANDLE ROOM CREATED ---
                        elif msg_type == "room_created":
                            logging.info("--- Processing 'room_created' message ---")
                            received_room_id = payload.get("room_id")
                            # Sửa lại: Đọc đúng key 'host_id' vì người tạo là host
                            assigned_player_id = payload.get("host_id", -1) 
                            max_p = payload.get("max_players", 0)
                            logging.info("   Payload: room_id=%s, host_id=%s, max_players=%s", received_room_id, assigned_player_id, max_p) # Sửa log
                            # Điều kiện kiểm tra giờ sẽ đúng
                            if received_room_id is not None and assigned_player_id != -1: 
                                my_player_id = assigned_player_id # Cập nhật ID
                                game_state = { # Khởi tạo game_state
                                    'room_id': received_room_id, 'required_players': max_p,
                                    'host_id': my_player_id, 'num_players': 1,
                                    'player_ids': [my_player_id], 'game_started': False,
                                    'dice_value': None, 'players_pieces': [[] for _ in range(max_p)]
                                }
                                last_message = f"Đã tạo phòng {received_room_id}. Chờ..."
                                logging.info("!!! CLIENT CẬP NHẬT ID (room_created): %d !!!", my_player_id + 1)
                            else:
                                logging.error("   Lỗi: Dữ liệu 'room_created' không hợp lệ hoặc thiếu host_id: %s", payload)

                        # --- HANDLE JOINED ROOM ---
                        elif msg_type == "joined_room":
                             logging.info("--- Processing 'joined_room' message ---") # ADDED LOG
                             room_details = payload
                             received_room_id = room_details.get("room_id")
                             server_assigned_id = room_details.get("player_id") # Server sends assigned ID
                             logging.info("   Payload: %s", room_details) # ADDED LOG
                             if server_assigned_id is not None:
                                 # *** UPDATE my_player_id ***
                                 my_player_id = server_assigned_id
                                 logging.info("!!! CLIENT CẬP NHẬT ID (joined_room): %d !!!", my_player_id + 1) # CONFIRMATION LOG
                             else:
                                 logging.error("   Lỗi: Server không gửi player_id trong 'joined_room'.") # ADDED LOG

                             if received_room_id and my_player_id != -1:
                                  game_state = { # Update state
                                       'room_id': received_room_id, 'required_players': room_details.get("max_players"),
                                       'host_id': room_details.get("host_id"), 'num_players': room_details.get("current_players"),
                                       'player_ids': room_details.get("player_ids"), 'game_started': False,
                                       'dice_value': None,'players_pieces': [[] for _ in range(room_details.get("max_players", 0))]
                                  }
                                  last_message = f"Đã vào phòng {received_room_id}. Chờ host..."
                                  logging.info("Client vào phòng %s với ID %d", received_room_id, my_player_id + 1)
                             else:
                                 logging.error("   Lỗi: Dữ liệu 'joined_room' không đầy đủ hoặc ID không hợp lệ.") # ADDED LOG


                        # --- Process other messages ---
                        elif msg_type == MSG_TYPE_GAME_STATE:
                            game_state.update(payload)
                            current_turn = game_state.get('turn', -1)
                            dice_val = game_state.get('dice_value')
                            if game_state.get('game_started', False):
                                if current_turn == my_player_id:
                                    if dice_val is None: last_message = "Đến lượt bạn gieo!"
                                    # Thông báo sau khi gieo
                                    else: last_message = f"Bạn gieo được {dice_val}. Chọn quân!"
                                elif current_turn != -1:
                                    # Lấy giá trị xúc xắc của người chơi khác (nếu có)
                                    if dice_val is not None:
                                        last_message = f"P{current_turn + 1} gieo được {dice_val}. Đang chờ đi..."
                                    else: # Nếu chưa gieo
                                        last_message = f"Đang chờ P{current_turn + 1} gieo..."
                                        
                        elif msg_type == MSG_TYPE_PLAYER_JOINED:
                            room_details = payload
                            if game_state.get('room_id') == room_details.get('room_id'):
                                game_state['num_players'] = room_details.get("current_players")
                                game_state['player_ids'] = room_details.get("player_ids")
                            pid = payload.get("player_id", -1)
                            total = payload.get("current_players", 0)
                            req = payload.get("max_players", '?')
                            if not game_state.get('game_started', False):
                                 last_message = f"Người chơi {pid + 1} vào. ({total}/{req})"
                            logging.info(f"Người chơi {pid + 1} vào phòng {game_state.get('room_id')}. ({total}/{req})")

                        elif msg_type == MSG_TYPE_PLAYER_LEFT:
                            room_details = payload
                            if game_state.get('room_id') == room_details.get('room_id'):
                                game_state['num_players'] = room_details.get("current_players")
                                game_state['player_ids'] = room_details.get("player_ids")
                            pid = payload.get("player_id", -1)
                            last_message = f"Người chơi {pid + 1} thoát."
                            logging.info(last_message)

                except json.JSONDecodeError: logging.error("Lỗi JSON: %s", message_json); buffer = ""
                except Exception as e: logging.exception("Lỗi xử lý thông điệp")

        except socket.timeout: continue
        except OSError as e:
             if running: logging.error("Lỗi socket: %s", e)
             running = False; is_connected = False; break
        except Exception as e:
             if running: logging.exception("Lỗi không xác định")
             running = False; is_connected = False; break

    logging.info("Luồng nhận dữ liệu đã dừng.")
    is_connected = False

    
def send_action(action_data):
    """Gửi hành động (dictionary) lên server."""
    global is_connected, last_message
    if client_socket and is_connected:
        try:
            message = json.dumps(action_data) + '\n'
            client_socket.sendall(message.encode(ENCODING))
            return True # Gửi thành công
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"Lỗi gửi (Mất kết nối?): {e}")
            last_message = "Mất kết nối khi gửi."
            disconnect_from_server() # Tự ngắt kết nối khi không gửi được
            return False
        except Exception as e:
            print(f"Lỗi gửi hành động không xác định: {e}")
            return False
    else:
        print("Không thể gửi: Chưa kết nối.")
        last_message = "Chưa kết nối đến server."
        return False

# --- Các hàm lấy trạng thái (để UI sử dụng) ---
def get_current_game_state():
    with state_lock:
        return game_state.copy() # Trả về bản sao để tránh sửa đổi trực tiếp

def get_my_player_id():
    return my_player_id

def get_last_message():
    return last_message

def is_client_connected():
    return is_connected

