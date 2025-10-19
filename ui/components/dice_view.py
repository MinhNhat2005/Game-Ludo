# ui/components/dice_view.py
import pygame
import random
from utils.constants import WHITE

class DiceView:
    def __init__(self, x, y, color, player_id):
        self.x = x
        self.y = y
        self.color = color
        self.player_id = player_id
        self.value = 1  # Bắt đầu với mặt 1
        self.active = False
        self.size = 50
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.dot_radius = 5

    def roll(self):
        """Tung xúc xắc và trả về giá trị."""
        self.value = random.randint(1, 6)
        return self.value

    def set_value(self, num):
        """Đặt giá trị cho xúc xắc (dùng cho bot)."""
        if 1 <= num <= 6:
            self.value = num

    def clicked(self, pos):
        """Kiểm tra xem người chơi có click vào xúc xắc không."""
        return self.rect.collidepoint(pos)

    def draw(self, screen):
        """Vẽ xúc xắc và các chấm."""
        # Vẽ viền nếu là lượt của người chơi
        if self.active:
            pygame.draw.rect(screen, (255, 200, 0), self.rect.inflate(10, 10), 4, border_radius=5)

        # Vẽ nền xúc xắc
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        
        # Tọa độ các chấm trên mặt xúc xắc
        center = self.size // 2
        quarter = self.size // 4
        three_quarter = self.size * 3 // 4
        
        dot_positions = []
        if self.value == 1:
            dot_positions = [(center, center)]
        elif self.value == 2:
            dot_positions = [(quarter, quarter), (three_quarter, three_quarter)]
        elif self.value == 3:
            dot_positions = [(quarter, quarter), (center, center), (three_quarter, three_quarter)]
        elif self.value == 4:
            dot_positions = [(quarter, quarter), (three_quarter, quarter), (quarter, three_quarter), (three_quarter, three_quarter)]
        elif self.value == 5:
            dot_positions = [(quarter, quarter), (three_quarter, quarter), (center, center), (quarter, three_quarter), (three_quarter, three_quarter)]
        elif self.value == 6:
            dot_positions = [(quarter, quarter), (three_quarter, quarter), (quarter, center), (three_quarter, center), (quarter, three_quarter), (three_quarter, three_quarter)]

        for pos in dot_positions:
            pygame.draw.circle(screen, WHITE, (self.x + pos[0], self.y + pos[1]), self.dot_radius)