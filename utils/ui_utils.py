import pygame

def draw_gradient_background(surface, color_top, color_bottom):
    """Vẽ gradient từ trên xuống dưới"""
    height = surface.get_height()
    width = surface.get_width()
    for y in range(height):
        ratio = y / height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def get_font(size=60):
    """Font Unicode-safe, fallback nếu không tìm thấy .ttf"""
    try:
        return pygame.font.Font('assets/fonts/NotoSans-Regular.ttf', size)
    except FileNotFoundError:
        return pygame.font.Font(pygame.font.get_default_font(), size)
