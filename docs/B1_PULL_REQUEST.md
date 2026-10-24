## Việc nào? (ID trong file Excel)
B1 — Bộ nạp JSON mở rộng & ô dễ vỡ. Gia Hân; reviewer Kiên (`tonthatkien`).

## Đã làm gì
- Kiểm tra JSON mở rộng, sao chép dữ liệu đầu vào và tính initial bridge mask; helper fragile.
- Áp dụng D1–D3 từ PR #9 theo yêu cầu: cấm chồng các ô đặc biệt, đích split trên hai ô sàn
  thường khác nhau, bridge ID/targets int 0–63 và target phải tồn tại.
- Thêm `LevelValidationError(ValueError)` cho JSON syntax/encoding/schema sai; giữ lỗi I/O
  và nguyên nhân syntax. Giữ `Switch.set`, JSON key "set" và các dataclass public theo D4.
- Giữ phần sửa tách PR trước đây; B1 không chứa runtime/test B2, không sửa code A1/A2.

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python main.py
python main.py levels/g3_switch_demo.json
git diff origin/main...feature/han-B1 --name-only
git diff --check
```
B1: **63 PASS, 0 FAIL, 0 SKIP**. Smoke thành công; ba JSON hiện có vẫn load được.
Regression kiểm từng cặp ô đặc biệt, mọi switch kind, ID0/63/64 và ID rất lớn, targets,
đích split, lỗi loader và tương thích `Switch.set`. CI xem trong Checks trên head mới.

## Checklist của người làm
- [x] Branch/commit đúng quy ước B1
- [x] PR chỉ chứa B1 khi so với main
- [x] Đã chạy toàn bộ unittest và xanh
- [x] Có tests; hàm/lớp công khai có type hints/docstrings
- [x] Không đổi State/Game/SearchResult; validation JSON tuân theo D1–D4 PR #9
- [x] Không TODO B1, print gỡ lỗi hoặc file rác trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Người làm/reviewer xác nhận hiểu toàn bộ bản cập nhật
- [ ] Reviewer kiểm tra head mới và thông báo nhóm
- [ ] Xác nhận quy trình đổi hợp đồng theo CONTRIBUTING §7 hoàn tất ở PR #9/nhóm chat

## Ghi chú cho người review
Dependency hợp đồng: **PR #9** (`docs/DECISION.md`), chưa merge tại thời điểm rà soát.
Gia Hân yêu cầu triển khai theo quyết định này; chưa có bằng chứng Duy/Bảo xác nhận D3
trong chat hoặc cả nhóm đã hoàn tất §7. Cần chốt trước khi merge, không đánh dấu thay nhóm.

Giữ PR #4 và các review/comment. B2 review riêng tại **PR #8**, base feature/han-B1.
**Không merge B2 vào B1.** Sau B1 merge, kiểm tra ancestry/diff trước khi chuyển base B2.
A1 đã merge; tích hợp Game A2/C3 làm sau. Không tự approve/merge/resolve review threads.
