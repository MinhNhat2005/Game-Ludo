# ui/settings_view.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT

class SettingsView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None

        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill(pygame.Color('#1a1a1a'))
        
        font = pygame.font.Font(None, 50)
        text = font.render('Cài Đặt (Sắp có)', True, pygame.Color('white'))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        self.background.blit(text, text_rect)

        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, HEIGHT // 2 + 20), (200, 50)),
            text='QUAY LẠI',
            manager=self.manager
        )

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'menu'

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)