# ui/create_room_view.py
import pygame
import pygame_gui
import random
from utils.constants import WIDTH, HEIGHT
from network import client
from network.protocol import *
import logging

class CreateRoomView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None
        self.room_id = None # Sẽ hiển thị khi server phản hồi
        self.max_players = 2 # Mặc định là 2
        self.current_players = 0
        self.player_ids = []
        self.is_host = False
        self.status_message = "Chọn số người chơi và Xác nhận"

        # --- Giao diện ---
        self.background = pygame.transform.scale(
            pygame.image.load('assets/images/black.png').convert(),
            (WIDTH, HEIGHT)
        
        )
        try:
            self.title_font = pygame.font.Font('assets/fonts/title_font.ttf', 80)
        except pygame.error: self.title_font = pygame.font.Font(None, 50)
        title_text = self.title_font.render('TẠO PHÒNG MỚI', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        self.background.blit(title_text, title_rect)

        # --- Hiển thị ID Phòng (Chỉ hiển thị sau khi tạo) ---
        self.id_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH // 2 - 200, 160), (400, 40)),
            text='Mã Phòng: (Chờ tạo)', manager=self.manager, object_id='@room_id_label'
        )

        # --- Lựa chọn số người chơi ---
        label_font_size = 30
        try: label_font = pygame.font.SysFont('Arial', label_font_size)
        except: label_font = pygame.font.Font(None, label_font_size)
        label_text_surf = label_font.render('Số người chơi tối đa:', True, pygame.Color('white'))
        label_text_rect = label_text_surf.get_rect(midright=(WIDTH // 2 - 20, 240))
        self.background.blit(label_text_surf, label_text_rect)
        button_width, button_height = 100, 40
        self.two_players_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 5, 220), (button_width, button_height)),
            text='2 NGƯỜI', manager=self.manager
        )
        self.four_players_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 + button_width + 15, 220), (button_width, button_height)),
            text='4 NGƯỜI', manager=self.manager
        )
        self.two_players_button.select()

        # --- Nút Xác Nhận Tạo Phòng ---
        self.confirm_create_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 50), (300, 50)),
            text='XÁC NHẬN TẠO PHÒNG',
            manager=self.manager
        )
        # Ban đầu vô hiệu hóa, chờ kết nối server
        self.confirm_create_button.disable()

        # --- Hiển thị danh sách/trạng thái (chỉ hiện sau khi tạo) ---
        self.player_list_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH // 2 - 200, HEIGHT // 2 + 10), (400, 30)),
            text="", # Ban đầu ẩn
            manager=self.manager
        )
        self.player_list_label.hide() # Ẩn đi

        # --- Nút Bắt Đầu (Chỉ hiện sau khi tạo) ---
        self.start_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 70), (300, 50)),
            text='BẮT ĐẦU GAME', manager=self.manager
        )
        self.start_button.disable()
        self.start_button.hide() # Ẩn đi

        # --- Nút Hủy / Quay Lại ---
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((30, HEIGHT - 80), (150, 50)),
            text='QUAY LẠI', # Đổi text thành Quay Lại ban đầu
            manager=self.manager, object_id='#back_button'
        )
        
        # --- Hiển thị trạng thái kết nối/lỗi ---
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH // 2 - 200, HEIGHT - 120), (400, 30)),
            text=self.status_message,
            manager=self.manager
        )


        # --- Kết nối Server khi vào màn hình ---
        if not client.is_client_connected():
            self.status_message = "Đang kết nối server..."
            self.status_label.set_text(self.status_message)
            # Dùng IP mặc định trong client.py
            if client.connect_to_server(client.SERVER_IP):
                self.status_message = "Kết nối thành công! Chọn số người chơi."
                self.status_label.set_text(self.status_message)
                self.confirm_create_button.enable() # Kích hoạt nút xác nhận
            else:
                self.status_message = f"Lỗi kết nối: {client.get_last_message()}"
                self.status_label.set_text(self.status_message)
        else:
            # Đã kết nối từ trước
             self.status_message = "Chọn số người chơi và Xác nhận"
             self.status_label.set_text(self.status_message)
             self.confirm_create_button.enable() # Kích hoạt nút xác nhận


    def handle_events(self, event):
        self.manager.process_events(event)
        my_id = client.get_my_player_id()
        # Chỉ host mới đổi được số người (và chỉ trước khi game bắt đầu)
        is_host_before_game = (self.room_id is not None and my_id == 0 and not client.get_current_game_state().get('game_started', False))

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.two_players_button and self.room_id is None: # Chỉ cho chọn trước khi tạo phòng
                self.max_players = 2
                self.two_players_button.select()
                self.four_players_button.unselect()
            elif event.ui_element == self.four_players_button and self.room_id is None:
                self.max_players = 4
                self.four_players_button.select()
                self.two_players_button.unselect()

            elif event.ui_element == self.confirm_create_button:
                # Gửi yêu cầu tạo phòng VỚI SỐ NGƯỜI ĐÃ CHỌN
                print(f"CreateRoomView: Gửi yêu cầu tạo phòng {self.max_players} người...")
                self.status_message = "Đang tạo phòng..."
                self.status_label.set_text(self.status_message)
                success = client.send_action({"type": "create_room", "payload": {"max_players": self.max_players}})
                if success:
                    # Vô hiệu hóa các nút chọn và nút xác nhận sau khi gửi
                    self.two_players_button.disable()
                    self.four_players_button.disable()
                    self.confirm_create_button.disable()
                    self.confirm_create_button.set_text("ĐANG CHỜ PHẢN HỒI...")
                    self.back_button.set_text("HỦY PHÒNG") # Đổi nút Quay lại thành Hủy
                else:
                    self.status_message = f"Lỗi gửi yêu cầu: {client.get_last_message()}"
                    self.status_label.set_text(self.status_message)

            elif event.ui_element == self.start_button and is_host_before_game:
                print("Host: Gửi yêu cầu bắt đầu game!")
                client.send_action({"type": "start_game"})

            elif event.ui_element == self.back_button:
                print("CreateRoomView: Quay lại / Hủy phòng...")
                client.disconnect_from_server() # Ngắt kết nối khi rời màn hình này
                self.is_running = False
                # Quay lại màn hình trước đó (online_lobby hoặc mode_select tùy luồng)
                self.next_screen = 'online_lobby' if self.room_id else 'mode_select'

    def _update_display_from_state(self):
         """Cập nhật giao diện dựa trên trạng thái từ client module."""
         game_state = client.get_current_game_state()
         last_msg = client.get_last_message()
         my_id = client.get_my_player_id()

         # Chỉ cập nhật nếu đã kết nối
         if not client.is_client_connected():
              if "Lỗi kết nối" not in self.status_message: # Tránh ghi đè lỗi ban đầu
                   self.status_message = f"Lỗi: {last_msg}"
                   self.status_label.set_text(self.status_message)
              return

         # Cập nhật ID phòng khi nhận được từ server
         received_room_id = game_state.get('room_id')
         if received_room_id and self.room_id != received_room_id:
              self.room_id = received_room_id
              self.id_label.set_text(f'Mã Phòng: {self.room_id}')
              # Hiển thị các thành phần chờ
              self.player_list_label.show()
              self.start_button.show()
              self.confirm_create_button.hide() # Ẩn nút xác nhận
              self.status_label.hide() # Ẩn trạng thái kết nối ban đầu

         # Chỉ cập nhật thông tin người chơi nếu đã có ID phòng
         if self.room_id and self.room_id != "Đang tạo...":
            self.current_players = game_state.get('num_players', self.current_players)
            self.max_players = game_state.get('required_players', self.max_players)
            self.player_ids = game_state.get('player_ids', self.player_ids if self.player_ids else [])
            self.is_host = (my_id == game_state.get('host_id', -1))

            player_list_str = f"Người chơi ({self.current_players}/{self.max_players}): "
            player_list_str += ", ".join([f"P{pid+1}{'(Bạn)' if pid == my_id else ''}{'(Host)' if pid == game_state.get('host_id', -1) else ''}"
                                        for pid in sorted(self.player_ids)])
            self.player_list_label.set_text(player_list_str)

            # Kích hoạt nút Start nếu đủ người và là host
            can_start = self.is_host and self.current_players == self.max_players
            if can_start:
                 if not self.start_button.is_enabled:
                      self.start_button.enable(); self.start_button.set_text('BẮT ĐẦU GAME')
            else:
                 if self.start_button.is_enabled:
                      self.start_button.disable(); self.start_button.set_text('BẮT ĐẦU GAME (Chờ đủ người)')


    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    # Trong file ui/create_room_view.py

    # Trong file ui/create_room_view.py

    def update(self, time_delta):
        self.manager.update(time_delta)
        # Liên tục cập nhật hiển thị
        self._update_display_from_state()

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
            else:
                 logging.debug("%s - Game state is empty, cannot check game_started.", self.__class__.__name__)

        except Exception as e:
             logging.exception("%s - Lỗi trong hàm update khi kiểm tra game_started", self.__class__.__name__) # Log lỗi
        # ----------------------------------------------