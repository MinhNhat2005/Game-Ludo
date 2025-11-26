import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT
from core.auth_manager import AuthManager
from utils.ui_utils import draw_gradient_background, get_font

class LoginView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.auth_manager = AuthManager()
        self.is_running = True
        self.next_screen = None
        self.user_id = None
        self.status_message = "Nhập Email và mật khẩu"

        # Placeholder text
        self.username_placeholder = "Nhập Email..."
        self.password_placeholder = "Nhập mật khẩu..."
        self.placeholder_font = get_font(20)  # font cho placeholder text, không đậm

        # Background gradient
        self.background = pygame.Surface((WIDTH, HEIGHT))
        draw_gradient_background(self.background, (255,140,0), (255,215,0))  # cam→vàng

        # Title
        self._draw_title("ĐĂNG NHẬP")

        # UI
        entry_width = 300
        entry_height = 40
        y_start = HEIGHT // 2 - 100

        self.username_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start), (entry_width, entry_height)),
            manager=self.manager
        )
        self.password_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start+60), (entry_width, entry_height)),
            manager=self.manager
        )
        self.password_entry.set_text_hidden(True)

        # Buttons
        self.login_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start+130), (300,50)),
            text='ĐĂNG NHẬP',
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(class_id="#main_button")
        )
        self.register_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start+200), (300,50)),
            text='ĐĂNG KÝ',
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(class_id="#back_button")
        )

        # Status label
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH//2-200, y_start+270), (400,30)),
            text=self.status_message,
            manager=self.manager
        )

    def _draw_title(self, text):
        title_font = get_font(70)
        title_surf = title_font.render(text, True, (255,255,255))
        shadow_surf = title_font.render(text, True, (0,0,0))
        title_rect = title_surf.get_rect(center=(WIDTH//2,80))
        shadow_rect = shadow_surf.get_rect(center=(WIDTH//2+3,83))
        self.background.blit(shadow_surf, shadow_rect)
        self.background.blit(title_surf, title_rect)

    def _show_status(self, message, success=False):
        color = '#3cb371' if success else '#ff4500'
        self.status_label.set_text(f'<font color="{color}">{message}</font>')

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            email = self.username_entry.get_text()
            password = self.password_entry.get_text()
            if event.ui_element == self.login_button:
                success, user_uid, message = self.auth_manager.login_user(email, password)
                if success:
                    self.user_id = user_uid
                    self.is_running = False
                    self.next_screen = 'menu'
                else:
                    self._show_status(message, success=False)
            elif event.ui_element == self.register_button:
                self.is_running = False
                self.next_screen = 'register'

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0,0))
        self.manager.draw_ui(self.screen)

        # Vẽ placeholder text cho email & password nếu rỗng
        placeholder_color = (180, 180, 180)
        if self.username_entry.get_text() == "":
            surf = self.placeholder_font.render(self.username_placeholder, True, placeholder_color)
            x = self.username_entry.relative_rect.x + 5
            y = self.username_entry.relative_rect.y + (self.username_entry.relative_rect.height - surf.get_height()) // 2
            self.screen.blit(surf, (x, y))
        if self.password_entry.get_text() == "":
            surf = self.placeholder_font.render(self.password_placeholder, True, placeholder_color)
            x = self.password_entry.relative_rect.x + 5
            y = self.password_entry.relative_rect.y + (self.password_entry.relative_rect.height - surf.get_height()) // 2
            self.screen.blit(surf, (x, y))

    def update(self, time_delta):
        self.manager.update(time_delta)
