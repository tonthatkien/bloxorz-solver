"""
gui/theme.py – Định nghĩa theme giao diện theo nhóm màn chơi.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Optional, Tuple

Color = Tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    name: str

    # Bầu trời
    sky_top: Color
    sky_bot: Color

    # Mây
    cloud_color: Color
    cloud_alpha: int          # 0-255

    # Mặt trời (None = ẩn)
    sun_disc: Optional[Color]
    sun_halo: Optional[Color]
    sun_halo_alpha: int

    # Mặt trăng
    show_moon: bool

    # Sao
    show_stars: bool

    # Sét
    show_lightning: bool

    # Sương mù đáy màn hình
    show_fog: bool

    # Màu sàn tile (top face)
    tile_top: Color
    tile_left: Color          # mặt trái (tối hơn)
    tile_right: Color         # mặt phải (vừa)
    tile_depth: Color         # cạnh dưới đất

    # Có vẽ hoa cỏ & vòng hoa không
    show_vegetation: bool
    show_garland: bool


# Định nghĩa 4 theme

GARDEN = Theme(
    name="garden",
    sky_top=(70, 135, 218),
    sky_bot=(145, 195, 248),
    cloud_color=(255, 255, 255),
    cloud_alpha=210,
    sun_disc=(230, 190, 70),
    sun_halo=(225, 175, 55),
    sun_halo_alpha=90,
    show_moon=False,
    show_stars=False,
    show_lightning=False,
    show_fog=False,
    tile_top=(110, 175, 75),
    tile_left=(72, 110, 42),
    tile_right=(90, 138, 55),
    tile_depth=(101, 67, 33),
    show_vegetation=True,
    show_garland=True,
)

SUNSET = Theme(
    name="sunset",
    sky_top=(195, 90, 40),
    sky_bot=(238, 162, 90),
    cloud_color=(255, 195, 155),
    cloud_alpha=190,
    sun_disc=(250, 135, 25),
    sun_halo=(238, 105, 15),
    sun_halo_alpha=100,
    show_moon=False,
    show_stars=False,
    show_lightning=False,
    show_fog=False,
    tile_top=(148, 128, 72),
    tile_left=(95, 75, 35),
    tile_right=(118, 100, 52),
    tile_depth=(88, 62, 28),
    show_vegetation=True,
    show_garland=True,
)

DUSK = Theme(
    name="dusk",
    sky_top=(42, 28, 75),
    sky_bot=(95, 60, 125),
    cloud_color=(115, 85, 145),
    cloud_alpha=155,
    sun_disc=None,
    sun_halo=None,
    sun_halo_alpha=0,
    show_moon=True,
    show_stars=True,
    show_lightning=False,
    show_fog=False,
    tile_top=(65, 75, 90),
    tile_left=(38, 42, 55),
    tile_right=(52, 58, 72),
    tile_depth=(30, 30, 40),
    show_vegetation=False,
    show_garland=True,
)

STORM = Theme(
    name="storm",
    sky_top=(28, 32, 40),
    sky_bot=(62, 67, 78),
    cloud_color=(78, 78, 88),
    cloud_alpha=225,
    sun_disc=None,
    sun_halo=None,
    sun_halo_alpha=0,
    show_moon=False,
    show_stars=False,
    show_lightning=True,
    show_fog=True,
    tile_top=(72, 68, 65),
    tile_left=(42, 38, 35),
    tile_right=(58, 54, 50),
    tile_depth=(35, 30, 28),
    show_vegetation=False,
    show_garland=False,
)

# Chu kỳ 4 theme xoay vòng
THEME_CYCLE = [GARDEN, SUNSET, DUSK, STORM]

_EXPLICIT_MAP = {
    "t2": SUNSET,
}


def get_theme(level_name: str) -> Theme:
    """Trả về Theme phù hợp dựa vào tên level (vd. 'g1_basic_01', 'g5_extreme_01').

    Hỗ trợ chu kỳ xoay vòng tự động (Loop):
      g1, g5, g9...   -> GARDEN  (Sáng)
      g2, g6, g10...  -> SUNSET  (Hoàng hôn)
      g3, g7, g11...  -> DUSK    (Đêm)
      g4, g8, g12...  -> STORM   (Giông bão)
    """
    lower = level_name.lower()

    # 1. Khớp theo tên theme tường minh nếu xuất hiện trong tên
    for th in THEME_CYCLE:
        if th.name in lower:
            return th

    # 2. Khớp các tiền tố đặc biệt đã định nghĩa (ví dụ t2)
    prefix_2 = lower[:2] if len(lower) >= 2 else ""
    if prefix_2 in _EXPLICIT_MAP:
        return _EXPLICIT_MAP[prefix_2]

    # 3. Chu kỳ tự động theo số hiệu nhóm màn (g1..g4, g5..g8, g9...)
    match = re.search(r'[gt](\d+)', lower)
    if match:
        group_num = int(match.group(1))
        if group_num > 0:
            return THEME_CYCLE[(group_num - 1) % len(THEME_CYCLE)]

    return GARDEN
