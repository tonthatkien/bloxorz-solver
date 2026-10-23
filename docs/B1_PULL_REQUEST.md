## Việc nào? (ID trong file Excel)
B1 — Bộ nạp JSON mở rộng & ô dễ vỡ. Developer: Gia Hân; reviewer: Kiên (`tonthatkien`).

## Đã làm gì
- Loader kiểm tra JSON grid/tọa độ, bridge IDs/targets, modes, permanent và split metadata;
  giữ public Level/Bridge/Switch, key JSON và bridge bitmask theo ID.
- Helper fragile kiểm trọng lượng trên trạng thái sau di chuyển; State bất biến/hashable giữ nguyên.
- Phản hồi review: dùng chung Cell từ game.state, giữ Switch.set có chủ đích và thêm regression
  cho constructor/JSON permanent, ID và từng loại overlap.
- Không áp đặt ID<64 hoặc cấm overlap: người dùng chọn giữ schema và chờ nhóm thống nhất.

## Cách kiểm tra
```bash
python -m unittest tests.test_level_validation tests.test_fragile
python -m unittest discover -s tests -t .
python main.py levels/g3_switch_demo.json
git diff --check
```
Kết quả ngày 23/10: loader/fragile **26 pass**; cả branch (đã chứa B2):
**89 discovered = 82 pass, 7 skip A1, 0 fail**.
Bản sao ghép A1 từ main: **115 pass, 0 skip/fail**. Smoke và diff check thành công.

## Checklist của người làm
- [x] Nhánh/commit đúng quy ước B1
- [x] Có regression và đã chạy test thực tế; skips/dependency được ghi rõ
- [x] Public API có type hints/docstrings, không đổi State/Game/SearchResult/JSON domain
- [x] Không TODO B1, print gỡ lỗi hoặc artefact tạm trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Gia Hân/reviewer xác nhận hiểu code và đồng thuận chính sách schema còn mở

## Ghi chú cho người review
A1 #3 đã merge vào main và đã sửa mapping #/., không cần workaround parser cũ.
B2 #5 đã được merge vào nhánh B1 trước lần sửa này; giữ nguyên commit và merge đó.
Game A2/C3 chưa tích hợp helper; không tự merge hoặc approve PR này.

Đề xuất ID<64 và cấm bridge/switch/fragile overlap chờ nhóm chốt với GUI/Game theo
CONTRIBUTING mục 7. Giữ .set vì là public attribute/JSON key, không shadow built-in set().
Đã tách test overlap thành từng trường hợp và chứng minh soft/heavy trên fragile đúng thứ tự
support/effects. Không sửa test sang reject khi chưa có quyết định đổi schema.

ID lớn vẫn có rủi ro cấp phát runtime; test ID10**9 chỉ parse metadata, không dịch bit lớn.
Chi tiết và bằng chứng ở docs/B1_IMPLEMENTATION_REPORT.md, phần cập nhật 23/10/2026.
