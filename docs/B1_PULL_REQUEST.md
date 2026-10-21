## Việc nào? (ID trong file Excel)
B1 — Bộ nạp JSON mở rộng & ô dễ vỡ. Developer: Gia Hân.

## Đã làm gì
- Mở rộng validation trong `game/level_loader.py`: kiểu dữ liệu, tọa độ, grid/goal,
  bridge IDs/targets, switch modes/permanent và split metadata; giữ API và JSON schema.
- Thêm `game/fragile.py`: helper pure kiểm tra STAND trên fragile theo state sau di chuyển.
- Thêm 21 test methods (nhiều validation subtests), report và AI usage log.
- Xác minh State immutable/hashable và bridge masks; không sửa State/Game/A1/GUI/solver.

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python main.py
python main.py levels/g3_switch_demo.json
git diff --check
```
Thực tế Python 3: **30 tests PASS, 0 fail, 0 skip**; cả hai smoke commands nạp thành công.
Compatibility suite với ba file A1 trong thư mục tạm: **53 tests PASS**;
đã kiểm tra chuyển đổi symbol JSON→A1 và roll/goal. Chưa có Game end-to-end do A2 thiếu.

## Checklist của người làm
- [x] Nhánh đúng tên `feature/<tên>-<ID>`, commit message dạng `[ID] ...`
- [x] PR chỉ làm một việc, không lẫn thay đổi B2
- [x] Đã chạy unittest discovery và xanh
- [x] Có test cho logic mới; public API có type hint + docstring
- [x] Không đổi State / Game / SearchResult / định dạng JSON
- [x] Không còn TODO B1, print gỡ lỗi hoặc file rác trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Gia Hân đã tự đọc hiểu và giải thích được từng phần (cần con người xác nhận)
- [ ] Đã request reviewer và thông báo nhóm (chỉ đánh dấu khi đã thực hiện đủ)

## Ghi chú cho người review
Reviewer: Kiên (`tonthatkien`). Dependency: A1 #3 còn open, A2 chưa triển khai.
Xem `docs/B1_IMPLEMENTATION_REPORT.md` để có audit, thiết kế, lỗi đã sửa và bằng chứng test.
Kiểm tra kỹ validation không ép bool/float thành int, bit i theo bridge ID, alias JSON,
và helper fragile sau roll. Fragile helper chỉ kiểm weight; support đầy đủ do B2 cung cấp.
Overlay khác loại không bị cấm tùy tiện; special tiles phải nằm trên # như README.
Không truyền grid JSON trực tiếp vào A1 Board.from_strings (. và # đang ngược nghĩa).
PR lớn hơn ~300 dòng do tests/validation của cùng B1; chưa bao gồm B2 hay Game integration.
CI cần được kiểm tra sau khi mở PR. Không merge trước dependency/review/CI.
