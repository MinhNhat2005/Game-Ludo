# utils/ui_utils.py
import pygame
from pathlib import Path

def get_font(size):
    """Trả về font pygame đúng với size."""
    font_path = Path(__file__).parent.parent / 'assets/fonts/Sans_Flex.ttf'
    try:
        return pygame.font.Font(str(font_path), size)
    except FileNotFoundError:
        print(f"WARNING: Font không tìm thấy tại {font_path}, dùng default font")
        return pygame.font.SysFont(None, size)

def draw_gradient_background(surface, top_color, bottom_color):
    """Vẽ gradient lên surface."""
    height = surface.get_height()
    for y in range(height):
        ratio = y / height
        color = (
            int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio),
            int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio),
            int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio),
        )
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))
