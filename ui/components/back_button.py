# ui/components/back_button.py
import pygame
import pygame_gui

class BackButton:
    def __init__(self, manager, x=20, y=20):
        self.manager = manager

        # Tải icon back.jpg
        self.icon = pygame.image.load("assets/icons/back.jpg")
        self.icon = pygame.transform.scale(self.icon, (28, 28))

        # Nút GUI
        self.button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x, y, 140, 42),
            text="   Quay Lại",  # chừa chỗ cho icon
            manager=self.manager,
            object_id="#back_button"
        )

    def draw(self, surface):
        # Vẽ icon vào trong nút
        btn_rect = self.button.rect
        surface.blit(self.icon, (btn_rect.x + 8, btn_rect.y + 7))

    def is_pressed(self, event):
        return (
            event.type == pygame_gui.UI_BUTTON_PRESSED
            and event.ui_element == self.button
        )
