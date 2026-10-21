## Việc nào? (ID trong file Excel)
B2 — Ô cầu, công tắc mềm/nặng. Developer: Gia Hân.

## Đã làm gì
- Thêm `game/tiles.py`: immutable terrain snapshot, bridge runtime support, soft/heavy
  activation edges, toggle/permanent nhiều targets và thứ tự tọa độ deterministic.
- `resolve_landing` kiểm support trước/sau effects, loại nước đi đóng cầu dưới khối;
  không mutate State hoặc Level. State/Game/JSON contract giữ nguyên.
- Thêm 45 unit/integration tests và 7 real-roll tests có dependency A1.
- Mở CI cho PR vào `feature/han-B1` để kiểm thử stacked PR B2; giữ CI cho main.

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python main.py levels/g3_switch_demo.json
git diff --check
```
Kết quả kiểm tra lại: **82 discovered = 75 PASS, 7 SKIP, 0 FAIL**.
7 skips do `game.block` của A1 chưa merge. Bản sao tạm bổ sung đúng ba file A1 PR #3:
**105 PASS, 0 SKIP, 0 FAIL**. Smoke loading và diff check thành công.
CI của PR được theo dõi sau khi xuất bản; chưa tự đánh dấu PASS khi chưa có kết quả.

## Checklist của người làm
- [x] Nhánh đúng tên feature/han-B2; commit messages dạng [B2] ...
- [x] PR chỉ chứa diff B2 so với base feature/han-B1, không trộn diff B1
- [x] Đã chạy unittest/regression; skips do dependency đã được ghi rõ
- [x] Có test logic mới, public API có type hints và docstrings
- [x] Không đổi State / Game / SearchResult / định dạng JSON
- [x] Không TODO B2, print gỡ lỗi hoặc artefact tạm trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Gia Hân xác nhận tự hiểu và giải thích được từng phần
- [ ] Đã chọn Reviewer và thông báo nhóm (request được thực hiện sau khi tạo PR)

## Ghi chú cho người review
Reviewer: Bảo Bảo (`BB1311`), xác minh từ tác giả PR E1 #1 và bảng phân công Excel.
Dependency trực tiếp: **B1 #4**. Base tạm: **feature/han-B1**, head: **feature/han-B2**.
Người dùng đã xác nhận cho phép tạo hai PR phụ thuộc nhau trong chat.
Không merge B2 trước B1. Sau B1 merge, kiểm tra lịch sử/diff trước khi chuyển base sang main;
nếu cần rewrite lịch sử hoặc có conflict phải hỏi người dùng, không force-push/reset.

Entry-trigger và thứ tự tọa độ đã được người dùng xác nhận. Kiểm tra kỹ second footprint cell,
heavy không nhận single cube, idempotent permanent và support sau đóng cầu.
A2/C3 cần tạo TileRules một lần và gọi resolve_landing sau roll; None bị loại khỏi successors.
A1 #3 và A2 chưa merge/tích hợp. B2 không triển khai movement/goal/split gameplay.
Self-review chưa phải reviewer approval; trạng thái implementation completed, pending review.
