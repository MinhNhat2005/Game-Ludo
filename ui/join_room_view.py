# ui/join_room_view.py
import pygame
import pygame_gui
import logging
from utils.constants import WIDTH, HEIGHT
from network import client # Import client để kết nối và lấy trạng thái
from network.protocol import *

class JoinRoomView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None
        self.connection_status = "Nhập ID Phòng và Tham Gia"

        # --- Giao diện ---
        self.background = pygame.transform.scale(
            pygame.image.load('assets/images/black.png').convert(),
            (WIDTH, HEIGHT)
        )
        
        try:
            self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 80)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 60) 

        title_text = self.title_font.render('VÀO PHÒNG', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, 150))
        self.background.blit(title_text, title_rect)

        # --- Ô nhập ID Phòng ---
        self.room_id_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 80), (300, 50)),
            manager=self.manager,
            placeholder_text='Nhập ID Phòng...'
        )

        # --- Nút Tham Gia ---
        self.join_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 10), (300, 50)),
            text='THAM GIA',
            manager=self.manager
        )

        # --- Hiển thị Trạng thái ---
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH // 2 - 200, HEIGHT // 2 + 60), (400, 30)),
            text=self.connection_status,
            manager=self.manager
        )

       # --- Nút quay lại ---
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, HEIGHT - 100), (200, 50)),
            text='QUAY LẠI',
            manager=self.manager,
            object_id='#back_button'
        )

        # --- Thêm icon nhỏ bên trái nút ---
        back_icon = pygame.image.load("assets/images/back.jpg").convert_alpha()
        back_icon = pygame.transform.smoothscale(back_icon, (20, 20))  # icon nhỏ

        # Icon đặt sát chữ, căn giữa theo chiều cao nút
        icon_x = (WIDTH // 2 - 100) + 10  # cách mép trái nút 10px
        icon_y = (HEIGHT - 100) + (50 - 20) // 2  # căn giữa theo chiều cao nút
        self.back_icon_image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((icon_x, icon_y), (20, 20)),
            image_surface=back_icon,
            manager=self.manager
        )


    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.join_button:
                room_id = self.room_id_entry.get_text().strip().upper() 
                if room_id:
                    self.connection_status = f"Đang kết nối đến server..."
                    self.status_label.set_text(self.connection_status)
                    
                    # Bước 1: Kết nối đến server chính (nếu chưa kết nối)
                    if not client.is_client_connected():
                         # Lấy IP server từ đâu đó (ví dụ: config hoặc ô nhập riêng)
                         # Hiện tại vẫn dùng IP mặc định trong client.py
                         if not client.connect_to_server(client.SERVER_IP):
                              self.connection_status = client.get_last_message()
                              self.status_label.set_text(self.connection_status)
                              return # Dừng lại nếu không kết nối được server

                    # Bước 2: Gửi yêu cầu vào phòng
                    self.connection_status = f"Đang vào phòng {room_id}..."
                    self.status_label.set_text(self.connection_status)
                    client.send_action({"type": "join_room", "payload": {"room_id": room_id}})
                    # Chờ server phản hồi qua luồng receive_updates

                else:
                    self.connection_status = "Vui lòng nhập ID Phòng!"
                    self.status_label.set_text(self.connection_status)

            elif event.ui_element == self.back_button:
                 client.disconnect_from_server() # Ngắt kết nối nếu đang kết nối
                 self.is_running = False
                 self.next_screen = 'online_lobby' 

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    # Trong file ui/join_room_view.py

    def update(self, time_delta):
        self.manager.update(time_delta)
        
        # Cập nhật hiển thị (ví dụ: danh sách người chơi trong CreateRoomView)
        if hasattr(self, '_update_display_from_state'):
            self._update_display_from_state()
        # Cập nhật status label trong JoinRoomView
        elif hasattr(self, 'status_label'):
            current_msg = client.get_last_message()
            if current_msg != self.connection_status:
                self.connection_status = current_msg
                self.status_label.set_text(self.connection_status)

        # --- KIỂM TRA TRẠNG THÁI GAME ĐÃ BẮT ĐẦU ---
        try: # Thêm try-except để bắt lỗi tiềm ẩn khi đọc state
            game_state = client.get_current_game_state()
            if game_state: # Chỉ kiểm tra nếu game_state không rỗng
                game_has_started = game_state.get('game_started', False)
                logging.debug("%s - Checking game_started: %s", self.__class__.__name__, game_has_started) # Log kiểm tra

                # Nếu game đã bắt đầu -> Chuyển màn hình
                if game_has_started:
                    logging.info("%s: Server báo game đã bắt đầu, chuyển màn hình...", self.__class__.__name__)
                    self.is_running = False
                    self.next_screen = 'network_game'
                # Cập nhật trạng thái chờ trong JoinRoomView (nếu chưa bắt đầu)
                elif isinstance(self, JoinRoomView) and client.get_my_player_id() != -1 and game_state.get('room_id') and "Đã vào phòng" not in self.connection_status:
                    logging.info("JoinRoomView: Đã vào phòng %s, chờ host...", game_state.get('room_id'))
                    self.connection_status = f"Đã vào phòng {game_state.get('room_id')}. Chờ host..."
                    self.status_label.set_text(self.connection_status)
                    if self.join_button.is_enabled: self.join_button.disable()
                    if self.room_id_entry.is_enabled: self.room_id_entry.disable()
            else:
                logging.debug("%s - Game state is empty, cannot check game_started.", self.__class__.__name__)

        except Exception as e:
            logging.exception("%s - Lỗi trong hàm update khi kiểm tra game_started", self.__class__.__name__) # Log lỗi
        # ----------------------------------------------