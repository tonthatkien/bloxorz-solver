## Việc nào? (ID trong file Excel)
B2 — Ô cầu, công tắc mềm/nặng. Gia Hân; reviewer Bảo Bảo (`BB1311`).

## Đã làm gì
- Runtime bridge/soft/heavy, toggle/permanent nhiều targets, immutable TileRules và
  landing rules; snapshot và State không bị thay đổi tại chỗ.
- Cập nhật dependency B1 theo D1–D4 PR #9 bằng merge bình thường B1 → B2, không rewrite.
- Thay sáu fixture/test chồng ô bằng cấu hình hợp lệ. Giữ kiểm tra fragile, toàn footprint,
  rơi trước effects và rơi sau khi switch đóng cầu đang đỡ; thêm regression ID63/hash State.
- Giữ Switch.set/JSON "set", entry-trigger, thứ tự tọa độ; không đổi runtime game/tiles.py
  trong lần sửa này. Giữ đủ bảy integration tests dùng roll thật A1.

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python -m unittest tests.test_tiles tests.test_tiles_a1
python main.py levels/g3_switch_demo.json
git diff feature/han-B1...feature/han-B2-review --name-only
git diff --check
```
Toàn branch: **118 PASS, 0 FAIL, 0 SKIP**. Riêng B2: **55 PASS**; B1 riêng: **63 PASS**.
Smoke và diff/style pass. CI xem trong Checks trên head mới.

## Checklist của người làm
- [x] Branch/commit theo quy ước B2, giữ nhánh B2 cũ
- [x] Diff so với B1 chỉ chứa B2; thay đổi B1 nằm ở dependency
- [x] Đã chạy toàn bộ unittest và xanh
- [x] Có tests cho bridge, footprint, soft/heavy, toggle/permanent, immutability
- [x] Không đổi State/Game/SearchResult; nhận Level theo validation D1–D4 PR #9
- [x] Không TODO B2, print gỡ lỗi hoặc file rác trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Người làm/reviewer xác nhận hiểu toàn bộ bản cập nhật
- [ ] Reviewer kiểm tra head mới và thông báo nhóm
- [ ] Quy trình đổi hợp đồng theo CONTRIBUTING §7 hoàn tất ở PR #9/nhóm chat

## Ghi chú cho người review
Dependency: **B1 #4**; hợp đồng: **PR #9**, chưa merge tại thời điểm rà soát.
Gia Hân yêu cầu áp dụng D1–D4; chưa có bằng chứng Duy/Bảo xác nhận D3 trong chat
hoặc cả nhóm đã hoàn tất §7. Cần chốt trước merge, không xác nhận thay nhóm.

Base feature/han-B1; head feature/han-B2-review. Reviewer BB1311 đã được Gia Hân xác nhận.
PR #5 và branch B2 cũ giữ nguyên; PR này thay thế phần review B2 của PR #5.
**Không merge PR này vào B1.** Sau B1 merge vào main, kiểm tra ancestry/diff rồi mới
chuyển base B2; nếu cần rewrite phải xin phép. Không tự approve/merge/resolve threads.
A1 đã merge; tích hợp Game A2/C3 là bước sau, ngoài phạm vi B1/B2.
