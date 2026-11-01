# Bloxorz Solver – CSC14003 Project 1

Cài đặt lại game **Bloxorz** bằng Python, có giao diện đồ họa (pygame) và 4 thuật toán tìm kiếm tự cài đặt:
**BFS, DFS, UCS, A\***. Có 20 màn chơi chia thành 4 nhóm độ khó và bộ công cụ thực nghiệm để đo
thời gian, bộ nhớ, số nút mở rộng và độ dài lời giải.

- Môn học: CSC14003 – Introduction to Artificial Intelligence, Khoa CNTT, ĐH Khoa học Tự nhiên, ĐHQG-HCM
- Video demo: `<điền link YouTube>`
- Báo cáo: `Report.pdf` (nằm cùng cấp với thư mục `Source`)

## Thành viên

| MSSV | Họ và tên |
|---|---|
| `<24120078>` | `<Tôn Thất Kiên >` |
| `<24120160>` | `<Mai Thảo Vy>` |
| `<24120170>` | `<Phạm Gia Bảo>` |
| `<24120177>` | `<Cáp Hửu Duy>` |
| `<24120178>` | `<Trần Ngọc Gia Hân>` |


## Cài đặt và chạy

Yêu cầu: **Python 3.10 trở lên**. Thư viện: `pygame`, `matplotlib`, `pandas` (xem `requirements.txt`).
Các thuật toán tìm kiếm không dùng thư viện ngoài, tất cả được cài đặt trong thư mục `solvers/`.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py                                  # mở game ở màn mặc định (g1_basic_01)
python main.py levels/g4_mixed_04.json          # mở thẳng một màn bất kỳ
```

Chạy các lệnh từ **thư mục chứa `main.py`** (thư mục `Source`).

## Hướng dẫn dùng giao diện

**Phím điều khiển**

| Phím | Tác dụng |
|---|---|
| Mũi tên | Lăn khối lên, xuống, trái, phải |
| Space | Đổi cube đang điều khiển (khi khối đang tách thành 2 cube) |
| R | Chơi lại màn hiện tại |
| H | Mở hộp thoại hướng dẫn luật chơi |
| Space hoặc Enter | Sang màn kế tiếp (khi vừa thắng) |
| ESC | Thoát |

**Nút trên màn hình**

| Nút | Tác dụng |
|---|---|
| New Game | Mở bảng chọn màn |
| Restart | Chơi lại màn hiện tại |
| `?` | Hướng dẫn luật chơi |
| Home | Quay về màn hình mở đầu |
| BFS / DFS / UCS / A\* | Chạy thuật toán tương ứng. Nếu đã lăn khối vài bước thì giải **từ vị trí hiện tại**; nếu từ đó không còn đường tới đích, hộp thoại *Dead End* hiện ra và cho chọn Restart & Solve |
| Replay Solution / Stop Replay | Phát lại lời giải tìm được |
| 0.5x … 2.0x | Đổi tốc độ phát lại |
| Path / Hide Path | Hiện hoặc ẩn vết duyệt (các ô solver đã mở rộng) và đường nghiệm |

Ô thống kê ở thanh dưới hiển thị thời gian tìm kiếm, bộ nhớ, số nút mở rộng và độ dài lời giải của lần chạy gần nhất.
Lưu ý: bộ nhớ trên GUI là **giá trị ước lượng** để hiển thị; số đo bộ nhớ đỉnh dùng trong báo cáo
được đo bằng `tracemalloc` trong `experiments/` (xem mục Thực nghiệm).

## Các lựa chọn thiết kế

- **Biểu diễn trạng thái** (`game/state.py`): vị trí, tư thế khối (đứng / nằm ngang / nằm dọc), bitmask trạng
  thái đóng/mở của các cầu và thông tin tách cube. Hai trạng thái cùng vị trí nhưng khác cấu hình cầu là hai
  trạng thái khác nhau.
- **BFS**: hàng đợi FIFO + tập visited, cho lời giải ít bước nhất.
- **DFS**: nhóm chọn **DFS** (ngăn xếp tự quản lý, không đệ quy) kèm tập visited để tránh lặp, **không dùng IDS**.
  Lời giải tìm được không đảm bảo ngắn nhất.
- **UCS**: hàm chi phí mặc định mỗi bước 1.0. Chế độ *weighted* (dùng trong thực nghiệm) tính: bước thường 1.0,
  bước đè lên ô dễ vỡ 1.5, bước kích hoạt công tắc hoặc tách cube 1.2, hành động đổi cube 0.5.
  Giải thích và biện luận đầy đủ nằm trong báo cáo.
- **A\***: heuristic mặc định là `h_advanced` (`solvers/heuristics_advanced.py`). Các heuristic có sẵn để so sánh:
  `zero`, `manhattan`, `manhattan_orient`, `relaxed_maze`, `switch_aware`, `split_cubes`, `advanced`.
  Chứng minh tính admissible/consistent nằm trong báo cáo.
- **Đếm nút mở rộng**: một nút được tính là đã mở rộng khi được lấy khỏi frontier và sinh successor. Mọi solver
  đếm theo cùng quy ước này.
- **Giới hạn mặc định** (`Limits`): 2 triệu nút hoặc 60 giây. Vượt thì `solved=False`, `note="node_limit"` hoặc
  `"timeout"`.

## Cấu trúc thư mục

```
Source/
├── main.py                  Điểm vào chương trình
├── requirements.txt
├── README.md
├── game/                    Luật chơi và logic game
│   ├── state.py             State (bất biến, hashable)
│   ├── block.py, board.py   Khối 1x1x2 và các phép lăn; lưới màn chơi
│   ├── cube.py, split.py    Cube đơn, đổi cube, tách/ghép khối
│   ├── fragile.py, tiles.py Ô dễ vỡ, cầu, công tắc
│   ├── level_loader.py      Đọc và kiểm tra file JSON màn chơi
│   ├── game.py              Giao diện game cho solver và GUI
│   └── dummy_game.py        Game giả dùng để test solver sớm
├── solvers/                 Thuật toán tìm kiếm
│   ├── base.py              SearchResult, Limits, đo đạc dùng chung
│   ├── bfs.py, dfs.py, ucs.py, astar.py
│   ├── heuristics.py        Hàm chi phí và heuristic cơ bản
│   ├── heuristics_advanced.py   Các heuristic dùng cho A*
│   └── metrics.py           Kiểm chứng và đo đạc kết quả
├── gui/                     Giao diện pygame (vẽ board, khối, hiệu ứng, hộp thoại, replay, vết duyệt)
├── levels/                  20 màn chơi dạng JSON
├── experiments/             Chạy thực nghiệm và vẽ biểu đồ
│   ├── run_all.py, benchmark_heuristics.py, common.py
│   └── plot.py, plot_*.py
└── tests/                   Unit test
```

## Màn chơi

20 màn trong `levels/`, chia 4 nhóm (tên file dùng luôn trong bảng thực nghiệm của báo cáo):

| Nhóm | Số màn | Nội dung |
|---|---|---|
| `g1_basic_01` … `05` | 5 | Chỉ có ô sàn, ô trống và đích |
| `g2_fragile_01` … `05` | 5 | Thêm ô dễ vỡ |
| `g3_switch_01` … `04` | 4 | Thêm cầu và công tắc (soft, heavy) |
| `g4_mixed_01` … `06` | 6 | Kết hợp tất cả, có công tắc split |

### Định dạng file màn chơi

| Ký tự `grid` | Ý nghĩa |
|---|---|
| `.` | Ô trống (void) |
| `#` | Ô sàn |
| `G` | Ô đích |

