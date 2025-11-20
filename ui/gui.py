# ui/gui.py
import pygame
import pygame_gui
import logging
from utils import firebase_manager
firebase_manager.initialize_firebase()

from utils.constants import WIDTH, HEIGHT
from utils.sound_manager import SoundManager
from core.auth_manager import AuthManager

# Import các View
from .menu_view import MenuView
from .mode_selection_view import ModeSelectionView
from .player_selection_view import PlayerSelectionView
from .bot_selection_view import BotSelectionView
from .online_lobby_view import OnlineLobbyView
from .create_room_view import CreateRoomView
from .join_room_view import JoinRoomView
from .rules_view import RulesView
from .settings_view import SettingsView
from .HistoryUI import HistoryUI
from .game_ui import GameUI
from .network_game_ui import NetworkGameUI
from .login_view import LoginView
from .register_view import RegisterView

class LudoGUI:
    def __init__(self):
        pygame.init()
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.sound_manager = SoundManager()
        self.auth_manager = AuthManager()
        self.logged_in_user_id = None

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
        # Bắt đầu với màn hình login, KHÔNG phát nhạc
        self.change_screen('login')

    def change_screen(self, screen_name, num_players=None, player_types=None, user_uid=None):
        """Chuyển màn hình GUI, với phát nhạc đúng màn hình"""
        if self.active_view and hasattr(self.active_view, 'manager'):
            self.ui_manager.clear_and_reset()

        logging.info(f"Chuyển màn hình sang: {screen_name}")

        # --- Login / Register ---
        if screen_name == 'login':
            self.active_view = LoginView(self.screen, self.ui_manager)
            # Không phát nhạc
        elif screen_name == 'register':
            self.active_view = RegisterView(self.screen, self.ui_manager)
            # Không phát nhạc

        # --- Menu / Mode Selection / Player / Bot ---
        elif screen_name == 'menu':
            self.active_view = MenuView(self.screen, self.ui_manager)
            # Phát nhạc chỉ khi vào menu
            self.sound_manager.play_music()
        elif screen_name == 'mode_select':
            self.active_view = ModeSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'player_select':
            self.active_view = PlayerSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'bot_select':
            self.active_view = BotSelectionView(self.screen, self.ui_manager)
        elif screen_name == 'history':
            self.active_view = HistoryUI(self.screen, self.ui_manager)
            # Không phát nhạc (hoặc tùy chỉnh nếu muốn)


        # --- Game Offline ---
        # --- Trong LudoGUI.change_screen() ---
        elif screen_name == 'game':
            self.sound_manager.stop_music() 
            
            # Khối này chỉ chạy khi self.active_view là BotSelectionView
            if isinstance(self.active_view, BotSelectionView):
                
                # SỬA LỖI Ở ĐÂY: Đọc thuộc tính đã được BotSelectionView lưu
                bot_difficulty = getattr(self.active_view, 'selected_bot_difficulty', 'easy') 
                
                logging.info(f"Đã chọn độ khó: {bot_difficulty}") # DÒNG LOG KIỂM TRA
                
                if bot_difficulty == 'hard':
                    bot_type = 'bot_hard' # <--- CHÍNH XÁC
                else:
                    bot_type = 'bot_easy'
                
                self.active_view = GameUI(
                    self.screen,
                    num_players=2, 
                    player_types=['human', bot_type],
                    sound_manager=self.sound_manager
                )
            else:
                # Offline bình thường
                self.active_view = GameUI(
                    self.screen,
                    num_players=num_players or 4,
                    player_types=player_types,
                    sound_manager=self.sound_manager
                )


        # --- Online / Network ---
        elif screen_name == 'online_lobby':
            self.active_view = OnlineLobbyView(self.screen, self.ui_manager)
        elif screen_name == 'create_room':
            self.active_view = CreateRoomView(self.screen, self.ui_manager)
        elif screen_name == 'join_room':
            self.active_view = JoinRoomView(self.screen, self.ui_manager)
        elif screen_name == 'network_game':
            self.active_view = NetworkGameUI(self.screen, self.sound_manager)

        # --- Settings / Rules / History ---
        elif screen_name == 'rules':
            self.active_view = RulesView(self.screen, self.ui_manager)
        elif screen_name == 'settings':
            self.active_view = SettingsView(self.screen, self.ui_manager, self.sound_manager)
        elif screen_name == 'history':
            self.active_view = HistoryUI(self.screen, self.ui_manager, self.sound_manager)

        # --- Exit ---
        elif screen_name == 'exit':
            self.is_running = False

        elif screen_name == 'resume_game':
            # num_players và player_types lúc này dùng tạm để chứa match_id và final_state
            match_id, final_state = num_players, player_types  
            mode = final_state.get('mode', 'Offline')


            # Xác định player_types cho Offline/Bot
            if mode == 'Offline':
                player_types_to_use = ['human'] * final_state['num_players']
            elif mode == 'Bot':
                player_types_to_use = ['human', 'bot_easy']  # hoặc lấy từ final_state nếu lưu đủ
            else:
                # Online không resume, chỉ chơi trực tiếp
                player_types_to_use = ['human'] * final_state['num_players']

            # Tạo GameManager từ state đã load
            gm = GameUI(
                self.screen,
                num_players=final_state['num_players'],
                player_types=player_types_to_use,
                sound_manager=self.sound_manager
            ).gm
            gm.match_id = match_id
            gm._apply_loaded_state(final_state)

            # Tạo lại GameUI với GameManager đã load
            self.active_view = GameUI(
                self.screen,
                num_players=final_state['num_players'],
                player_types=player_types_to_use,
                sound_manager=self.sound_manager,
                gm=gm
            )


        else:
            logging.warning(f"Màn hình '{screen_name}' chưa được định nghĩa!")

    def run(self):
        while self.is_running:
            time_delta = self.clock.tick(60) / 1000.0

            # --- Handle events ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                if self.active_view:
                    self.active_view.handle_events(event)

            # --- Update active view ---
            if self.active_view:
                self.active_view.update(time_delta)

                # Nếu view báo dừng, chuyển màn hình mới
                if hasattr(self.active_view, 'is_running') and not self.active_view.is_running:
                    next_screen = getattr(self.active_view, 'next_screen', None)

                    if next_screen:
                        # Trường hợp resume game từ HistoryUI
                        if isinstance(next_screen, tuple) and next_screen[0] == 'resume_game':
                            match_id = next_screen[1]
                            final_state = next_screen[2]
                            self.change_screen('resume_game', num_players=match_id, player_types=final_state)

                        else:
                            num_players = getattr(self.active_view, 'num_players', None)
                            player_types = getattr(self.active_view, 'player_types', None)

                            # Xử lý login
                            if isinstance(self.active_view, LoginView) and next_screen == 'menu':
                                self.logged_in_user_id = getattr(self.active_view, 'user_id', None)
                                logging.info(f"Người dùng ID {self.logged_in_user_id} đăng nhập thành công, chuyển Menu.")
                                self.sound_manager.play_music()
                            elif isinstance(self.active_view, RegisterView) and next_screen == 'login':
                                logging.info("Đăng ký thành công, quay về màn hình đăng nhập.")

                            self.change_screen(next_screen, num_players=num_players, player_types=player_types)

            # --- Draw active view ---
            if self.active_view:
                self.active_view.draw()

            pygame.display.flip()

        # --- Close game ---
        if (hasattr(self.active_view, 'game_manager') and 
            self.active_view.game_manager and 
            hasattr(self.active_view.game_manager, 'logger') and 
            self.active_view.game_manager.logger):
            self.active_view.game_manager.logger.close()

        pygame.quit()

