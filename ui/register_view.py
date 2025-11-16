import pygame
import pygame_gui
import logging
from utils.constants import WIDTH, HEIGHT
from core.auth_manager import AuthManager
from utils.ui_utils import draw_gradient_background, get_font

class RegisterView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.auth_manager = AuthManager()
        self.is_running = True
        self.next_screen = None
        self.status_message = "Tạo tài khoản mới (Cần Email hợp lệ)"

        # --- Background Gradient ---
        self.background = pygame.Surface((WIDTH, HEIGHT))
        draw_gradient_background(self.background, (58,123,213), (58,213,195))

        # --- Title ---
        self._draw_title("ĐĂNG KÝ")

        # --- UI Elements ---
        entry_width = 300; entry_height = 40; spacing = 50
        y_start = HEIGHT // 2 - 100
        
        self.username_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start), (entry_width, entry_height)),
            manager=self.manager, placeholder_text='Email hợp lệ'
        )
        self.password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start+60), (entry_width, entry_height)),
            manager=self.manager, placeholder_text='Mật khẩu (>=6 ký tự)',
        )
        self.password_input.set_text_hidden(True)

        self.register_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start+130), (300, 50)),
            text='TẠO TÀI KHOẢN',
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(class_id="#main_button")
        )
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH//2-150, y_start+200), (300, 50)),
            text='QUAY LẠI',
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(class_id="#back_button")
        )
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH//2-200, y_start+270), (400, 30)),
            text=self.status_message, manager=self.manager
        )

    def _draw_title(self, text):
        title_font = get_font(70)
        title_surf = title_font.render(text, True, (255,255,255))
        title_rect = title_surf.get_rect(center=(WIDTH//2, 80))
        # Shadow
        shadow_surf = title_font.render(text, True, (0,0,0))
        shadow_rect = shadow_surf.get_rect(center=(WIDTH//2+3, 83))
        self.background.blit(shadow_surf, shadow_rect)
        self.background.blit(title_surf, title_rect)

    def _show_status(self, message, success=False):
        color = '#3cb371' if success else '#ff4500'
        self.status_label.set_text(f'<font color="{color}">{message}</font>')

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.register_button:
                email = self.username_entry.get_text()
                password = self.password_input.get_text()
                success, message = self.auth_manager.register_user(email, password)
                self._show_status(message, success=success)
                if success:
                    self.is_running = False
                    self.next_screen = 'login'

            elif event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'login'

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0,0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)
