# ui/player_selection_view.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT

class PlayerSelectionView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None
        self.num_players = 0 # Sẽ lưu số người chơi được chọn

        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill(pygame.Color('#1a1a1a'))
        
        title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 80)
        title_text = title_font.render('CHỌN SỐ NGƯỜI CHƠI', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        self.background.blit(title_text, title_rect)

        # Tạo các nút bấm chọn số người chơi
        self.two_players_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 50), (300, 50)),
            text='2 NGƯỜI CHƠI',
            manager=self.manager
        )
        self.three_players_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 20), (300, 50)),
            text='3 NGƯỜI CHƠI',
            manager=self.manager
        )
        self.four_players_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 90), (300, 50)),
            text='4 NGƯỜI CHƠI',
            manager=self.manager
        )
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((30, HEIGHT - 80), (150, 50)),
            text='QUAY LẠI',
            manager=self.manager
        )

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.two_players_button:
                self.num_players = 2
                self.is_running = False
                self.next_screen = 'game'
            if event.ui_element == self.three_players_button:
                self.num_players = 3
                self.is_running = False
                self.next_screen = 'game'
            if event.ui_element == self.four_players_button:
                self.num_players = 4
                self.is_running = False
                self.next_screen = 'game'
            if event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'mode_select' # Quay lại màn hình chọn chế độ

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)