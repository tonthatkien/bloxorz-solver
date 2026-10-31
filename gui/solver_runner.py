"""Bộ điều khiển luồng tìm kiếm (Solver Thread) và Replay lời giải cho Bloxorz."""
import queue
import threading
from typing import List, Optional
import pygame

from game.game import Game
from game.level_loader import Level
from solvers import astar, bfs, dfs, ucs
from solvers.base import Limits, SearchResult, run_measured

SOLVER_MODULES = {
    'BFS': bfs,
    'DFS': dfs,
    'UCS': ucs,
    'A*': astar,
}

REPLAY_SPEEDS = [1.0, 1.5, 2.0, 0.5]


class SolverManager:
    """Quản lý chạy thuật toán nền và điều khiển replay."""

    def __init__(self) -> None:
        self.is_solving: bool = False
        self.solving_name: str = ""
        self.solve_req_id: int = 0
        self.solve_queue: queue.Queue = queue.Queue()
        self.last_result: Optional[SearchResult] = None
        self.last_solver_name: str = ""

        # Trạng thái replay
        self.is_replaying: bool = False
        self.replay_actions: List[str] = []
        self.replay_index: int = 0
        self.replay_last_time: int = 0
        self.replay_speed: float = 1.0

    def cycle_speed(self) -> float:
        """Chuyển đổi xoay vòng tốc độ replay: 1.0x -> 1.5x -> 2.0x -> 0.5x -> 1.0x."""
        idx = (REPLAY_SPEEDS.index(self.replay_speed) + 1) % len(REPLAY_SPEEDS)
        self.replay_speed = REPLAY_SPEEDS[idx]
        return self.replay_speed

    def reset(self, reset_result: bool = False) -> None:
        """Đặt lại trạng thái tìm kiếm và dừng replay."""
        self.solve_req_id += 1
        self.is_solving = False
        self.solving_name = ""
        self.is_replaying = False
        self.replay_actions = []
        self.replay_index = 0
        if reset_result:
            self.last_result = None
            self.last_solver_name = ""

    def start_solve(self, name: str, level: Level) -> None:
        """Khởi động luồng chạy solver ngầm (Threaded Background Worker)."""
        if self.is_solving or name not in SOLVER_MODULES:
            return

        self.reset(reset_result=False)
        self.solve_req_id += 1
        current_req_id = self.solve_req_id
        self.is_solving = True
        self.solving_name = name

        def _worker(solver_fn, game_level, s_name, req_id):
            try:
                solver_game = Game(game_level)
                limits = Limits(max_nodes=2_000_000, timeout_sec=60.0)
                res = run_measured(solver_fn, solver_game, limits=limits, repeats=1, record_trace=True)
            except Exception as exc:
                res = SearchResult(solved=False, note=str(exc))
            self.solve_queue.put((req_id, s_name, res))

        solver_mod = SOLVER_MODULES[name]
        thread = threading.Thread(
            target=_worker,
            args=(solver_mod.solve, level, name, current_req_id),
            daemon=True
        )
        thread.start()

    def poll_queue(self) -> bool:
        """Kiểm tra hàng đợi kết quả solver từ worker thread.

        Trả về True nếu vừa nhận được lời giải thành công và có thể bắt đầu replay.
        """
        received_new = False
        while not self.solve_queue.empty():
            try:
                req_id, s_name, res = self.solve_queue.get_nowait()
            except queue.Empty:
                break
            if req_id == self.solve_req_id:
                self.last_result = res
                self.last_solver_name = s_name
                self.is_solving = False
                if self.last_result.solved and self.last_result.path:
                    received_new = True
        return received_new

    def start_replay(self) -> bool:
        """Khởi động replay lời giải đã tìm được."""
        if not self.last_result or not self.last_result.solved or not self.last_result.path:
            return False

        self.is_replaying = True
        self.replay_actions = list(self.last_result.path)
        self.replay_index = 0
        self.replay_last_time = pygame.time.get_ticks() + int(200 / self.replay_speed)
        return True

    def stop_replay(self) -> None:
        """Dừng replay lời giải."""
        self.is_replaying = False
        self.replay_actions = []
        self.replay_index = 0

    def get_next_replay_action(self, now_ticks: int, can_step: bool) -> Optional[str]:
        """Lấy nước đi tiếp theo trong replay nếu đã đến thời gian bước tiếp theo."""
        if not self.is_replaying:
            return None
        if not can_step:
            return None
        if now_ticks < self.replay_last_time:
            return None

        if self.replay_index < len(self.replay_actions):
            act = self.replay_actions[self.replay_index]
            self.replay_index += 1
            return act
        else:
            self.stop_replay()
            return None
