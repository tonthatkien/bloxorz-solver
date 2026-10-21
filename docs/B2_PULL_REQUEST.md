## Việc nào? (ID trong file Excel)
B2 — Ô cầu, công tắc mềm/nặng. Developer: Gia Hân.

## Đã làm gì
- Thêm `game/tiles.py`: snapshot terrain bất biến, bridge runtime support, soft/heavy
  activation edges, toggle/permanent nhiều targets và deterministic coordinate ordering.
- `resolve_landing` kiểm tra support trước/sau switch effects, loại nước đi đóng cầu
  đang đỡ khối; giữ State input và Level không đổi.
- Thêm 45 unit/integration tests cùng B1 và 7 real-roll tests chạy khi có A1.
- Thêm report và AI log; không sửa State/Game/GUI/solver và không triển khai split gameplay.

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python main.py levels/g2_fragile_01.json
python main.py levels/g3_switch_demo.json
git diff --check
```
Kết quả local: **82 discovered = 75 PASS, 7 SKIP, 0 FAIL**; skips là A1 chưa có.
Trong bản sao tạm thêm ba file A1 từ PR #3: **105 PASS, 0 SKIP, 0 FAIL**.
Hai smoke commands nạp thành công. Xem log và cách tái hiện ở B2_IMPLEMENTATION_REPORT.md.

## Checklist của người làm
- [x] Nhánh feature/han-B2, commit message dạng [B2] ...
- [x] Diff so với base B1 chỉ chứa B2
- [x] Đã chạy unittest và regression; 7 test thiếu A1 được ghi rõ skip, đã kiểm chứng với A1
- [x] Logic mới có test, type hints và docstrings; git diff --check sạch
- [x] Không đổi State / Game / SearchResult / định dạng JSON
- [x] Không TODO B2, print gỡ lỗi hoặc artefact tạm trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Gia Hân xác nhận hiểu và giải thích được code
- [ ] B1 đã merge, diff so main chỉ còn B2, test lại trên main mới
- [ ] Đã request reviewer đúng người và nhắn nhóm
- [ ] CI xanh (chưa có PR remote)

## Ghi chú cho người review
Reviewer: Bảo Bảo (`BB1311`, đã đối chiếu tác giả PR E1).
Dependency: B1, A1 #3; A2/C3 tích hợp sau. Chờ B1 merge trước khi mở PR vào main.
Nếu B1 squash merge, tạo branch từ main và cherry-pick riêng B2; giữ branch cũ để phục hồi,
không force-push. Không mở PR B2 vào main chứa cả B1.

Entry-trigger và thứ tự tọa độ đã được người dùng xác nhận. Cần xem kỹ pre/post support,
heavy không nhận single cube, second footprint cell và permanent set là idempotent.
Game gọi TileRules.from_level một lần, resolve_landing sau roll và loại None khỏi successors.
B2 không có movement/goal/split gameplay. Self-review chưa phải reviewer approval.
