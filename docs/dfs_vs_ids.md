# Lựa chọn DFS hay IDS cho bộ giải Bloxorz

> Task E1. Quyết định cuối cùng cần cả nhóm xác nhận (ghi tên người xác nhận ở mục 7).

## 1. Quyết định
Nhóm chọn: **DFS (stack tự quản lý, có tập visited)**.

## 2. Lý do
1. **Đề yêu cầu xử lý trạng thái lặp bằng visited/hashing.** Khi đã có visited, lợi thế bộ nhớ
   của IDS (chỉ lưu một nhánh) gần như mất đi, vì visited vẫn phình ra theo số trạng thái đã thăm.
2. **Không gian trạng thái hữu hạn**, nên DFS có visited luôn kết thúc và tìm được lời giải nếu có.
3. **Tạo sự tương phản với BFS** ở phần Thực nghiệm: DFS thường mở ít nút hơn nhưng lời giải
   dài hơn và không tối ưu, nên có nhiều điều để phân tích.
4. **Cài đặt đơn giản và an toàn.** Dùng stack thay vì đệ quy để tránh `RecursionError` khi
   đường đi dài. IDS cần xử lý thêm "bẫy visited" (xem mục 4).

## 3. So sánh

| Tiêu chí | DFS + visited | IDS |
|---|---|---|
| Độ khó cài đặt | Dễ | Khó hơn (xử lý visited theo độ sâu) |
| Có tìm được lời giải? | Có (không gian hữu hạn, có visited) | Có |
| Độ dài lời giải | Có thể rất dài, không tối ưu | Ngắn nhất khi mỗi nước đi tốn 1 |
| Bộ nhớ | Phụ thuộc kích thước visited | Ít khi không dùng visited toàn cục; phải duyệt lại các tầng nông |
| Giá trị phân tích trong báo cáo | Tương phản rõ với BFS | Gần giống BFS về độ dài lời giải |

## 4. Xử lý trạng thái lặp
- Visited lưu **toàn bộ `State`**: vị trí, tư thế, bitmask cầu, và `split` (2 cube + cube đang điều khiển).
- `State` là dataclass `frozen=True` nên hashable, dùng được trong `set`/`dict`.
- Với IDS, một visited chung cho mọi vòng có thể làm bỏ lỡ lời giải: trạng thái bị đánh dấu khi gặp
  ở tầng sâu có thể cần đi tiếp từ tầng nông hơn. Cách đúng là reset visited mỗi vòng, hoặc lưu độ
  sâu nhỏ nhất đã gặp và chỉ chặn khi lần gặp mới không nông hơn.

## 5. Quy ước đo đạc (dùng chung `solvers/base.py`)
- **Expanded node**: mỗi lần lấy một nút ra khỏi frontier thì tăng đúng một lần
  (theo `docs/CODING_STANDARDS.md`, mục 4). Mọi solver đếm giống nhau.
- **Search time**: `time.perf_counter()`, trung bình 3 lần chạy, **không** bật tracemalloc.
- **Peak memory**: `tracemalloc`, đo ở một lần chạy riêng vì tracemalloc làm chương trình chậm đi.
- **Solution length**: `len(path)`, với `path` là danh sách action.
- Mọi lời giải được kiểm bằng `solvers.metrics.verify_path` (đi lại path bằng `get_successors`).

## 6. Hạn chế
- DFS không đảm bảo lời giải ngắn nhất.
- `tracemalloc` chỉ đo bộ nhớ Python cấp phát; thời gian phụ thuộc máy, nên chạy mọi solver
  trên cùng một máy khi làm thực nghiệm.

  