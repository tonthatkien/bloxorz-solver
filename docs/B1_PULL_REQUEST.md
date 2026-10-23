## Việc nào? (ID trong file Excel)
B1 — Bộ nạp JSON mở rộng & ô dễ vỡ. Người làm: Gia Hân; reviewer: Kiên (`tonthatkien`).

## Đã làm gì
- Extended JSON loader/validation, bridge initial mask và split metadata theo schema nhóm.
- Fragile helper theo weight sau di chuyển; giữ State/Level/Game API.
- Giữ toàn bộ sửa B1 từ 7308a83: shared Cell, Switch.set, regression ID/overlap/JSON.
- Revert nội dung merge B2 145de62 bằng ee81296, cập nhật A1 đã merge từ main.
  B1 hiện không có tiles.py, test/tài liệu B2 hoặc CI chỉ phục vụ B2.

## Cách kiểm tra
```bash
python -m unittest discover -s tests -t .
python main.py
python main.py levels/g3_switch_demo.json
git diff origin/main...feature/han-B1 --name-only
git diff --check
```
Sau tách và cập nhật main/A1: **61 PASS, 0 FAIL, 0 SKIP**.
Hai smoke commands thành công. Blob code/tests B1 khớp backup 7308a83.
Diff chỉ có 7 file thuộc B1. CI cần được xác minh trên head mới sau push.

## Checklist của người làm
- [x] Branch/commit đúng quy ước B1
- [x] PR chỉ chứa thay đổi B1 khi so với main
- [x] Đã chạy toàn bộ unittest và xanh
- [x] Có unit test cho logic mới; type hints/docstrings được giữ
- [x] Không đổi State/Game/SearchResult/định dạng JSON
- [x] Không TODO B1, print gỡ lỗi hoặc file rác trong diff
- [x] Đã ghi docs/AI_USAGE_LOG.md
- [ ] Người làm/reviewer xác nhận hiểu toàn bộ bản cập nhật
- [ ] Reviewer đã kiểm tra lại head sau sửa topology và thông báo nhóm

## Ghi chú cho người review
Giữ PR #4 và mọi review/comment. PR #5 cũ đã merged vào B1; revert chỉ hoàn tác nội dung,
không xóa lịch sử. B2 chuyển sang feature/han-B2-review với PR mới thay thế phần review B2.
Reviewer B1 Kiên, B2 Bảo Bảo đã được Gia Hân xác nhận lại.
ID limit/overlap giữ schema hiện tại và chờ nhóm chốt. A1 đã merge; A2/C3 tích hợp sau.
Không tự approve/merge hoặc resolve review threads. Không merge PR B2 mới vào B1.
