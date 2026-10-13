"""Heuristic cho A*: h(game, state) -> float.  TODO [F3-F5].

Nhắc: phải admissible với hàm chi phí đã chọn ở UCS (F1).
"""


def h_zero(game, state) -> float:
    """h = 0 (A* thành UCS), dùng để so sánh/kiểm tra."""
    return 0.0
