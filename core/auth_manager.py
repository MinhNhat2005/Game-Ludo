# core/auth_manager.py
import pyrebase
import logging
from datetime import datetime # Cần import datetime

# ************************************************
# *** CẤU HÌNH FIREBASE DỰA TRÊN DỰ ÁN LUDO-7F297 CỦA BẠN ***
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyCdkob8nSTUyaMkQYe_k2fWwxHj-RttX3g",
    "authDomain": "ludo-71297.firebaseapp.com",
    "projectId": "ludo-71297",
    "storageBucket": "ludo-71297.firebasestorage.app",
    "messagingSenderId": "478136883068",
    "appId": "1:478136883068:web:b8bf85b22640951c9af6f9",
    "databaseURL": "https://ludo-71297-default-rtdb.asia-southeast1.firebasedatabase.app"

}

# ************************************************

class AuthManager:
    """Quản lý xác thực người dùng (Đăng ký/Đăng nhập) với Firebase."""
    def __init__(self):
        self.auth = None
        self.firebase = None
        self.db = None
        try:
            self.firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
            self.auth = self.firebase.auth()
            self.db = self.firebase.database() 
            logging.info("Pyrebase AuthManager initialized successfully.")
        except Exception as e:
            logging.error(f"Lỗi khởi tạo Pyrebase. Kiểm tra FIREBASE_CONFIG và kết nối: {e}", exc_info=True)
            self.auth = None

    def register_user(self, email, password):
        """Đăng ký người dùng mới."""
        if not self.auth: return False, "Lỗi hệ thống: Firebase chưa được cấu hình."
        if not email or not password: return False, "Vui lòng nhập đầy đủ Email và mật khẩu."
        if len(password) < 6: return False, "Mật khẩu tối thiểu 6 ký tự."

        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            user_uid = user['localId']
            
            self.db.child("users").child(user_uid).set({
                "email": email,
                "display_name": email.split('@')[0], 
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            logging.info(f"Đăng ký thành công người dùng Firebase: {email}, UID: {user_uid}")
            return True, f"Đăng ký thành công, chào mừng {email}!"
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message: return False, "Email đã tồn tại."
            elif "WEAK_PASSWORD" in error_message: return False, "Mật khẩu tối thiểu 6 ký tự."
            elif "INVALID_EMAIL" in error_message: return False, "Địa chỉ Email không hợp lệ."
            else:
                logging.error(f"Lỗi Pyrebase khi đăng ký: {error_message}")
                return False, "Lỗi hệ thống khi đăng ký."

    def login_user(self, email, password):
        """Đăng nhập người dùng bằng Email/Password."""
        if not self.auth: return False, None, "Lỗi hệ thống: Firebase chưa được cấu hình."
        if not email or not password: return False, None, "Vui lòng nhập đầy đủ Email và mật khẩu."

        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            user_uid = user['localId']
            
            logging.info(f"Đăng nhập thành công người dùng Pyrebase: {email}, UID: {user_uid}")
            return True, user_uid, f"Chào mừng trở lại!" 

        except Exception as e:
            error_message = str(e)
            if "INVALID_LOGIN_CREDENTIALS" in error_message or "INVALID_PASSWORD" in error_message or "EMAIL_NOT_FOUND" in error_message:
                return False, None, "Email hoặc mật khẩu không chính xác."
            else:
                logging.error(f"Lỗi Pyrebase khi đăng nhập: {error_message}")
                return False, None, "Lỗi hệ thống khi đăng nhập."