import pygame
import pygame_gui
from utils import firebase_manager
from utils.constants import WIDTH, HEIGHT
from datetime import datetime

class HistoryUI:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None

        # --- Nền ---
        try:
            bg = pygame.image.load("assets/images/Sanh.png").convert()
            self.background = pygame.transform.scale(bg, (WIDTH, HEIGHT))
        except pygame.error:
            # fallback nếu không có ảnh nền
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((30, 30, 30))

        # --- Tiêu đề LỊCH SỬ ---
        try:
            self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 50)
        except:
            self.title_font = pygame.font.Font(None, 50) 
            
        title_text = self.title_font.render('LỊCH SỬ', True, pygame.Color('yellow'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, 50)) 
        
        shadow_text = self.title_font.render('LỊCH SỬ', True, pygame.Color('black'))
        shadow_rect = shadow_text.get_rect(center=(WIDTH // 2 + 2, 52))
        
        self.background.blit(shadow_text, shadow_rect)
        self.background.blit(title_text, title_rect)

        # --- Nút quay lại ---
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, HEIGHT - 100), (200, 50)),
            text='QUAY LẠI',
            manager=self.manager,
            object_id='#back_button'
        )

        # Icon nhỏ bên trái nút
        back_icon = pygame.image.load("assets/images/back.jpg").convert_alpha()
        back_icon = pygame.transform.smoothscale(back_icon, (20, 20))
        icon_x = (WIDTH // 2 - 100) + 10
        icon_y = (HEIGHT - 100) + (50 - 20) // 2
        self.back_icon_image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((icon_x, icon_y), (20, 20)),
            image_surface=back_icon,
            manager=self.manager
        )

        # --- Lấy lịch sử và lọc trùng lặp ---
        raw_history = firebase_manager.get_match_history(limit=100)
        unique_matches = {}
        for match in raw_history:
            match_id = match.get('MatchID')
            if match_id:
                # Nếu đã có, chỉ giữ bản kết thúc
                if match_id in unique_matches:
                    if not unique_matches[match_id]['is_loadable'] and match.get('is_loadable'):
                        continue
                    if unique_matches[match_id]['is_loadable'] and not match.get('is_loadable'):
                        unique_matches[match_id] = match
                else:
                    unique_matches[match_id] = match
        self.history_data = list(unique_matches.values())

        # --- Scroll container ---
        scroll_top = 100 
        scroll_bottom = HEIGHT - 100 
        container_height = scroll_bottom - scroll_top
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((50, scroll_top, WIDTH - 100, container_height)),
            manager=self.manager
        )
        
        # --- Tạo nút lịch sử & Xóa ---
        self.buttons = []
        self.delete_buttons = {}
        button_height = 50
        spacing = 10
        delete_button_width = 50
        main_button_width = self.scroll_container.relative_rect.width - 20 - delete_button_width - spacing
        date_format_in = '%Y-%m-%d %H:%M:%S'

        for i, match in enumerate(self.history_data):
            match_id = match['MatchID']
            status = "Đang chơi" if match.get('is_loadable') else "Kết thúc"
            mode = match.get('Mode', 'Offline')

            # Xử lý WinnerPlayerID đúng
            winner_id = match.get('WinnerPlayerID')
            if winner_id is None or winner_id == '-':
                winner = 'Chưa xác định'
            else:
                winner_id = int(winner_id)
                if winner_id < match.get('NumPlayers', 0):
                    if mode == 'Bot' and winner_id != 0:
                        winner = f'Bot {winner_id}'
                    elif mode == 'Bot' and winner_id == 0:
                        winner = 'Player 1'
                    else:
                        winner = f'Player {winner_id + 1}'
                else:
                    winner = 'Chưa xác định'

            # Xử lý thời gian
            timestamp_str = match.get('StartTime')
            dt_str = '-'
            if isinstance(timestamp_str, str) and timestamp_str:
                try:
                    dt_object = datetime.strptime(timestamp_str, date_format_in)
                    dt_str = dt_object.strftime('%d/%m/%Y %H:%M:%S')
                except ValueError:
                    dt_str = 'Lỗi định dạng'

            text = f"ID: {match_id} | Mode: {mode} | Status: {status} | Winner: {winner} | Thời gian: {dt_str}"

            # Nút chính
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (0, i*(button_height + spacing), main_button_width, button_height)
                ),
                text=text,
                manager=self.manager,
                container=self.scroll_container,
                object_id="#history_item"
            )
            self.buttons.append(btn)

            # Nút xóa
            delete_btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (main_button_width + spacing, i*(button_height + spacing), delete_button_width, button_height)
                ),
                text='Xóa',
                manager=self.manager,
                container=self.scroll_container,
                object_id="#delete_history_item"
            )
            self.delete_buttons[delete_btn] = match_id

        # --- Cập nhật scroll ---
        total_height = len(self.history_data) * (button_height + spacing)
        self.scroll_container.set_scrollable_area_dimensions((self.scroll_container.relative_rect.width, total_height))


    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'menu'
            
            # XỬ LÝ SỰ KIỆN XÓA
            elif event.ui_element in self.delete_buttons:
                match_id_to_delete = self.delete_buttons[event.ui_element]
                
                # Gọi hàm xóa dữ liệu khỏi Firebase
                firebase_manager.delete_match_history(match_id_to_delete)
                print(f"Đã xóa lịch sử trận đấu: {match_id_to_delete}")
                
                # Tải lại màn hình lịch sử để cập nhật giao diện
                self.is_running = False
                self.next_screen = 'history' 
                
            # XỬ LÝ SỰ KIỆN NÚT CHÍNH (Tiếp tục/Xem lại)
            else:
                for i, btn in enumerate(self.buttons):
                    if event.ui_element == btn:
                        match = self.history_data[i]
                        match_id = match['MatchID']
                        
                        # Tải trạng thái game
                        final_state = firebase_manager.load_game_state(match_id)
                        
                        if final_state:
                            if match.get('is_loadable'):
                                # Trận Đang chơi -> Tiếp tục
                                self.next_screen = ('resume_game', match_id, final_state)
                            else:
                                # Trận Kết thúc -> Xem lại (view)
                                self.next_screen = ('view_game', match_id, final_state) 
                            
                            self.is_running = False
                        else:
                            print(f"Lỗi: Không thể tải trạng thái trận đấu {match_id}.")

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)