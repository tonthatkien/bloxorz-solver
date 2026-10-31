# Bloxorz Solver – CSC14003 Project 1

Game Bloxorz có GUI + 4 solver (BFS, DFS/IDS, UCS, A*). Python 3.10+.

## Cài đặt & chạy
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                   # nạp màn mặc định
python main.py levels/g3_switch_demo.json
python -m unittest discover -s tests -t .    # chạy test

# Thực nghiệm (F3)
python -m experiments.run_all --repeats 3            # -> experiments/results/results.csv
python -m experiments.benchmark_heuristics --repeats 3  # -> experiments/results/heuristics*.csv
```

## Đọc trước khi code (bắt buộc)
| File | Nội dung |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | **Quy định làm việc nhóm**: 5 quy tắc không được vi phạm, quy trình một việc, nhánh/commit/PR, review, Definition of Done, họp và báo tiến độ, AI và liêm chính học thuật, chốt code |
| [`docs/GIT_GUIDE.md`](docs/GIT_GUIDE.md) | Hướng dẫn Git/GitHub từng bước, xử lý conflict, các tình huống hay gặp |
| [`docs/CODING_STANDARDS.md`](docs/CODING_STANDARDS.md) | Quy ước viết code, kiến trúc (ai được gọi ai), quy ước riêng cho game/solver/GUI/test |
| [`docs/REVIEW_GUIDE.md`](docs/REVIEW_GUIDE.md) | Cách review, checklist theo từng loại việc, cách viết nhận xét |
| [`docs/REVIEW_ASSIGNMENTS.md`](docs/REVIEW_ASSIGNMENTS.md) | Ai làm việc gì, ai review ai, lịch dự kiến của từng người |
| [`docs/AI_USAGE_LOG.md`](docs/AI_USAGE_LOG.md) | Nhật ký dùng AI (phụ lục báo cáo) |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Tài liệu tham khảo (phần tài liệu trong báo cáo) |
| `Bloxorz_Task_Tracker.xlsx` | Danh sách việc, lịch, độ nặng, người làm, **người review**, trạng thái |

Mẫu Pull Request nằm ở `.github/pull_request_template.md`; CI chạy unit test tự động (`.github/workflows/tests.yml`).
Repo GitHub nên có **gốc là thư mục `Source`** (chứa `main.py`) để CI chạy đúng.

## Cấu trúc thư mục
| Thư mục / file | Nội dung | Người phụ trách |
|---|---|---|
| `game/state.py` | `State`, `cells()` (**đã xong, đừng sửa nếu chưa báo nhóm**) | cả nhóm |
| `game/level_loader.py` | đọc + kiểm tra JSON màn chơi (đã xong) | cả nhóm |
| `game/game.py` | `Game`: `initial_state`, `is_goal`, `get_successors` | A, B, C |
| `game/dummy_game.py` | game giả để E, F test solver sớm | – |
| `solvers/base.py` | `SearchResult`, `Limits`, `run_measured` (đã xong) | E, F |
| `solvers/bfs.py`, `dfs.py` | BFS, DFS/IDS | E |
| `solvers/ucs.py`, `astar.py`, `heuristics.py` | UCS, A*, heuristic | F |
| `gui/app.py`, `main.py` | GUI (B vẽ ô dễ vỡ/cầu/công tắc, D làm phần còn lại) | D, B |
| `experiments/common.py` | hạ tầng dùng chung: `run_one`, `measure`, `sanity_check`, `write_csv` | F |
| `experiments/run_all.py` | chạy 4 solver trên bộ màn, xuất `results.csv` (E: script chạy; F: biểu đồ) | E, F |
| `experiments/benchmark_heuristics.py` | so sánh các heuristic của A*, xuất `heuristics.csv` + `heuristics_summary.csv` | F |
| `levels/` | file JSON màn chơi | A, B, C |
| `tests/` | unit test | mọi người |

Chỗ nào cần làm có comment `TODO [ID]` (ID khớp file Excel theo dõi công việc).
Tìm nhanh: `grep -rn "TODO" --include=*.py .`

## Quy định giữa các module (KHÔNG tự ý đổi, muốn đổi phải báo nhóm)

### 1. State (`game/state.py`)
- Tọa độ `(r, c)`: hàng, cột, đếm từ 0 ở góc trên-trái.
- Tư thế: `STAND=0, HORIZ=1, VERT=2`. `(r, c)` là ô **trên-trái** của khối
  (HORIZ chiếm `(r,c),(r,c+1)`; VERT chiếm `(r,c),(r+1,c)`).
- `bridges`: bitmask, bit i = 1 là cầu id=i đang **mở**.
- `split`: `None` khi chưa tách; khi tách là `((r1,c1),(r2,c2))`, phần tử **đầu** là cube
  đang điều khiển. Hành động `S` chỉ hoán đổi 2 phần tử. Khi tách đặt `r=c=0, orient=STAND`.
- Hai cube ở hai ô kề nhau thì ghép lại thành `State` thường (`split=None`).
- Ô dễ vỡ không lưu trong State (đứng lên là thua nên nước đó bị loại khỏi successors).

### 2. Giao diện game (`game/game.py`)
```python
game.initial_state() -> State
game.is_goal(state) -> bool
game.get_successors(state) -> [(action, new_state, cost), ...]
```
- Hành động: `"U","D","L","R"` và `"S"` (đổi cube). Thứ tự sinh cố định: `U, D, L, R, S`.
- Nước đi không hợp lệ **không** xuất hiện trong danh sách; solver không cần biết luật thua.
- Chi phí mặc định 1/bước; UCS truyền `cost_fn(old, action, new)` qua `Game(level, cost_fn=...)`.
- Solver/GUI chỉ gọi game qua 3 hàm trên.

### 3. Solver (`solvers/base.py`)
- Chữ ký: `solve(game, limits=None) -> SearchResult`.
- Mỗi lần mở rộng một nút gọi `checker.tick(expanded)` (để có timeout / giới hạn nút).
- **Nút đã mở rộng** = nút được lấy khỏi frontier và sinh successor (mọi solver đếm giống nhau).
- Đo đạc dùng `run_measured(solver.solve, game)`: thời gian lấy trung bình 3 lần (không bật
  tracemalloc), bộ nhớ đỉnh đo ở lần chạy riêng bằng tracemalloc.
- Gợi ý: dùng `reconstruct_path(parent, state)` với `parent[state] = (prev_state, action)`,
  gốc ánh xạ tới `None`.
- Heuristic: `h(game, state) -> float` trong `solvers/heuristics.py`.

## Định dạng màn chơi (`levels/*.json`)
| Ký tự `grid` | Ý nghĩa |
|---|---|
| `.` | ô trống (void) |
| `#` | ô sàn |
| `G` | ô đích |

Ô dễ vỡ, cầu, công tắc, ô xuất phát đều ghi `#` trong `grid` rồi khai báo ở các danh sách riêng.
```json
{
  "name": "g3_switch_demo",
  "grid": ["###...", "######", "..###G", "..###."],
  "start": [0, 0],
  "goal": [2, 5],
  "fragile": [[1, 3]],
  "bridges": [{"id": 0, "pos": [2, 3], "open": false}],
  "switches": [
    {"type": "soft",  "pos": [1, 1], "targets": [0], "mode": "toggle"},
    {"type": "heavy", "pos": [3, 2], "targets": [0], "mode": "permanent", "set": "open"},
    {"type": "split", "pos": [0, 2], "cubes": [[3, 3], [1, 5]]}
  ]
}
```
- `mode`: `"toggle"` (mỗi lần kích hoạt đảo trạng thái) hoặc `"permanent"` (kèm `"set": "open"|"close"`).
- Công tắc `split` có đúng 2 vị trí trong `cubes`; công tắc soft/heavy dùng `targets` (id cầu).
- Tên file màn chơi theo nhóm test: `g1_basic_XX`, `g2_fragile_XX`, `g3_switch_XX`, `g4_mixed_XX`
  (tên này dùng luôn trong bảng thực nghiệm). Thêm màn mới thì chạy `python -m unittest discover -s tests -t .`
  để loader kiểm tra hợp lệ.

## Quy ước Git (tóm tắt, đầy đủ ở CONTRIBUTING.md và docs/GIT_GUIDE.md)
- `main` chỉ chứa code chạy được, **không push thẳng**. Mỗi việc một nhánh: `feature/<tên>-<ID>`
  (ví dụ `feature/an-A3`), xong thì mở Pull Request, **nhờ 1 người khác xem** rồi mới merge.
- Commit message: `[A3] Add orientation transition table`.
- Mỗi việc có **người review** riêng (xem Excel); không tự merge khi chưa được Approve; review trong 24 giờ.
- Mỗi người chỉ sửa file thuộc module của mình. Muốn đổi `State` hoặc 3 hàm của `Game` thì báo cả nhóm trước.
- Trước khi bắt đầu việc mới: `git checkout main && git pull`.
```bash
git checkout main && git pull
git checkout -b feature/an-A3
# ... code ...
git add <file> && git commit -m "[A3] Add orientation transition table"
git push -u origin feature/an-A3     # rồi mở Pull Request trên GitHub
```

## Công cụ khác
- Danh sách việc chi tiết: file Excel theo dõi công việc của nhóm (ID như `A3`, `E2`...).
- Timeout / giới hạn nút mặc định trong `Limits` (2 triệu nút, 60 giây). Vượt thì `solved=False`
  và `note="timeout"` / `"node_limit"`.
