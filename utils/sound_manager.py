# utils/sound_manager.py
import pygame
import os
import logging # Thêm logging

class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init()
            self.sounds = {}
            self.music_volume = 0.5
            self.sfx_volume = 0.8

            # --- Trạng thái bật/tắt cho từng SFX ---
            self.sfx_enabled = {
                'dice': True,
                'move': True,
                'kick': True,
                'win': True,
                'done': True
                # Thêm các loại khác nếu cần
            }
            # ----------------------------------------

            self._load_sounds()
            self.set_music_volume(self.music_volume)
            logging.info("SoundManager initialized successfully.") # Dùng logging
        except pygame.error as e:
            logging.error("Lỗi khởi tạo Pygame Mixer: %s. Âm thanh có thể không hoạt động.", e) # Dùng logging
            pygame.mixer.quit()
            self.sounds = None

    def _load_sounds(self):
        if not pygame.mixer.get_init(): return

        sound_dir = 'assets/sounds'
        try:
            music_path = os.path.join(sound_dir, 'background_music.mp3')
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                logging.info("Loaded music: %s", music_path)
            else:
                logging.warning("Music file not found at %s", music_path)

            sfx_files = { 'dice': 'dice_roll.mp3', 'move': 'piece_move.mp3',
                          'kick': 'kick.mp3', 'win': 'win.mp3', 'done':'done.mp3' }
            for name, filename in sfx_files.items():
                path = os.path.join(sound_dir, filename)
                if os.path.exists(path):
                    self.sounds[name] = pygame.mixer.Sound(path)
                    logging.info("Loaded sound '%s': %s", name, path)
                else:
                    logging.warning("Sound file not found at %s for '%s'", path, name)
                    # Đặt cờ enabled thành False nếu không tải được file
                    if name in self.sfx_enabled:
                         self.sfx_enabled[name] = False


        except pygame.error as e: logging.error("Lỗi khi tải âm thanh: %s", e)
        except Exception as e: logging.exception("Lỗi không xác định khi tải âm thanh")


    def play_music(self, loops=-1):
        if pygame.mixer.get_init() and pygame.mixer.music.get_volume() > 0:
             try:
                  if not pygame.mixer.music.get_busy():
                       pygame.mixer.music.play(loops)
                       logging.info("Playing background music.")
             except pygame.error as e: logging.error("Lỗi khi phát nhạc: %s", e)

    def stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            logging.info("Stopped background music.")

    def play_sfx(self, name):
        """Phát hiệu ứng âm thanh nếu nó được bật."""
        # --- KIỂM TRA TRẠNG THÁI ENABLED ---
        if pygame.mixer.get_init() and name in self.sounds and self.sfx_enabled.get(name, False):
        # ----------------------------------
            try:
                sound = self.sounds[name]
                sound.set_volume(self.sfx_volume)
                sound.play()
            except pygame.error as e: logging.error("Lỗi khi phát SFX '%s': %s", name, e)

    def set_music_volume(self, volume):
        if pygame.mixer.get_init():
            try: self.music_volume = float(max(0.0, min(1.0, volume)))
            except ValueError: self.music_volume = 0.5; logging.warning("Âm lượng nhạc không hợp lệ.")
            pygame.mixer.music.set_volume(self.music_volume)
            logging.debug("Music volume set to %.2f", self.music_volume)

    def set_sfx_volume(self, volume):
        if pygame.mixer.get_init():
            try: self.sfx_volume = float(max(0.0, min(1.0, volume)))
            except ValueError: self.sfx_volume = 0.8; logging.warning("Âm lượng SFX không hợp lệ.")
            logging.debug("SFX volume base set to %.2f", self.sfx_volume)

    def get_music_volume(self): return self.music_volume
    def get_sfx_volume(self): return self.sfx_volume

    # --- HÀM BẬT/TẮT VÀ KIỂM TRA TRẠNG THÁI SFX ---
    def toggle_sfx(self, name):
        """Bật/tắt một loại hiệu ứng âm thanh."""
        if name in self.sfx_enabled:
            self.sfx_enabled[name] = not self.sfx_enabled[name]
            logging.info("SFX '%s' set to %s", name, self.sfx_enabled[name])
            return self.sfx_enabled[name] # Trả về trạng thái mới
        return None # Trả về None nếu tên không hợp lệ

    def is_sfx_enabled(self, name):
        """Kiểm tra xem một loại hiệu ứng có đang bật không."""
        return self.sfx_enabled.get(name, False)
    # ---------------------------------------------