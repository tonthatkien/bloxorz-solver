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
| 17/10/2026 | Gia Bảo | E1 | Claude | Hướng dẫn khái niệm tìm kiếm, gợi ý code module đo, so sánh DFS/IDS | "Hướng dẫn em hiểu đề và gợi ý bộ khung làm task E1 (module đo, chốt DFS/IDS); viết code; chỉnh lại cho khớp base.py" | Dùng làm cơ sở, chỉnh theo base.py của nhóm | Chạy unittest, tự giải 6 bài tập trên giấy |
|  |  |  |  |  |  |  |  |

