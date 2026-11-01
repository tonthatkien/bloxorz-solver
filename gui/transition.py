"""Hiệu ứng chuyển cảnh mờ dần (Smooth Fade Transition) cho Bloxorz."""
from typing import Callable, Optional, Tuple
import pygame

FADE_COLOR: Tuple[int, int, int] = (15, 23, 42)
FADE_OUT_MS: int = 320                            # Thời gian mờ tối dần
HOLD_DARK_MS: int = 60                            # Giữ màn tối để nạp màn chơi ngầm
FADE_IN_MS: int = 340                             # Thời gian sáng dần trở lại
TOTAL_FADE_MS: int = FADE_OUT_MS + HOLD_DARK_MS + FADE_IN_MS
SPAWN_DELAY_MS: int = 280                         # Chờ màn hình sáng rõ rồi mới thả khối rơi


def _smootherstep(t: float) -> float:
    """Nội suy Ken Perlin's Smootherstep (đạo hàm 0 tại hai đầu biên)."""
    c = max(0.0, min(1.0, t))
    return c * c * c * (c * (c * 6.0 - 15.0) + 10.0)


class ScreenFader:
    """Quản lý chu trình fade-out và fade-in giữa các màn chơi."""

    def __init__(self, window_size: Tuple[int, int], color: Tuple[int, int, int] = FADE_COLOR) -> None:
        self.window_size = window_size
        self.color = color
        self.is_fading: bool = False
        self.fade_start_time: int = 0
        self.mid_callback: Optional[Callable[[], None]] = None
        self.callback_called: bool = False
        self._surface = pygame.Surface(window_size, pygame.SRCALPHA)

    def start(self, now_ms: int, on_mid_point: Optional[Callable[[], None]] = None) -> None:
        """Bắt đầu chu trình fade: mờ tối dần -> gọi callback đổi màn -> sáng dần."""
        self.is_fading = True
        self.fade_start_time = now_ms
        self.mid_callback = on_mid_point
        self.callback_called = False

    def update(self, now_ms: int) -> None:
        """Cập nhật tiến trình fade và gọi callback tại đỉnh điểm tối."""
        if not self.is_fading:
            return
        elapsed = now_ms - self.fade_start_time
        if elapsed >= FADE_OUT_MS and not self.callback_called:
            self.callback_called = True
            if self.mid_callback:
                self.mid_callback()
        if elapsed >= TOTAL_FADE_MS:
            self.is_fading = False

    def draw(self, surface: pygame.Surface, now_ms: int) -> None:
        """Vẽ lớp phủ mờ dần lên màn hình."""
        if not self.is_fading:
            return
        elapsed = now_ms - self.fade_start_time
        if elapsed < FADE_OUT_MS:
            alpha = int(255 * _smootherstep(elapsed / float(FADE_OUT_MS)))
        elif elapsed < FADE_OUT_MS + HOLD_DARK_MS:
            alpha = 255
        elif elapsed < TOTAL_FADE_MS:
            rem = elapsed - FADE_OUT_MS - HOLD_DARK_MS
            alpha = int(255 * (1.0 - _smootherstep(rem / float(FADE_IN_MS))))
        else:
            alpha = 0

        if alpha > 0:
            self._surface.fill((*self.color, max(0, min(255, alpha))))
            surface.blit(self._surface, (0, 0))
