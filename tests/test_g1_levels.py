import unittest
import glob
from game.level_loader import load_level
from game.game import Game
from game.state import STAND

class TestGroup1Levels(unittest.TestCase):
    def test_g1_levels_validity(self):
        """1. Kiểm tra JSON nạp thành công và đúng luật G1 (chỉ có sàn, trống, đích)."""
        level_files = glob.glob("levels/g1_*.json")
        self.assertTrue(len(level_files) > 0, "Chưa tìm thấy file test case nhóm 1!")
        
        for file_path in level_files:
            with self.subTest(file=file_path):
                level = load_level(file_path)
                self.assertIsNotNone(level)
                self.assertEqual(len(level.fragile), 0, "Nhóm 1 không được có ô fragile")
                self.assertEqual(len(level.bridges), 0, "Nhóm 1 không được có bridge")
                self.assertEqual(len(level.switches), 0, "Nhóm 1 không được có switch")

    def test_g1_levels_playability(self):
        """2. Kiểm tra tính chơi được (Playability): Nạp vào Game API không lỗi."""
        level_files = glob.glob("levels/g1_*.json")
        
        for file_path in level_files:
            with self.subTest(file=file_path):
                level = load_level(file_path)
                game = Game(level)
                
                # Khởi tạo trạng thái ban đầu
                init_state = game.initial_state()
                
                # Theo luật game.py: Khối phải đứng thẳng tại điểm start và không bị tách
                self.assertEqual((init_state.r, init_state.c), level.start, "Tọa độ ban đầu phải khớp với level.start")
                self.assertEqual(init_state.orient, STAND, "Tư thế ban đầu phải là đứng thẳng (STAND)")
                self.assertIsNone(init_state.split, "Khối không được tách đôi ở đầu game")
                
                # Hàm get_successors phải chạy thành công trả về list (có thể rỗng nếu map quá hẹp, nhưng không crash)
                successors = game.get_successors(init_state)
                self.assertIsInstance(successors, list, "get_successors phải trả về một danh sách")
                
                # Nếu là các map hợp lệ mình thiết kế, chắc chắn bước đầu tiên phải có nước đi
                # (Trừ khi cố tình thiết kế Start bị giam cứng)
                self.assertTrue(len(successors) > 0, f"Map {file_path} không có nước đi nào từ vị trí Start!")

if __name__ == "__main__":
    unittest.main()