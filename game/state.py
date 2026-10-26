"""State của Bloxorz (bất biến + hashable, dùng được trong set/dict).

QUY ƯỚC (đã chốt cả nhóm, KHÔNG tự ý đổi):
- Tọa độ (r, c): hàng, cột, đếm từ 0 ở góc trên-trái.
- Khối thường: (r, c) là ô TRÊN-TRÁI của khối.
    STAND : chiếm (r, c)
    HORIZ : chiếm (r, c), (r, c+1)
    VERT  : chiếm (r, c), (r+1, c)
- bridges: bitmask int, bit i = 1 nghĩa là cầu có id=i đang MỞ.
- split: None khi khối chưa tách. Khi tách: ((r1,c1), (r2,c2));
    phần tử ĐẦU là cube đang được điều khiển. Hành động "S" chỉ hoán đổi 2 phần tử.
    Khi split != None thì đặt r=c=0, orient=STAND để tránh sinh state trùng.
- Khi 2 cube ở 2 ô kề nhau -> ghép lại thành State thường (split=None).
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

STAND, HORIZ, VERT = 0, 1, 2
Cell = Tuple[int, int]


@dataclass(frozen=True)
class State:
    """Bản ghi bất biến, có thể băm, của khối thường hoặc khối đã tách."""

    r: int = 0
    c: int = 0
    orient: int = STAND
    bridges: int = 0
    split: Optional[Tuple[Cell, Cell]] = None

    def __post_init__(self) -> None:
        """Kiểm tra tọa độ split và chuẩn hóa các trường không dùng khi khối đã tách."""
        if self.split is None:
            return
        if not isinstance(self.split, tuple) or len(self.split) != 2:
            raise TypeError("split phải là tuple gồm đúng hai bộ tọa độ")
        for position in self.split:
            if not isinstance(position, tuple) or len(position) != 2:
                raise TypeError("mỗi vị trí trong split phải là một bộ tọa độ")
            if any(type(coordinate) is not int for coordinate in position):
                raise TypeError("tọa độ trong split phải là số nguyên")
        if self.split[0] == self.split[1]:
            raise ValueError("hai cube tách rời phải nằm ở hai ô khác nhau")
        object.__setattr__(self, "r", 0)
        object.__setattr__(self, "c", 0)
        object.__setattr__(self, "orient", STAND)


def cells(s: State) -> List[Cell]:
    """Danh sách ô mà khối (hoặc 2 cube) đang chiếm."""
    if s.split is not None:
        return list(s.split)
    if s.orient == STAND:
        return [(s.r, s.c)]
    if s.orient == HORIZ:
        return [(s.r, s.c), (s.r, s.c + 1)]
    return [(s.r, s.c), (s.r + 1, s.c)]
