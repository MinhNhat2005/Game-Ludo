# ui/bot_selection_view.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT

class BotSelectionView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None
        self.bot_difficulty = None # Sẽ lưu độ khó được chọn

        self.background = pygame.transform.scale(
            pygame.image.load('assets/images/background.png').convert(),
            (WIDTH, HEIGHT)
        )
        
        try:
            #self.title_font = pygame.font.SysFont('Arial', 60, bold=True)
            self.title_font = pygame.font.Font('assets/fonts/title_font.ttf', 60)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 60)

        title_text = self.title_font.render('CHỌN ĐỘ KHÓ', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        shadow_text = self.title_font.render('CHỌN ĐỘ KHÓ', True, pygame.Color('black'))
        shadow_rect = shadow_text.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 147))
        self.background.blit(shadow_text, shadow_rect)
        self.background.blit(title_text, title_rect)

        self.easy_bot_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 50), (300, 50)),
            text='BOT DỄ (NGẪU NHIÊN)',
            manager=self.manager
        )
        self.hard_bot_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 20), (300, 50)),
            text='BOT KHÓ (SẮP CÓ)',
            manager=self.manager
        )
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((30, HEIGHT - 80), (150, 50)),
            text='QUAY LẠI',
            manager=self.manager,
            object_id='#back_button'
        )

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.easy_bot_button:
                self.bot_difficulty = 'bot_easy' # <- Gửi tín hiệu 'bot_easy'
                self.is_running = False
                self.next_screen = 'game'
            if event.ui_element == self.hard_bot_button:
                self.bot_difficulty = 'bot_hard' # <- Gửi tín hiệu 'bot_hard'
                self.is_running = False
                self.next_screen = 'game'
            if event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'mode_select'

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)