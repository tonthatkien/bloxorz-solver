# Quy ước viết code

Mục tiêu: code của 6 người đọc như của một người, dễ review, dễ giải thích khi vấn đáp.

## 1. Chung
- Python **3.10+**. Theo **PEP 8**; độ dài dòng **tối đa 100 ký tự**; thụt lề 4 dấu cách; file UTF-8.
- **Tên (biến, hàm, lớp, file) viết bằng tiếng Anh**: `snake_case` cho hàm/biến/file, `PascalCase` cho lớp,
  `UPPER_CASE` cho hằng số. Tên phải nói lên ý nghĩa (`bridge_mask`, không phải `bm` hay `x2`).
- **Comment và docstring có thể viết tiếng Việt hoặc tiếng Anh**, nhưng trong **một file** dùng một ngôn ngữ cho nhất quán.
  Comment giải thích *vì sao*, không lặp lại *cái gì* mà code đã nói rõ.
- **Type hint** cho tham số và kết quả của mọi hàm công khai; **docstring** cho mọi lớp và hàm công khai (một dòng tóm tắt là đủ cho hàm nhỏ).
- Mỗi hàm làm một việc, **ngắn (< ~40 dòng)**. Dài hơn thì tách.
- Không để **code chết**, không comment-out cả khối code, không `print` gỡ lỗi sót lại (dùng `logging` hoặc xóa trước khi commit).
- Không dùng "số ma thuật": `0, 1, 2` cho tư thế thì dùng `STAND, HORIZ, VERT`; số khác đặt hằng số có tên.
- Không dùng `from module import *` (trừ khi để re-export có chủ đích).
- Thêm `.editorconfig` (đã có sẵn) vào VS Code/PyCharm để tự thụt lề đúng. Khuyến khích chạy `ruff check` hoặc `black` trước khi commit (không bắt buộc).

## 2. Kiến trúc: ai được gọi ai
```
gui/  ───►  solvers/  ───►  game/
 │                           ▲
 └───────────────────────────┘
experiments/  ──►  solvers/, game/
```
- `game/` **không** import `solvers/` hay `gui/`.
- `solvers/` chỉ gọi game qua **3 hàm**: `initial_state()`, `is_goal()`, `get_successors()` (+ `game.cost_fn` nếu có). Không đụng vào nội bộ của `Game`.
- `gui/` chỉ gọi game qua cùng 3 hàm và gọi solver qua `solve(game, limits)`; GUI **không** chứa luật chơi.
- `experiments/` và `tests/` được phép import mọi thứ.

## 3. Quy ước cho `game/`
- `State` **bất biến** (`frozen=True`) và hashable. Không bao giờ sửa state tại chỗ: tạo `State` mới.
- `get_successors` **không có tác dụng phụ** (không sửa `self`, không sửa state truyền vào) và trả về theo **thứ tự cố định** `U, D, L, R, S`.
- Nước đi không hợp lệ **không xuất hiện** trong kết quả. Không dùng exception để báo "rơi khỏi bản đồ".
- Mọi luật (dễ vỡ, cầu, công tắc, tách/ghép) nằm trong `game/`, kèm unit test cho từng luật.
- Hai state bằng nhau về mặt trò chơi phải **bằng nhau về dữ liệu** (chuẩn hóa: khi tách thì `r=c=0, orient=STAND`; khi ghép thì `split=None`).

## 4. Quy ước cho `solvers/`
- Chữ ký cố định: `solve(game, limits=None) -> SearchResult`. Không đổi.
- Mỗi lần **lấy một nút ra khỏi frontier** thì tăng `expanded` đúng một lần và gọi `checker.tick(expanded)`.
- Dùng `set`/`dict` cho visited, dùng `collections.deque` cho hàng đợi BFS, `heapq` cho UCS/A*. Khi dùng `heapq` thêm **số thứ tự phá hòa** (counter) vào tuple để không so sánh `State` với nhau.
- Truy vết đường đi bằng `parent` (state → (state trước, hành động)), không lưu cả đường đi trong từng nút (tốn bộ nhớ).
- **Tự cài đặt thuật toán**, không gọi hàm tìm kiếm từ thư viện.
- Không in ra màn hình trong solver; trả mọi số liệu qua `SearchResult`.
- Heuristic nằm ở `solvers/heuristics.py`, mỗi hàm có docstring nêu **vì sao admissible** với hàm chi phí đang dùng.

## 5. Quy ước cho `gui/`
- Tách **vẽ** (render) khỏi **xử lý sự kiện** khỏi **logic**. Không viết một hàm 300 dòng.
- GUI không được đứng hình khi chạy solver lâu: chạy solver ở luồng/tiến trình riêng hoặc cho giới hạn thời gian rõ ràng và báo "đang tìm...".
- Màu, kích thước ô, phím tắt đặt thành hằng số ở đầu file hoặc file `settings`.

## 6. Test
- Thư mục `tests/`, file `test_*.py`, dùng `unittest`. Tên test mô tả hành vi: `test_standing_on_fragile_tile_loses`.
- Mỗi test kiểm **một ý**. Dữ liệu test nhỏ, dựng ngay trong test hoặc dùng file trong `levels/`.
- Muốn thêm màn mới: đặt tên theo nhóm (`g1_basic_XX`, `g2_fragile_XX`, `g3_switch_XX`, `g4_mixed_XX`) và để test nạp màn tự kiểm tra tính hợp lệ.

## 7. Hiệu năng (vì có đo thời gian/bộ nhớ)
- Không `copy.deepcopy` trong vòng lặp tìm kiếm. State bất biến nên không cần.
- Tính trước những thứ không đổi (ví dụ tập ô sàn, ô dễ vỡ) trong `Game.__init__`, đừng tính lại ở mỗi lần gọi `get_successors`.
- Tối ưu có đo đạc (ghi lại trước/sau), không đoán mò.

## 8. File và cấu trúc
- Một file một trách nhiệm; file > ~400 dòng thì cân nhắc tách.
- Không sửa file thuộc module của người khác khi chưa báo (xem bảng trong `README.md`). Cần sửa nhỏ thì nhắn họ hoặc để họ review.
- Đường dẫn dùng `pathlib`/đường dẫn tương đối từ gốc dự án, không hardcode `C:\Users\...`.
- Ngẫu nhiên (nếu có): luôn đặt **seed** để kết quả lặp lại được.
