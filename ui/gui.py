# ui/gui.py
import pygame
import pygame_gui
import logging
from utils.constants import WIDTH, HEIGHT
from utils.sound_manager import SoundManager

# Import tất cả các View
from .menu_view import MenuView
from .mode_selection_view import ModeSelectionView
from .player_selection_view import PlayerSelectionView
from .bot_selection_view import BotSelectionView
from .online_lobby_view import OnlineLobbyView
from .create_room_view import CreateRoomView
from .join_room_view import JoinRoomView
from .rules_view import RulesView
from .settings_view import SettingsView
from .history_view import HistoryView
from .game_ui import GameUI
from .network_game_ui import NetworkGameUI

class LudoGUI:
    def __init__(self):
        pygame.init()
        # Khởi tạo logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.sound_manager = SoundManager()
        pygame.display.set_caption("Cờ Cá Ngựa - Đồ Án")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        try:
            self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')
        except FileNotFoundError:
             logging.warning("Không tìm thấy file 'theme.json', sử dụng theme mặc định.")
             self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT))
             
        self.active_view = None
        
        self.change_screen('menu')
        self.sound_manager.play_music()

    # 1. Hàm change_screen PHẢI nhận 'match_id_to_load'
    def change_screen(self, screen_name, num_players=4, player_types=None, match_id_to_load=None):
        
        if self.active_view and hasattr(self.active_view, 'manager'):
             self.ui_manager.clear_and_reset()
        
        logging.info(f"Chuyển màn hình sang: {screen_name} (Load MatchID: {match_id_to_load})")
        
        if screen_name == 'menu':
            self.active_view = MenuView(self.screen, self.ui_manager)
        elif screen_name == 'mode_select':
            self.active_view = ModeSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'player_select':
            self.active_view = PlayerSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'bot_select':
            self.active_view = BotSelectionView(self.screen, self.ui_manager)
        
        # --- Online ---
        elif screen_name == 'online_lobby':
            self.active_view = OnlineLobbyView(self.screen, self.ui_manager)
        elif screen_name == 'create_room':
             self.active_view = CreateRoomView(self.screen, self.ui_manager)
        elif screen_name == 'join_room':
             self.active_view = JoinRoomView(self.screen, self.ui_manager)
        elif screen_name == 'network_game':
             self.active_view = NetworkGameUI(self.screen, self.sound_manager)
        
        # --- Các màn hình khác ---
        elif screen_name == 'rules':
            self.active_view = RulesView(self.screen, self.ui_manager)
        elif screen_name == 'settings':
             self.active_view = SettingsView(self.screen, self.ui_manager, self.sound_manager)
        elif screen_name == 'history':
             self.active_view = HistoryView(self.screen, self.ui_manager, self.sound_manager)

        # --- PHẦN QUAN TRỌNG ĐỂ TẢI GAME ---
        elif screen_name == 'game': # Game offline/bot
            self.active_view = GameUI(
                self.screen, 
                num_players, 
                player_types, 
                self.sound_manager, 
                match_id_to_load=match_id_to_load # Truyền ID vào đây
            )
        # ------------------------------------
            
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

                # 2. Sửa vòng lặp run để bắt tín hiệu 'load_game'
                if hasattr(self.active_view, 'is_running') and not self.active_view.is_running:
                    next_screen = self.active_view.next_screen
                    if next_screen:
                        num_players = 4 
                        player_types = None
                        match_id = None # Đặt match_id là None ban đầu

                        # Lấy thông số cho game MỚI (Offline)
                        if isinstance(self.active_view, PlayerSelectionView) and next_screen == 'game':
                            num_players = self.active_view.num_players
                            player_types = ['human'] * num_players
                        # Lấy thông số cho game MỚI (Bot)
                        elif isinstance(self.active_view, BotSelectionView) and next_screen == 'game':
                            difficulty = self.active_view.bot_difficulty
                            num_players = 2 
                            player_types = ['human', difficulty]
                        
                        # --- LOGIC QUAN TRỌNG ĐỂ TẢI GAME ---
                        elif isinstance(self.active_view, HistoryView) and next_screen == 'load_game':
                             match_id = self.active_view.selected_match_id
                             next_screen = 'game' # Đổi tín hiệu thành 'game'
                             logging.info(f"GUI: Nhận tín hiệu load_game cho MatchID: {match_id}")
                        # ----------------------------------
                        
                        # Gọi change_screen với các thông số đã lấy
                        self.change_screen(
                            next_screen, 
                            num_players=num_players, 
                            player_types=player_types, 
                            match_id_to_load=match_id # Sẽ là ID (nếu tải) hoặc None (nếu game mới)
                        )
                        continue

            if self.active_view:
                self.active_view.draw()
                
            pygame.display.flip()

        # Đóng logger khi thoát
        if (hasattr(self.active_view, 'game_manager') and 
            self.active_view.game_manager and 
            hasattr(self.active_view.game_manager, 'logger') and 
            self.active_view.game_manager.logger):
             self.active_view.game_manager.logger.close()
             
        pygame.quit()