# main.py
from ui.gui import LudoGUI
from utils import firebase_manager

if __name__ == "__main__":
    # Khởi tạo Firebase trước
    firebase_manager.initialize_firebase() 
    
    gui = LudoGUI()
    gui.run()
