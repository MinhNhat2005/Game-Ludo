# ui/gui.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT
from .menu_view import MenuView
from .mode_selection_view import ModeSelectionView
from .player_selection_view import PlayerSelectionView # Import mới
from .game_ui import GameUI
from .online_lobby_view import OnlineLobbyView
from .rules_view import RulesView
from .settings_view import SettingsView
from .bot_selection_view import BotSelectionView
from .create_room_view import CreateRoomView
from .join_room_view import JoinRoomView
# (Đảm bảo bạn cũng đã import NetworkGameUI nếu có)
from .network_game_ui import NetworkGameUI

class LudoGUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Cờ Cá Ngựa - Đồ Án")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')
        self.active_view = None
        self.change_screen('menu')

    def change_screen(self, screen_name, num_players=4, player_types=None):
        self.ui_manager.clear_and_reset()

        if screen_name == 'menu':
            self.active_view = MenuView(self.screen, self.ui_manager)
        elif screen_name == 'mode_select':
            self.active_view = ModeSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'player_select':
            self.active_view = PlayerSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'bot_select':
            self.active_view = BotSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'online_lobby':
            self.active_view = OnlineLobbyView(self.screen, self.ui_manager)

        # --- THÊM LOGIC MỚI ---
        elif screen_name == 'create_room':
            self.active_view = CreateRoomView(self.screen, self.ui_manager)
        elif screen_name == 'join_room':
            self.active_view = JoinRoomView(self.screen, self.ui_manager)
        # --- LOGIC MỚI CHO GAME ONLINE ---
        elif screen_name == 'network_game':
            # NetworkGameUI sẽ tự lấy trạng thái từ client.py
            self.active_view = NetworkGameUI(self.screen) 
        # ---------------------------

        elif screen_name == 'rules':
            self.active_view = RulesView(self.screen, self.ui_manager)
        elif screen_name == 'settings':
            self.active_view = SettingsView(self.screen, self.ui_manager)
        elif screen_name == 'game': # Game offline
            self.active_view = GameUI(self.screen, num_players, player_types)
        elif screen_name == 'exit':
            self.is_running = False

    def run(self):
        while self.is_running:
            time_delta = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                if self.active_view:
                    self.active_view.handle_events(event)

            if self.active_view:
                self.active_view.update(time_delta)

                if hasattr(self.active_view, 'is_running') and not self.active_view.is_running:
                    next_screen = self.active_view.next_screen
                    if next_screen:
                        if isinstance(self.active_view, PlayerSelectionView) and next_screen == 'game':
                            num_players = self.active_view.num_players
                            player_types = ['human'] * num_players
                            self.change_screen(next_screen, num_players=num_players, player_types=player_types)
                        elif isinstance(self.active_view, BotSelectionView) and next_screen == 'game':
                            player_types = ['human', 'bot'] # Default: 1 Human vs 1 Bot
                            self.change_screen(next_screen, num_players=2, player_types=player_types)
                        else:
                            self.change_screen(next_screen)
                        continue

            if self.active_view:
                self.active_view.draw()
            pygame.display.flip()

        pygame.quit()