# core/piece.py
class Piece:
    def __init__(self, player_id, piece_id):
        self.player_id = player_id
        self.id = piece_id
        self.path_index = -1  # -1 = còn trong chuồng
        self.finished = False # Trạng thái đã về đích hay chưa

    # Trong file: core/piece.py

    def move(self, steps, path_len):
        """
        Di chuyển quân cờ và cập nhật trạng thái nếu về đích.
        - steps: số bước đi (giá trị xúc xắc).
        - path_len: tổng độ dài đường đi (ví dụ: 57 ô).
        """
        if self.finished:
            return

        # Ra quân từ trong chuồng
        if self.path_index == -1 and steps == 6:
            self.path_index = 0
            return

        # Di chuyển trên đường đi
        if self.path_index >= 0:
            new_index = self.path_index + steps
            # GameManager đã kiểm tra nước đi này là hợp lệ
            self.path_index = new_index

            # KIỂM TRA VỀ ĐÍCH: Nếu đến đúng ô cuối cùng
            # (ví dụ: index 56 nếu đường đi dài 57 ô)
            if self.path_index == path_len - 1:
                self.finished = True