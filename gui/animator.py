"""Quản lý các trạng thái diễn hoạt (Animations) cho Bloxorz GUI."""
import math
from typing import Optional, Tuple
from game.state import STAND, State

# Animation timings (in milliseconds)
ANIM_DURATION_MS      = 140
FALL_GOAL_DURATION_MS = 600
FALL_VOID_DURATION_MS = 900
SPAWN_DURATION_MS     = 500
SPAWN_HEIGHT          = 8.5
REPLAY_STEP_DELAY_MS  = 70
REPLAY_SPLIT_PAUSE_MS = 650
REPLAY_SWAP_PAUSE_MS  = 380
REPLAY_MERGE_PAUSE_MS = 480


def ease_roll(t: float) -> float:
    """Đường cong nội suy chuyển động lăn khối."""
    return t * t * (3.0 - 2.0 * t)


class AnimationManager:
    """Quản lý tiến độ diễn hoạt spawn, lăn khối (roll) và rơi vực/hố (fall)."""

    def __init__(self) -> None:
        # Spawn
        self.spawning: bool = True
        self.spawn_start_time: int = 0
        self.z_spawn: float = SPAWN_HEIGHT

        # Roll
        self.animating: bool = False
        self.anim_start_r: int = 0
        self.anim_start_c: int = 0
        self.anim_start_orient: int = STAND
        self.anim_action: str = 'D'
        self.anim_next_state: Optional[State] = None
        self.anim_is_void: bool = False
        self.anim_start_time: int = 0
        self.buffered_action: Optional[str] = None
        self.anim_is_split: bool = False
        self.anim_split_tuple: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        self.anim_progress: float = 0.0

        # Falling
        self.falling_goal: bool = False
        self.falling_void: bool = False
        self.fall_start_time: int = 0
        self.fall_r: float = 0.0
        self.fall_c: float = 0.0
        self.fall_orient: int = STAND
        self.fall_is_split: bool = False
        self.fall_split_tuple: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None

    def reset_for_level(self, now_ms: int, delay_ms: int = 0) -> None:
        """Đặt lại toàn bộ trạng thái animation khi bắt đầu màn mới hoặc restart."""
        self.spawning = True
        self.spawn_start_time = now_ms + delay_ms
        self.z_spawn = SPAWN_HEIGHT

        self.animating = False
        self.anim_is_split = False
        self.anim_split_tuple = None
        self.buffered_action = None
        self.anim_progress = 0.0

        self.falling_goal = False
        self.falling_void = False
        self.fall_is_split = False
        self.fall_split_tuple = None

    def start_roll(self, state: State, action: str, next_st: State,
                   is_void: bool, now_ms: int) -> None:
        """Bắt đầu diễn hoạt lăn khối."""
        self.animating = True
        if state.split is not None:
            self.anim_is_split = True
            self.anim_start_r, self.anim_start_c = state.split[0]
            self.anim_start_orient = STAND
            self.anim_split_tuple = state.split
        else:
            self.anim_is_split = False
            self.anim_start_r = state.r
            self.anim_start_c = state.c
            self.anim_start_orient = state.orient
            self.anim_split_tuple = None

        self.anim_action = action
        self.anim_next_state = next_st
        self.anim_is_void = is_void
        self.anim_start_time = now_ms
        self.buffered_action = None

    def start_fall_goal(self, state: State, now_ms: int) -> None:
        """Bắt đầu diễn hoạt chìm xuống hố đích."""
        self.falling_goal = True
        self.fall_start_time = now_ms
        self.fall_r = float(state.r)
        self.fall_c = float(state.c)
        self.fall_orient = state.orient
        self.buffered_action = None

    def start_fall_void(self, now_ms: int) -> None:
        """Bắt đầu diễn hoạt rơi vào khoảng không."""
        self.falling_void = True
        self.fall_is_split = self.anim_is_split
        self.fall_split_tuple = self.anim_split_tuple
        self.fall_start_time = now_ms
        self.buffered_action = None

    def update_spawn(self, now_ms: int) -> None:
        """Cập nhật tọa độ rơi tiếp đất từ trên trời xuống."""
        if not self.spawning:
            return
        if now_ms < self.spawn_start_time:
            self.z_spawn = SPAWN_HEIGHT
            return
        elapsed = now_ms - self.spawn_start_time
        if elapsed >= SPAWN_DURATION_MS:
            self.spawning = False
            self.z_spawn = 0.0
        else:
            t = elapsed / float(SPAWN_DURATION_MS)
            if t <= 0.78:
                tf = t / 0.78
                self.z_spawn = SPAWN_HEIGHT * (1.0 - tf * tf)
            else:
                tb = (t - 0.78) / 0.22
                self.z_spawn = 0.22 * math.sin(tb * math.pi) * (1.0 - tb * 0.5)

    def get_anim_tuple(self) -> Optional[tuple]:
        """Tạo tuple truyền cho renderer draw_scene khi đang animating."""
        if not self.animating:
            return None
        if self.anim_is_split and self.anim_split_tuple is not None:
            return ('split', self.anim_start_r, self.anim_start_c, self.anim_action,
                    self.anim_progress, self.anim_split_tuple)
        return (self.anim_start_r, self.anim_start_c, self.anim_start_orient,
                self.anim_action, self.anim_progress)

    def get_fall_tuple(self, now_ms: int) -> Tuple[Optional[tuple], bool, bool]:
        """Cập nhật tiến trình rơi và trả về (fall_tuple, won_event, lost_event)."""
        if self.falling_goal:
            gt = (now_ms - self.fall_start_time) / FALL_GOAL_DURATION_MS
            if gt >= 1.0:
                self.falling_goal = False
                return None, True, False
            alpha = int(255 * max(0.0, 1.0 - gt))
            return ('goal', self.fall_r, self.fall_c, self.fall_orient, alpha), False, False

        elif self.falling_void:
            elapsed_ms = now_ms - self.fall_start_time
            t = elapsed_ms / 1000.0
            if elapsed_ms >= FALL_VOID_DURATION_MS:
                self.falling_void = False
                return None, False, True
            if self.fall_is_split and self.fall_split_tuple is not None:
                f_tup = ('void_split', self.anim_start_r, self.anim_start_c,
                         self.anim_action, t, self.fall_split_tuple)
            else:
                f_tup = ('void', self.anim_start_r, self.anim_start_c,
                         self.anim_start_orient, self.anim_action, t)
            return f_tup, False, False

        return None, False, False
