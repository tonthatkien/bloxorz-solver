import unittest
import glob
from collections import deque
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

    def test_g1_levels_playability_and_solvability(self):
        """2. Kiểm tra trạng thái đầu vào và chạy BFS mini để chắc chắn map giải được."""
        level_files = glob.glob("levels/g1_*.json")
        
        for file_path in level_files:
            with self.subTest(file=file_path):
                level = load_level(file_path)
                game = Game(level)
                
                init_state = game.initial_state()
                
                # Luật game.py: Khối đứng thẳng tại Start và không tách
                self.assertEqual((init_state.r, init_state.c), level.start, "Tọa độ ban đầu khớp level.start")
                self.assertEqual(init_state.orient, STAND, "Tư thế ban đầu phải là STAND")
                self.assertIsNone(init_state.split, "Khối không được tách đôi ở đầu game")
                
                # Hàm get_successors hoạt động
                successors = game.get_successors(init_state)
                self.assertIsInstance(successors, list, "get_successors phải trả list")
                self.assertTrue(len(successors) > 0, f"Map {file_path} không có nước đi nào từ Start (bị kẹt cứng)!")

                # --- BFS mini để đảm bảo map giải được ---
                queue = deque([init_state])
                visited = set([init_state])
                solved = False
                
                max_nodes = 5000 
                nodes_expanded = 0
                
                while queue and nodes_expanded < max_nodes:
                    curr_state = queue.popleft()
                    nodes_expanded += 1
                    
                    if game.is_goal(curr_state):
                        solved = True
                        break
                        
                    # Fix: Nhóm bạn trả về (action, state, cost) hoặc tương tự, 
                    # nên ta linh hoạt dò tìm phần tử State thay vì fix cứng index.
                    for result_tuple in game.get_successors(curr_state):
                        # Dò phần tử nào là object State (có thuộc tính r và c)
                        next_state = next((x for x in result_tuple if hasattr(x, 'r')), None)
                        
                        if next_state and next_state not in visited:
                            visited.add(next_state)
                            queue.append(next_state)
                
                self.assertTrue(solved, f"Map {file_path} không có lời giải hợp lệ!")

if __name__ == "__main__":
    unittest.main()