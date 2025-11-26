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
            pygame.image.load('assets/images/board.png').convert(),
            (WIDTH, HEIGHT)
        )
        
        try:
            #self.title_font = pygame.font.SysFont('Arial', 60, bold=True)
            self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 70)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 60)

        title_text = self.title_font.render('CHỌN ĐỘ KHÓ', True, pygame.Color('blue'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        shadow_text = self.title_font.render('CHỌN ĐỘ KHÓ', True, pygame.Color('black'))
        shadow_rect = shadow_text.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 147))
        self.background.blit(shadow_text, shadow_rect)
        self.background.blit(title_text, title_rect)

        self.easy_bot_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 50), (300, 50)),
            text='BOT DỄ',
            manager=self.manager
        )
        self.hard_bot_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 20), (300, 50)),
            text='BOT KHÓ',
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