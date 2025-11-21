# ui/settings_view.py
import pygame
import pygame_gui
import logging
from utils.constants import WIDTH, HEIGHT

class SettingsView:
    def __init__(self, screen, manager, sound_manager):
        self.screen = screen
        self.manager = manager
        self.sound_manager = sound_manager
        self.is_running = True
        self.next_screen = None

        # --- Nền tổng thể ---
        try:
            self.background = pygame.transform.scale(
                pygame.image.load('assets/images/background.png').convert(), 
                (WIDTH, HEIGHT)
            )
        except pygame.error:
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill(pygame.Color('#1a1a1a'))

        # --- Font tiêu đề ---
        try:
            self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 80)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 60)

        title_text = self.title_font.render('CÀI ĐẶT', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, 80))
        self.background.blit(title_text, title_rect)

        # --- Bố cục chung ---
        setting_y_start = HEIGHT // 2 - 120 
        label_width = 180
        slider_width = 200 
        value_label_width = 60
        slider_height = 25
        row_height = 40 
        start_x_label = WIDTH // 2 - (label_width + slider_width + 20 + value_label_width) // 2
        start_x_slider = start_x_label + label_width + 20
        start_x_value = start_x_slider + slider_width + 10

        # --- Khung trắng bao quanh tất cả slider/label ---
        padding = 20
        top_y = setting_y_start - padding
        bottom_y = setting_y_start + 4 * row_height + slider_height + padding  # 4 slider
        left_x = start_x_label - padding
        right_x = start_x_value + value_label_width + padding

        pygame.draw.rect(
            self.background,
            pygame.Color('white'),
            pygame.Rect(left_x, top_y, right_x - left_x, bottom_y - top_y),
            border_radius=12
        )

        # --- Slider và label ---
        y_pos = setting_y_start

        # --- Nhạc nền ---
        initial_music_volume = self.sound_manager.get_music_volume() if self.sound_manager else 0.5
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_label, y_pos), (label_width, slider_height)),
            text='Nhạc nền:',
            manager=self.manager,
            object_id="#settings_label"
        )
        self.music_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((start_x_slider, y_pos), (slider_width, slider_height)),
            start_value=initial_music_volume,
            value_range=(0.0, 1.0),
            manager=self.manager
        )
        self.music_value_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_value, y_pos), (value_label_width, slider_height)),
            text=f"{int(initial_music_volume * 100)}%",
            manager=self.manager,
            object_id="#settings_value"
        )

        # --- Hiệu ứng (SFX) ---
        y_pos += row_height
        initial_sfx_volume = self.sound_manager.get_sfx_volume() if self.sound_manager else 0.8
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_label, y_pos), (label_width, slider_height)),
            text='Hiệu ứng (SFX):',
            manager=self.manager,
            object_id="#settings_label"
        )
        self.sfx_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((start_x_slider, y_pos), (slider_width, slider_height)),
            start_value=initial_sfx_volume,
            value_range=(0.0, 1.0),
            manager=self.manager
        )
        self.sfx_value_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_value, y_pos), (value_label_width, slider_height)),
            text=f"{int(initial_sfx_volume * 100)}%",
            manager=self.manager,
            object_id="#settings_value"
        )

        # --- Tiếng Xúc Xắc ---
        y_pos += row_height + 10
        is_enabled = self.sound_manager.is_sfx_enabled('dice') if self.sound_manager else True
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_label, y_pos), (label_width, slider_height)),
            text='Tiếng Xúc Xắc:',
            manager=self.manager,
            object_id="#settings_label"
        )
        self.dice_sfx_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((start_x_slider, y_pos), (slider_width, slider_height)),
            start_value=1.0 if is_enabled else 0.0,
            value_range=(0.0, 1.0),
            manager=self.manager
        )
        self.dice_sfx_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_value, y_pos), (value_label_width, slider_height)),
            text="100%" if is_enabled else "0%",
            manager=self.manager,
            object_id="#settings_value"
        )

        # --- Tiếng Di Chuyển ---
        y_pos += row_height
        is_enabled = self.sound_manager.is_sfx_enabled('move') if self.sound_manager else True
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_label, y_pos), (label_width, slider_height)),
            text='Tiếng Di Chuyển:',
            manager=self.manager,
            object_id="#settings_label"
        )
        self.move_sfx_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((start_x_slider, y_pos), (slider_width, slider_height)),
            start_value=1.0 if is_enabled else 0.0,
            value_range=(0.0, 1.0),
            manager=self.manager
        )
        self.move_sfx_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_value, y_pos), (value_label_width, slider_height)),
            text="100%" if is_enabled else "0%",
            manager=self.manager,
            object_id="#settings_value"
        )

        # --- Tiếng Đá Quân ---
        y_pos += row_height
        is_enabled = self.sound_manager.is_sfx_enabled('kick') if self.sound_manager else True
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_label, y_pos), (label_width, slider_height)),
            text='Tiếng Đá Quân:',
            manager=self.manager,
            object_id="#settings_label"
        )
        self.kick_sfx_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((start_x_slider, y_pos), (slider_width, slider_height)),
            start_value=1.0 if is_enabled else 0.0,
            value_range=(0.0, 1.0),
            manager=self.manager
        )
        self.kick_sfx_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((start_x_value, y_pos), (value_label_width, slider_height)),
            text="100%" if is_enabled else "0%",
            manager=self.manager,
            object_id="#settings_value"
        )

        # --- Nút Quay Lại ---
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, HEIGHT - 100), (200, 50)),
            text='QUAY LẠI MENU',
            manager=self.manager,
            object_id='#back_button'
        )

    # --- Xử lý sự kiện ---
    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.music_slider:
                volume = event.value
                self.music_value_label.set_text(f"{int(volume * 100)}%")
                if self.sound_manager: self.sound_manager.set_music_volume(volume)
            elif event.ui_element == self.sfx_slider:
                volume = event.value
                self.sfx_value_label.set_text(f"{int(volume * 100)}%")
                if self.sound_manager: self.sound_manager.set_sfx_volume(volume)
            elif event.ui_element == self.dice_sfx_slider:
                is_now_enabled = event.value > 0.5
                current_state = self.sound_manager.is_sfx_enabled('dice')
                if is_now_enabled != current_state and self.sound_manager:
                    self.sound_manager.toggle_sfx('dice')
                self.dice_sfx_label.set_text("100%" if is_now_enabled else "0%")
            elif event.ui_element == self.move_sfx_slider:
                is_now_enabled = event.value > 0.5
                current_state = self.sound_manager.is_sfx_enabled('move')
                if is_now_enabled != current_state and self.sound_manager:
                    self.sound_manager.toggle_sfx('move')
                self.move_sfx_label.set_text("100%" if is_now_enabled else "0%")
            elif event.ui_element == self.kick_sfx_slider:
                is_now_enabled = event.value > 0.5
                current_state = self.sound_manager.is_sfx_enabled('kick')
                if is_now_enabled != current_state and self.sound_manager:
                    self.sound_manager.toggle_sfx('kick')
                self.kick_sfx_label.set_text("100%" if is_now_enabled else "0%")

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                logging.info("SettingsView: Lưu cài đặt (nếu cần)...")
                self.is_running = False
                self.next_screen = 'menu'

    # --- Vẽ màn hình ---
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)
