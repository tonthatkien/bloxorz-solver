# Câu hỏi 
1. GUI mình có hỗ trợ một tọa độ vừa là bridge vừa có switch hoặc fragile không? Nếu có, khi cầu đóng thì marker được ẩn hay hiển thị ở trạng thái không hoạt động? Nếu không hỗ trợ, mình thống nhất cụ thể những tổ hợp nào sẽ bị loader từ chối (Vy làm phần GUI nma Kiên leader nên nhờ ông chốt lại để hiển thị khớp với luật game)
2. với fragile chồng heavy/split, nhóm muốn coi đây là JSON không hợp lệ, hay vẫn cho load nhưng công tắc không thể kích hoạt khi khối đứng? Mình chốt quy tắc này để tui làm validation, Game và test cùng một kỳ vọng nhen
3. Nhóm chốt bridge ID trong khoảng 0–63, hay chọn giới hạn khác? Giới hạn này có áp dụng đồng nhất cho cả bridge ID và switch targets không? (Kiên thống nhất lại với Duy và Bảo giúp tui nha)
4. tui đã xác minh Switch.set không gây shadow built-in trong các hàm. Hiện B2 đang dùng .set, nên tui giữ để tương thích. Ông muốn giữ tên hiện tại hay thống nhất đổi Python attribute thành setting, giữ JSON key "set" và cập nhật các consumer cùng lúc?

# Quyết định thiết kế đã chốt (hợp đồng giữa các module)

Ai muốn đổi một mục dưới đây phải báo cả nhóm trước (xem `CONTRIBUTING.md`, mục 7) và sửa file này.
Người chốt: Kiên (leader). Cần Duy và Bảo xác nhận mục D3 trong nhóm chat.

## D1. Một ô chỉ có một loại đặc biệt

Các loại ô đặc biệt: `fragile`, `bridge`, `switch` (soft / heavy / split), `goal`.
**Không cho hai loại trở lên cùng một tọa độ.** Loader phải từ chối và nêu rõ tọa độ + hai loại bị trùng.

| Tổ hợp | Kết quả | Lý do |
|---|---|---|
| bridge + switch | Từ chối | Cầu đóng là ô trống thì không bấm được công tắc |
| bridge + fragile | Từ chối | Hai trạng thái chồng nhau, GUI không có cách vẽ rõ |
| bridge + goal | Từ chối | Đích phải luôn đứng được |
| fragile + goal | Từ chối | Thắng khi đứng trên đích, mà đứng trên fragile thì thua |
| fragile + switch (soft) | Từ chối | Chạy được về luật nhưng bỏ cho đơn giản; có thể mở lại sau |
| fragile + switch (heavy / split) | Từ chối | Hai công tắc này chỉ kích hoạt khi đứng, mà đứng trên fragile thì thua nên không bao giờ bấm được |
| switch + goal | Từ chối | Tránh nhập nhằng giữa thắng và kích hoạt |

Hệ quả cho GUI (Vy): mỗi ô chỉ vẽ **một** biểu tượng, không cần lớp phủ hay quy tắc ẩn/hiện marker khi cầu đóng.
Cầu đóng vẽ như ô trống, cầu mở vẽ như ô sàn (đúng luật game).

## D2. Ràng buộc khác của loader

- Ô bắt đầu và ô đích phải là ô đứng được (sàn hoặc đích), không phải ô trống.
- Hai vị trí tách của công tắc split phải là ô sàn thường (không fragile, không bridge), khác nhau.
- Mọi `target` của công tắc phải trỏ tới một bridge ID **có tồn tại** trong màn.
- Lỗi loader: dùng một loại exception riêng của loader, thông báo ghi rõ tọa độ và lý do. Chỉ áp dụng cho
  **file JSON sai**; nước đi rơi khỏi bản đồ vẫn **không** dùng exception (xem `CODING_STANDARDS.md`, mục 3).

## D3. Giới hạn ID

- Bridge ID nằm trong khoảng **0 đến 63** (`0 <= id <= 63`), là số nguyên (không nhận bool, số âm, số thực).
- **Cùng một giới hạn** cho bridge ID và cho các phần tử trong `target` của công tắc.
- Lý do: trạng thái đóng/mở của các cầu lưu thành một bitmask nên State gọn và hashable.

## D4. Tên thuộc tính của công tắc

- Giữ **`Switch.set`** (thuộc tính Python) và **`"set"`** (khóa JSON). Không đổi tên trong đợt này.
- Quy tắc kèm theo: trong `game/` và `gui/`, không dùng `set` làm tên biến cục bộ hoặc tham số; không viết
  `set: set[...]` trong thân dataclass (sẽ che mất hàm `set` có sẵn). Dùng `bridge_ids`, `open_bridges`... cho tập hợp.
- Muốn đổi sang `setting`: làm sau khi B2, C3, D3 đã merge, đổi một lượt ở mọi nơi dùng.

## Việc của từng người

| Người | Việc |
|---|---|
| Gia Hân (B1/B2) | Thêm kiểm tra D1, D2, D3 vào loader; test cho từng tổ hợp bị từ chối |
| Hửu Duy, Bảo Bảo | Xác nhận D3; màn trong `levels/` không được vi phạm D1 và D2 |
| Thảo Vy (D1/D3) | Vẽ một biểu tượng cho mỗi ô, theo D1 |
| Kiên | Cập nhật tài liệu định dạng JSON (nếu có) theo file này; báo nhóm |