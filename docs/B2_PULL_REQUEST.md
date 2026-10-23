## Việc nào? (ID trong file Excel)
B2 — Ô cầu, công tắc mềm/nặng. Gia Hân; reviewer Bảo Bảo (`BB1311`).

## Đã làm gì
- Tạo feature/han-B2-review từ B1 đã sửa, phục hồi runtime bridge/soft/heavy,
  toggle/permanent nhiều targets và immutable TileRules từ backup B2 mới nhất.
- Giữ nguyên code/tests B2 tại 7308a83, gồm hai regression soft/heavy trên fragile
  đã bổ sung sau merge cũ. Không sửa State/Game/schema hay logic gameplay.
- Chỉ thêm B2 files, AI usage B2 và CI phục vụ PR base feature/han-B1.
- PR này thay thế phần review B2 của PR #5 cũ (đã merged vào B1, nay nội dung đã revert).

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python main.py levels/g3_switch_demo.json
git diff feature/han-B1...feature/han-B2-review --name-only
git diff --check
```
B2-review: **115 PASS, 0 FAIL, 0 SKIP** (đã có A1 từ main).
B1 chạy riêng: **61 PASS, 0 FAIL, 0 SKIP**.
B2 code/test blobs khớp backup 7308a83; B1 fixes không bị sửa. Smoke và diff check thành công.

## Checklist của người làm
- [x] Nhánh/commit theo quy ước B2, giữ nguyên nhánh B2 cũ
- [x] Diff so với base B1 chỉ chứa B2, không duplicate changes B1
- [x] Đã chạy toàn bộ unit/regression tests thực tế
- [x] Có tests cho bridges, footprint, soft/heavy, toggle/permanent, immutability
- [x] Không đổi State/Game/SearchResult/JSON contract
- [x] Không TODO B2, print gỡ lỗi hoặc file rác trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Người làm/reviewer xác nhận hiểu toàn bộ bản cập nhật
- [ ] Reviewer đã xem head mới và được thông báo trong nhóm

## Ghi chú cho người review
Dependency: **B1 #4**. Base: feature/han-B1; head: feature/han-B2-review.
Reviewer B2 BB1311 được Gia Hân xác nhận lại sau khi đối chiếu tracker.
PR #5 và branch B2 cũ được giữ nguyên; không sửa/xóa lịch sử đó.
**Không merge PR B2 này vào B1.** Chờ B1 merge vào main, kiểm tra ancestry/diff rồi chuyển
base sang main nếu chỉ còn B2. Nếu cần rewrite lịch sử phải xin phép người dùng trước.
Không tự approve/merge. CI cần xác minh trên head mới sau khi tạo PR.
A1 đã merge; tích hợp Game A2/C3 vẫn là bước sau, ngoài phạm vi sửa Git này.