Ô dễ vỡ, cầu, công tắc và ô xuất phát đều ghi `#` trong `grid`, rồi khai báo ở các danh sách riêng.
Tọa độ `(hàng, cột)` đếm từ 0 ở góc trên-trái.

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

- `mode`: `"toggle"` (mỗi lần kích hoạt đảo trạng thái) hoặc `"permanent"` (kèm `"set": "open"` hoặc `"close"`).
- Công tắc `split` có đúng 2 vị trí trong `cubes`; công tắc soft/heavy dùng `targets` (id cầu, từ 0 đến 63).
- Một ô chỉ chứa một loại đặc biệt. Loader từ chối file sai và báo rõ tọa độ.
- Thêm màn mới: đặt file vào `levels/` theo quy ước tên trên, rồi chạy test để loader kiểm tra.

## Quy ước giữa các module

**State** (`game/state.py`)
- Tư thế: `STAND=0`, `HORIZ=1`, `VERT=2`. `(r, c)` là ô **trên-trái** của khối
  (HORIZ chiếm `(r,c),(r,c+1)`; VERT chiếm `(r,c),(r+1,c)`).
- `bridges`: bitmask, bit *i* bằng 1 nghĩa là cầu có id *i* đang mở.
- `split`: `None` khi chưa tách; khi tách là `((r1,c1),(r2,c2))`, phần tử đầu là cube đang điều khiển.
  Hai cube ở hai ô kề nhau thì tự ghép lại thành khối thường.

