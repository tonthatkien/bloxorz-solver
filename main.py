"""Điểm vào chương trình.  python main.py [đường_dẫn_màn_chơi.json]"""
import sys

# Windows: đảm bảo stdout dùng UTF-8 để in tiếng Việt không lỗi
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from game.level_loader import load_level
from gui.app import run


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "levels/g1_basic_01.json"
    level = load_level(path)
    print(f"Loaded level '{level.name}' ({level.rows}x{level.cols}), start={level.start}, goal={level.goal}")
    run(path)


if __name__ == "__main__":
    main()
