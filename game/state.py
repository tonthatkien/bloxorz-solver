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
    r: int = 0
    c: int = 0
    orient: int = STAND
    bridges: int = 0
    split: Optional[Tuple[Cell, Cell]] = None


def cells(s: State) -> List[Cell]:
    """Danh sách ô mà khối (hoặc 2 cube) đang chiếm."""
    if s.split is not None:
        return list(s.split)
    if s.orient == STAND:
        return [(s.r, s.c)]
    if s.orient == HORIZ:
        return [(s.r, s.c), (s.r, s.c + 1)]
    return [(s.r, s.c), (s.r + 1, s.c)]
