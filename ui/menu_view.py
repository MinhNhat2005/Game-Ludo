# ui/menu_view.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT

class MenuView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None

        # --- TẢI HÌNH NỀN VÀ FONT CHỮ ---
        self.background = pygame.transform.scale(
            pygame.image.load('assets/images/background.png').convert(), 
            (WIDTH, HEIGHT)
        )
        self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 80)

        # --- VẼ TIÊU ĐỀ LÊN BACKGROUND ---
        title_text = self.title_font.render('Cờ Cá Ngựa', True, pygame.Color('yellow'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        shadow_text = self.title_font.render('Cờ Cá Ngựa', True, pygame.Color('black'))
        shadow_rect = shadow_text.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 147))
        self.background.blit(shadow_text, shadow_rect)
        self.background.blit(title_text, title_rect)

        # --- KÍCH THƯỚC VÀ VỊ TRÍ NÚT ---
        button_width = 220
        button_height = 50
        spacing_y = 70
        button_y_start = HEIGHT // 2 - (spacing_y * 2) // 2 + 50

        # Hàng trên
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - button_width - 10, button_y_start), (button_width, button_height)),
            text='CHƠI NGAY',
            manager=self.manager
        )
        self.rules_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 + 10, button_y_start), (button_width, button_height)),
            text='LUẬT CHƠI',
            manager=self.manager
        )

        # Hàng giữa
        self.settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - button_width - 10, button_y_start + spacing_y), (button_width, button_height)),
            text='CÀI ĐẶT',
            manager=self.manager
        )
        self.history_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 + 10, button_y_start + spacing_y), (button_width, button_height)),
            text='LỊCH SỬ',
            manager=self.manager
        )

        # Hàng dưới (THOÁT GAME nằm giữa, màu đỏ)
        self.exit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - button_width // 2, button_y_start + spacing_y * 2), (button_width, button_height)),
            text='THOÁT GAME',
            manager=self.manager,
            object_id="#exit_button"
        )

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.play_button:
                self.is_running = False
                self.next_screen = 'mode_select'
            elif event.ui_element == self.rules_button:
                self.is_running = False
                self.next_screen = 'rules'
            elif event.ui_element == self.settings_button:
                self.is_running = False
                self.next_screen = 'settings'
            elif event.ui_element == self.history_button:
                self.is_running = False
                self.next_screen = 'history'
            elif event.ui_element == self.exit_button:
                self.is_running = False
                self.next_screen = 'exit'

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)
