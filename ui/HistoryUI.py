# ui/history_ui.py
import pygame
import pygame_gui
from utils import firebase_manager
from utils.constants import WIDTH, HEIGHT

class HistoryUI:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.is_running = True
        self.next_screen = None

        # Nút quay lại
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 20, 100, 40)),
            text='Quay lại',
            manager=self.manager
        )

        # Lấy lịch sử từ Firebase
        self.history_data = firebase_manager.get_match_history(limit=50)

        # Hiển thị danh sách trận đấu
        self.buttons = []
        start_y = 100
        for i, match in enumerate(self.history_data):
            status = "Đang chơi" if match.get('is_loadable') else "Kết thúc"
            mode = match.get('Mode', 'Offline')
            winner = match.get('WinnerPlayerID', '-')
            text = f"ID: {match['MatchID']} | Mode: {mode} | Status: {status} | Winner: {winner}"

            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((50, start_y + i*50, 700, 40)),
                text=text,
                manager=self.manager
            )
            self.buttons.append(btn)

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.is_running = False
                self.next_screen = 'menu'
            else:
                # Click vào 1 trận đấu
                for i, btn in enumerate(self.buttons):
                    if event.ui_element == btn:
                        match = self.history_data[i]
                        match_id = match['MatchID']
                        if match.get('is_loadable'):
                            # Load game state từ Firebase
                            final_state = firebase_manager.load_game_state(match_id)
                            if final_state:
                                self.next_screen = ('resume_game', match_id, final_state)
                                self.is_running = False
                        else:
                            print(f"Trận {match_id} đã kết thúc, không thể tiếp tục.")

        self.manager.process_events(event)

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)
