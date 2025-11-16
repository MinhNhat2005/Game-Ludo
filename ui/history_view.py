# ui/history_view.py
import pygame
import pygame_gui
import logging
from utils.constants import WIDTH, HEIGHT
# Đảm bảo đã có file database_manager.py trong utils


class HistoryView:
    def __init__(self, screen, manager, sound_manager):
        self.screen = screen
        self.manager = manager
        self.sound_manager = sound_manager
        self.is_running = True
        self.next_screen = None
        self.selected_match_id = None # Sẽ lưu ID trận đấu được chọn để tải

        # --- Giao diện nền và tiêu đề ---
        try:
            self.background = pygame.transform.scale( pygame.image.load('assets/images/background.png').convert(), (WIDTH, HEIGHT))
        except pygame.error:
            self.background = pygame.Surface((WIDTH, HEIGHT)); self.background.fill(pygame.Color('#1a1a1a'))
        try:
            self.title_font = pygame.font.SysFont('Arial', 60, bold=True)
        except pygame.error: self.title_font = pygame.font.Font(None, 60)
        title_text = self.title_font.render('LỊCH SỬ / TIẾP TỤC', True, pygame.Color('white'))
        title_rect = title_text.get_rect(center=(WIDTH // 2, 80))
        self.background.blit(title_text, title_rect)

        # --- Tạo danh sách hiển thị lịch sử ---
        list_width = WIDTH - 200
        list_height = HEIGHT - 300
        list_rect = pygame.Rect(0, 0, list_width, list_height)
        list_rect.center = (WIDTH // 2, HEIGHT // 2 + 30)

        match_list = get_match_history()

        item_list_data = []
        self.match_data_map = {} 

        if not match_list:
            item_list_data.append( ("Chưa có lịch sử trận đấu nào.", "no_history") )
        else:
            for match in match_list:
                is_loadable = match.get('is_loadable', False)
                
                if is_loadable:
                    status_text = "(Đang chơi dở - Click để tiếp tục)"
                elif match['WinnerPlayerID'] is not None:
                    status_text = f"(Người {match['WinnerPlayerID'] + 1} thắng)"
                else:
                    status_text = "(Đã kết thúc - Không rõ)"
                
                start_time = match['StartTime']
                display_text = f"[{match['Mode']}] - {start_time} - {status_text} ({match['NumPlayers']} người)"
                match_id_str = f"match_{match['MatchID']}" 
                
                item_list_data.append( (display_text, match_id_str) )
                self.match_data_map[match_id_str] = match 
        
        self.history_list = pygame_gui.elements.UISelectionList(
            relative_rect=list_rect, item_list=item_list_data, manager=manager, allow_multi_select=False
        )

        # --- Nút Quay Lại ---
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, HEIGHT - 100), (200, 50)),
            text='QUAY LẠI MENU', manager=self.manager, object_id='#back_button'
        )

    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.history_list:
                selected_item_id = event.ui_object_id 
                if selected_item_id and selected_item_id in self.match_data_map:
                    match_info = self.match_data_map[selected_item_id]
                    
                    if match_info.get('is_loadable', False):
                        self.selected_match_id = match_info['MatchID']
                        self.is_running = False 
                        self.next_screen = 'load_game' # Gửi tín hiệu tải game
                        logging.info(f"HistoryView: Yêu cầu tải lại game: MatchID {self.selected_match_id}")
                    else:
                        logging.info(f"HistoryView: Xem lịch sử trận đã kết thúc: MatchID {match_info['MatchID']}")
                        actions = get_action_history(match_info['MatchID'])
                        logging.info(f"--- Chi tiết trận {match_info['MatchID']} ---")
                        for action in actions:
                             logging.info(f"  P{action['PlayerID']+1}: {action['ActionType']} - {action['Detail']}")
                        logging.info("-----------------------------")

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.is_running = False; self.next_screen = 'menu'

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.manager.draw_ui(self.screen)

    def update(self, time_delta):
        self.manager.update(time_delta)