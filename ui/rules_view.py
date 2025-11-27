# ui/rules_view.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT

class RulesView:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None

        # --- Sử dụng hình nền cho nhất quán ---
        try:
            self.background = pygame.transform.scale(
                pygame.image.load('assets/images/Sanh.png').convert(),
                (WIDTH, HEIGHT)
            )
        except pygame.error:
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill(pygame.Color('#1a1a1a'))
        
        # --- Tiêu đề màn hình ---
        try:
            #self.title_font = pygame.font.SysFont('Arial', 60, bold=True)
            self.title_font = pygame.font.Font('assets/fonts/Sans_Flex.ttf', 70)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 60) # Font dự phòng

        title_text = self.title_font.render('LUẬT CHƠI', True, pygame.Color('yellow'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, 130))
        self.background.blit(title_text, title_rect)

        # --- Nội dung luật chơi (sử dụng định dạng giống HTML) ---
        rules_html_text = (
            "<b>Mục Tiêu:</b>"
            "<br>Là người đầu tiên đưa tất cả <b>4 quân cờ</b> của mình về đến chuồng (đích) an toàn."
            "<br><br>"
            "<b>Bắt Đầu:</b>"
            "<br>- Gieo xúc xắc được <b>6 điểm</b> để được ra một quân cờ từ sân nhà ra ô xuất phát."
            "<br><br>"
            "<b>Di Chuyển:</b>"
            "<br>- Di chuyển quân cờ theo <b>chiều kim đồng hồ</b>, số bước đi bằng đúng số điểm trên xúc xắc."
            "<br><br>"
            "<b>Luật Đặc Biệt:</b>"
            "<br>- <b>Đá quân:</b> Khi quân của bạn đi đến một ô đã có quân của đối phương (không phải ô xuất phát), quân đối phương sẽ bị 'đá' về sân nhà. Bạn sẽ được thưởng <b>thêm một lượt</b> gieo xúc xắc."
            "<br>- <b>Thêm lượt:</b> Gieo được <b>6 điểm</b> sẽ được thưởng thêm một lượt gieo."
            "<br>- <b>Về Đích:</b> Khi đã đi hết một vòng, quân cờ sẽ đi vào đường về đích (đường cùng màu). Bạn phải gieo được số điểm <b>vừa đủ</b> để về các ô trong chuồng, không được đi lố."
        )

        # --- Tạo ô hiển thị văn bản ---
        # Vị trí và kích thước của ô luật chơi
        text_box_rect = pygame.Rect(0, 0, WIDTH - 200, HEIGHT - 350)
        text_box_rect.center = (WIDTH // 2, HEIGHT // 2 + 50)
        
        pygame_gui.elements.UITextBox(
            html_text=rules_html_text,
            relative_rect=text_box_rect,
            manager=self.manager
        )

        # --- Nút quay lại ---
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
            if event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'menu'

        self.manager.process_events(event)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)