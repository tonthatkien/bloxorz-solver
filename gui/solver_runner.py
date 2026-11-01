"""Bộ điều khiển luồng tìm kiếm (Solver Thread) và Replay lời giải cho Bloxorz."""
import queue
import threading
import time
from typing import List, Optional
import pygame

from game.game import Game
from game.level_loader import Level
from game.state import State
from solvers import astar, bfs, dfs, ucs
from solvers.base import LimitReached, Limits, SearchResult, run_measured

SOLVER_MODULES = {
    'BFS': bfs,
    'DFS': dfs,
    'UCS': ucs,
    'A*': astar,
}

REPLAY_SPEEDS = [1.0, 1.5, 2.0, 0.5]


class GuiSolverGame(Game):
    """Game tùy biến cho GUI: hỗ trợ trạng thái ban đầu và nhường CPU cho animation."""

    def __init__(self, level: Level, start_state: Optional[State] = None) -> None:
        super().__init__(level)
        self._start_state = start_state
        self._step_counter = 0

    def initial_state(self) -> State:
        return self._start_state if self._start_state is not None else super().initial_state()

    def get_successors(self, s: State):
        self._step_counter += 1
        if (self._step_counter & 0x1FF) == 0:
            time.sleep(0.0005)  # Nhường CPU định kỳ
        return super().get_successors(s)


InProgressGame = GuiSolverGame


class SolverManager:
    """Quản lý chạy thuật toán nền và điều khiển replay."""

    def __init__(self) -> None:
        self.is_solving: bool = False
        self.solving_name: str = ""
        self.solve_req_id: int = 0
        self.solve_queue: queue.Queue = queue.Queue()
        self.last_result: Optional[SearchResult] = None
        self.last_solver_name: str = ""
        self.solve_start_state: Optional[State] = None
        self.is_from_progress: bool = False

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
            self.solve_start_state = None
            self.is_from_progress = False

    def start_solve(self, name: str, level: Level,
                    start_state: Optional[State] = None,
                    is_from_progress: bool = False) -> None:
        """Khởi động luồng chạy solver ngầm (Threaded Background Worker)."""
        if self.is_solving or name not in SOLVER_MODULES:
            return

        self.reset(reset_result=False)
        self.solve_req_id += 1
        current_req_id = self.solve_req_id
        self.is_solving = True
        self.solving_name = name
        self.solve_start_state = start_state
        self.is_from_progress = is_from_progress

        def _worker(solver_fn, game_level, s_name, req_id, custom_start):
            try:
                solver_game = GuiSolverGame(game_level, custom_start)
                limits = Limits(max_nodes=2_000_000, timeout_sec=60.0)

                t0 = time.perf_counter()
                res = solver_fn(solver_game, limits=limits, record_trace=True)
                res.time_sec = time.perf_counter() - t0
                # Ước tính peak memory dựa trên số node sinh ra (không dùng tracemalloc để tránh lag GUI)
                res.peak_memory_kb = max(64.0, res.expanded_nodes * 0.40 + len(res.expanded_order) * 0.08 + 128.0)
                res.length = len(res.path)
            except LimitReached as e:
                res = SearchResult(solved=False, note=str(e))
            except Exception as exc:
                res = SearchResult(solved=False, note=str(exc))
            self.solve_queue.put((req_id, s_name, res))

        solver_mod = SOLVER_MODULES[name]
        thread = threading.Thread(
            target=_worker,
            args=(solver_mod.solve, level, name, current_req_id, start_state),
            daemon=True
        )
        thread.start()

    def poll_status(self) -> Optional[str]:
        """Kiểm tra hàng đợi kết quả solver từ worker thread.

        Trả về 'solved' nếu vừa giải xong thành công,
        'failed' nếu vừa kết thúc mà không tìm thấy nghiệm (hoặc lỗi/timeout),
        None nếu đang chạy hoặc không có kết quả mới.
        """
        status: Optional[str] = None
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
                    status = 'solved'
                else:
                    status = 'failed'
        return status

    def poll_queue(self) -> bool:
        """Kiểm tra hàng đợi kết quả solver từ worker thread (tương thích ngược)."""
        return self.poll_status() == 'solved'

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
