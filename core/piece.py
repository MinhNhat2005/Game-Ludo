# core/piece.py
class Piece:
    def __init__(self, player_id, piece_id):
        self.player_id = player_id
        self.id = piece_id
        self.path_index = -1  # -1 = còn trong chuồng
        self.finished = False # Trạng thái đã về đích hay chưa

    def move(self, steps):
        """
        Di chuyển quân cờ và cập nhật trạng thái nếu về đích.
        Sử dụng tổng số bước đi là 57.
        """
        PATH_LENGTH = 57
        if self.finished:
            return

        # Ra quân từ trong chuồng
        if self.path_index == -1 and steps == 6:
            self.path_index = 0
            return

        # Di chuyển trên đường đi
        if self.path_index >= 0:
            new_index = self.path_index + steps
            self.path_index = new_index

            # KIỂM TRA VỀ ĐÍCH: Nếu đến đúng ô cuối cùng (index = 56)
            # thì đánh dấu là đã hoàn thành.
            if self.path_index == PATH_LENGTH - 1:
                self.finished = True