# utils/constants.py
import pygame
pygame.font.init()

WIDTH, HEIGHT = 1100, 830
CENTER = (WIDTH//2, HEIGHT//2)
CELL = 50

MAX_PLAYERS = 4 # Số người chơi tối đa cho online

# màu sắc
RED = (220,50,50)
BLUE = (60,90,230)
GREEN = (50,180,80)
YELLOW = (230,200,40)
WHITE = (255,255,255)
BLACK = (0,0,0)

PLAYER_COLORS = [GREEN, BLUE, YELLOW, RED]  # theo chiều kim đồng hồ

FONT = pygame.font.SysFont("Arial", 18)
BIG_FONT = pygame.font.SysFont("Arial", 22, bold=True)

# vị trí xúc xắc (x,y)
# vị trí xúc xắc (x,y)
# vị trí xúc xắc (x,y)

DICE_POSITIONS = {
    0: (50, 50),                   # Xanh lá (bắt đầu trước) - góc trên trái
    1: (WIDTH - 100, 50),          # Xanh dương - góc trên phải
    2: (WIDTH - 100, HEIGHT - 100),# Vàng - góc dưới phải
    3: (50, HEIGHT - 100)          # Đỏ - góc dưới trái
}

