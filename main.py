"""Điểm vào chương trình.  python main.py [đường_dẫn_màn_chơi.json]"""
import sys

from game.level_loader import load_level


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "levels/g1_basic_01.json"
    level = load_level(path)
    print(f"Đã nạp màn '{level.name}' ({level.rows}x{level.cols}), start={level.start}, goal={level.goal}")
    # TODO [D]: from gui.app import run; run(path)


if __name__ == "__main__":
    main()
