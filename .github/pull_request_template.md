## Việc nào? (ID trong file Excel)
<!-- Ví dụ: A3 – Bảng chuyển tư thế -->

## Đã làm gì
<!-- 2–4 gạch đầu dòng, nói ngắn gọn. -->

## Cách kiểm tra
<!-- Lệnh để người review chạy, ví dụ: python -m unittest discover -s tests -t .  /  python main.py levels/g1_basic_01.json -->

## Checklist của người làm
- [ ] Nhánh đúng tên `feature/<tên>-<ID>`, commit message dạng `[ID] ...`
- [ ] PR chỉ làm **một việc**, không lẫn thay đổi không liên quan
- [ ] Đã chạy `python -m unittest discover -s tests -t .` và **xanh**
- [ ] Có test cho logic mới; code có type hint + docstring cho hàm công khai
- [ ] Không đổi `State` / `Game` / `SearchResult` / định dạng JSON (nếu có đổi: đã được cả nhóm đồng ý, ghi rõ ở đây)
- [ ] Không còn `TODO [ID]` của việc này, không còn `print` gỡ lỗi, không có file rác
- [ ] Nếu dùng AI / nguồn ngoài: đã ghi `docs/AI_USAGE_LOG.md` / `docs/REFERENCES.md`
- [ ] Mình giải thích được từng phần của PR này
- [ ] Đã chọn **Reviewer** đúng người trong file Excel và nhắn người đó

## Ghi chú cho người review
<!-- Chỗ nào cần xem kỹ, chỗ nào còn băn khoăn. -->
