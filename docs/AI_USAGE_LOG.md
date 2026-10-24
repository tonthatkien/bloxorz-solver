# Nhật ký sử dụng AI (dùng cho Phụ lục của báo cáo)

Đề yêu cầu phụ lục nêu **đã dùng AI tạo sinh (LLM) thế nào và dùng prompt nào**. Ghi ngay khi dùng, đừng đợi cuối kỳ mới nhớ lại.

**Quy tắc**
- Mỗi lần dùng AI cho việc đáng kể (sinh code, giải thích thuật toán, viết/sửa báo cáo, tìm lỗi, dịch...) thì thêm **một dòng**.
- Ghi **prompt** (đủ để người khác hiểu, có thể rút gọn nếu quá dài) và **cách bạn kiểm chứng** kết quả.
- Code do AI sinh ra phải được đọc hiểu, chạy thử và có test trước khi commit.
- Không cần ghi: tra từ, sửa lỗi chính tả vặt.

| Ngày | Người | ID việc | Công cụ (tên + phiên bản nếu biết) | Mục đích | Prompt (tóm tắt hoặc đầy đủ) | Kết quả dùng thế nào | Đã kiểm chứng bằng |
|---|---|---|---|---|---|---|---|
| 14/10/2026 | (ví dụ) A | A3 | Claude | Gợi ý bảng chuyển tư thế | "Cho khối 1x1x2 ... liệt kê 12 trường hợp (tư thế, hướng) → (tư thế, vị trí)" | Dùng làm tham khảo, tự viết lại code | Unit test 12 trường hợp, tự vẽ tay đối chiếu |
| 17/10/2026 | Gia Bảo | E1 | Claude | Hướng dẫn khái niệm tìm kiếm, gợi ý code module đo, so sánh DFS/IDS | "Hướng dẫn em hiểu đề và gợi ý bộ khung làm task E1 ..." | Dùng làm khung phát triển và đối chiếu với bài tập | Chạy test, kiểm tra logic và tự rà soát lại code |
| 17/10/2026 | Hửu Duy | F1 | Claude | Lý thuyết admissible heuristic và tìm code mẫu tính khoảng cách trên lưới | "Nêu ra kiến thức và code mẫu về cách tính khoảng cách Manhattan cho vật thể khối chữ nhật 1x1x2 trên lưới; điều kiện admissible" | Đọc hiểu tài liệu lý thuyết và code mẫu được tra cứu; chọn lọc kiến thức, tự xây dựng lại hàm chi phí, viết toàn bộ code heuristic và tài liệu | Tự vẽ hình tính tay trên giấy để kiểm chứng công thức, viết bộ unit test kiểm tra |
|  |  |  |  |  |  |  |  |