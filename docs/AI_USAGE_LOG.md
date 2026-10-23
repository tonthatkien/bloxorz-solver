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
| 21/10/2026 | Gia Hân | B1 | Codex (GPT-6) | Audit, loader validation, fragile helper, test và self-review | "Triển khai B1 trước B2; giữ State/Game/schema, bảo toàn thay đổi chưa commit, test và PR riêng" | Sinh code/test/report trong worktree riêng; chưa có phê duyệt con người | 30 unittest pass; compatibility A1 53 pass; 2 smoke commands pass; Gia Hân và reviewer còn phải đọc hiểu/duyệt |
| 21/10/2026 | Gia Hân | B2 | Codex (GPT-6) | Bridge/switch helpers, unit/integration tests và hai vòng self-review | "Triển khai B2 sau B1; entry-trigger được người dùng xác nhận, giữ nguyên Game/State và không làm C1/C2" | Sinh TileRules, tests, report và PR body; chưa xuất bản do quyền GitHub | Branch: 75 pass/7 skip A1; bản sao cùng A1: 105 pass/0 skip; smoke và diff check pass; chờ con người đọc hiểu/review |
| 21/10/2026 | Gia Hân | B1/B2 | Codex (GPT-6) | Kiểm tra lại code, tests, branch/PR và dependency | "Kiểm tra B1/B2, tạo hai PR đúng template; cho phép B2 base B1; không rewrite/force-push" | B1 PR #4, request Kiên, CI xanh; cập nhật CI và PR body B2 cho stacked review | B1 30 pass; B2 75 pass/7 skip A1; compatibility A1 105 pass; git diff/checksum; chờ human review |