**Game** (`game/game.py`) – solver và GUI chỉ gọi game qua 3 hàm:

```python
game.initial_state() -> State
game.is_goal(state) -> bool
game.get_successors(state) -> [(action, new_state, cost), ...]
```

- Hành động: `"U"`, `"D"`, `"L"`, `"R"` và `"S"` (đổi cube). Thứ tự sinh cố định: U, D, L, R, S.
- Nước đi không hợp lệ không xuất hiện trong danh sách successor.
- Chi phí mặc định 1 mỗi bước; UCS truyền `cost_fn(old, action, new)` qua `Game(level, cost_fn=...)`.

**Solver** (`solvers/base.py`) – chữ ký `solve(game, limits=None) -> SearchResult`.

## Thực nghiệm

Chạy từ thư mục `Source`. Kết quả ghi vào `experiments/results/`.

```bash
# 1. Chạy 4 solver trên toàn bộ màn, cả hai chế độ chi phí (unit và weighted)
python -m experiments.run_all --repeats 3
#    -> experiments/results/results.csv
python -m experiments.run_all --levels g1 --repeats 1     # chạy thử nhanh một nhóm

# 2. So sánh các heuristic của A*
python -m experiments.benchmark_heuristics --repeats 3
#    -> experiments/results/heuristics.csv, heuristics_summary.csv

# 3. Vẽ biểu đồ từ các file CSV ở trên
python -m experiments.plot --results experiments/results/results.csv \
  --heuristics experiments/results/heuristics.csv \
  --summary experiments/results/heuristics_summary.csv
#    -> experiments/results/f4/ (PNG, PDF, SVG)
```

- Thời gian lấy trung bình theo `--repeats`; bộ nhớ đỉnh đo ở một lần chạy riêng bằng `tracemalloc`
  (vì `tracemalloc` làm chương trình chậm đi).
- Chế độ `unit`: mọi bước chi phí 1, UCS trùng BFS. Chế độ `weighted`: dùng hàm chi phí không đều nêu ở trên.
- Có thể chỉnh `--max-nodes` và `--timeout`. Trên PowerShell, viết lệnh trên một dòng hoặc dùng dấu backtick để xuống dòng.

## Kiểm thử

```bash
python -m unittest discover -s tests -t .
```

Test bao gồm: bảng chuyển tư thế, ô dễ vỡ, cầu và công tắc, tách/ghép cube, kiểm tra từng màn trong `levels/`,
và kiểm chứng lời giải của cả 4 solver bằng cách đi lại đường đi qua `get_successors`.

## Sử dụng AI và tài liệu tham khảo

Nhật ký dùng AI (prompt, kết quả, cách kiểm chứng) và danh sách tài liệu tham khảo nằm ở phụ lục và phần
tài liệu tham khảo của `Report.pdf`.