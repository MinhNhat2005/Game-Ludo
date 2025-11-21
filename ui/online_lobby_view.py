# ui/online_lobby_view.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT

class OnlineLobbyView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None

        # --- Giao diện ---
        self.background = pygame.transform.scale(
            pygame.image.load('assets/images/background.png').convert(),
            (WIDTH, HEIGHT)
        )
        
        # Luôn load từ file, không dùng SysFont
        self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 60)

        title_text = self.title_font.render('CHƠI ONLINE', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))

        # Hiệu ứng đổ bóng
        shadow_text = self.title_font.render('CHƠI ONLINE', True, pygame.Color('black'))
        shadow_rect = shadow_text.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 147))

        self.background.blit(shadow_text, shadow_rect)
        self.background.blit(title_text, title_rect)


        # --- Các nút lựa chọn ---
        button_width = 300
        button_height = 50
        
        self.create_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 50), (button_width, button_height)),
            text='TẠO PHÒNG MỚI',
            manager=self.manager
        )
        self.join_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 20), (button_width, button_height)),
            text='VÀO PHÒNG BẰNG ID',
            manager=self.manager
        )

        # --- Nút Quay Lại ---
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((30, HEIGHT - 80), (150, 50)),
            text='QUAY LẠI',
            manager=self.manager,
            object_id='#back_button' 
        )

    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.create_button:
                self.is_running = False
                self.next_screen = 'create_room' # Tín hiệu đến màn hình tạo phòng
            elif event.ui_element == self.join_button:
                self.is_running = False
                self.next_screen = 'join_room' # Tín hiệu đến màn hình vào phòng
            elif event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'mode_select' # Quay lại chọn chế độ

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)