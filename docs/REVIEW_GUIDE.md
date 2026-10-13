# Hướng dẫn review

Review không phải để "bắt lỗi" mà để: (1) **code đúng**, (2) **cả hai người cùng hiểu code**, (3) **sẵn sàng cho vấn đáp**.
Người review cũng phải giải thích được phần mình đã duyệt.

## 1. Ai review ai
- Xem cột **Người review** trong file Excel, hoặc [`REVIEW_ASSIGNMENTS.md`](REVIEW_ASSIGNMENTS.md).
- Không ai review việc của chính mình. Cần đổi người review thì sửa trong Excel và báo nhóm.
- Thời hạn: **review trong 24 giờ** kể từ khi được báo. Bận thì báo sớm để đổi người.

## 2. Quy trình của người review
1. Đọc **mô tả PR** (làm gì, cách kiểm tra). Đọc lại mô tả việc trong Excel (cột *Công việc*, *Phụ thuộc*).
2. **Chạy thật**:
   ```bash
   git fetch origin
   git checkout feature/an-A3
   pip install -r requirements.txt
   python -m unittest discover -s tests -t .
   python main.py            # hoặc cách kiểm tra ghi trong PR
   ```
3. Đọc code theo checklist ở mục 3 và mục 4. Đọc **cả test**: test có thật sự kiểm tra điều quan trọng không?
4. Viết nhận xét trên GitHub (*Files changed* → bấm dấu `+` cạnh dòng code, hoặc *Review changes* ở góc trên):
   - **Approve**: đủ điều kiện ở mục 5, ghi ít nhất một câu nói đã kiểm tra gì.
   - **Request changes**: có `[must]` cần sửa.
   - **Comment**: mới chỉ hỏi/góp ý, chưa quyết định.
5. Cập nhật cột **Trạng thái review** trong Excel: *Đang review* → *Cần sửa* hoặc *Đã duyệt*.
6. Tác giả sửa xong thì **xem lại đúng những chỗ đã yêu cầu sửa**, rồi Approve.

## 3. Checklist chung (mọi PR)
- [ ] PR chỉ làm **một việc** và đúng với việc có ID trong Excel; không lẫn thay đổi không liên quan.
- [ ] Tuân thủ `CONTRIBUTING.md` (nhánh, commit message, mô tả PR) và `docs/CODING_STANDARDS.md`.
- [ ] Chạy được. Test **xanh** trên máy mình (không chỉ tin CI).
- [ ] Có **test mới** cho logic mới; test kiểm tra hành vi thật, không chỉ "chạy qua".
- [ ] Không đụng "hợp đồng" (`State`, `Game`, `SearchResult`, JSON) trừ khi đã được cả nhóm đồng ý.
- [ ] Không có code chết, `print` gỡ lỗi, file rác, bí mật.
- [ ] Nếu có code từ AI/nguồn ngoài: đã ghi `docs/AI_USAGE_LOG.md` / `docs/REFERENCES.md`.
- [ ] Mình **hiểu** đoạn code này và có thể giải thích lại. Chưa hiểu → hỏi (`[question]`), đừng Approve.

## 4. Checklist theo loại việc

**Game core / ô nâng cao / công tắc tách (`game/`)**
- [ ] Bảng chuyển tư thế đúng cho cả **12 trường hợp** (3 tư thế × 4 hướng), có test.
- [ ] Nước đi không hợp lệ bị loại: ra ngoài bản đồ, rơi xuống ô trống, **đứng trên ô dễ vỡ**, cầu đóng.
- [ ] Thắng **chỉ khi khối đứng** trên ô đích (nằm vắt qua đích thì không thắng; cube đơn không thắng).
- [ ] Công tắc: mềm (nằm/đứng đều kích hoạt), nặng (chỉ đứng), tách (chỉ đứng, dịch chuyển + tách). Có cả `toggle` và `permanent`.
- [ ] `State` vẫn bất biến, hashable, đã **chuẩn hóa** (không sinh hai state khác nhau cho cùng một tình huống).
- [ ] `get_successors` không có tác dụng phụ, thứ tự `U, D, L, R, S` cố định.

**Solver (`solvers/`)**
- [ ] Đúng thuật toán: BFS dùng hàng đợi; DFS/IDS xử lý visited/độ sâu; UCS dùng hàng đợi ưu tiên theo **g**; A* theo **g + h**.
- [ ] Không bị lặp vô hạn; visited kiểm tra **đúng lúc** (khi thêm vào hay khi lấy ra, nhất quán với tính tối ưu của thuật toán đó).
- [ ] `expanded` đếm đúng một cách (khi lấy khỏi frontier), có gọi `checker.tick`.
- [ ] Lời giải **hợp lệ**: có test tự đi lại `path` bằng `get_successors` và tới đích.
- [ ] Tối ưu: BFS/UCS/A* cho độ dài/chi phí tối ưu như mong đợi; A* **không** ra chi phí lớn hơn UCS (nếu có thì heuristic không admissible).
- [ ] Trả đủ trường của `SearchResult`; không `print` trong solver.
- [ ] Heuristic có lập luận admissible (và consistent nếu có) viết ở docstring.

**GUI (`gui/`)**
- [ ] Hiển thị đủ: ô sàn, ô trống, đích, ô dễ vỡ, cầu (đóng/mở), 3 loại công tắc, khối ở 3 tư thế, 2 cube khi tách + cube đang điều khiển.
- [ ] Có các nút: New Game, Restart, Solve BFS / DFS / UCS / A*; hiển thị số liệu (time, memory, nodes, length).
- [ ] Chơi tay đúng luật (do gọi game core, **không tự cài lại luật** trong GUI).
- [ ] Không đứng hình khi solver chạy lâu; thông báo thắng/thua rõ ràng.

**Thực nghiệm (`experiments/`)**
- [ ] Dùng **cùng bộ test** và cùng `Limits` cho mọi solver; chạy lặp lại được (seed nếu có).
- [ ] Đo đúng: thời gian (không bật tracemalloc), bộ nhớ đỉnh, nút mở rộng, độ dài lời giải; xử lý `solved=False` (timeout/giới hạn nút) rõ ràng trong bảng.
- [ ] Biểu đồ có tiêu đề, nhãn trục, đơn vị, chú thích; dễ đọc.

**Bộ test case (màn chơi)**
- [ ] Chia đúng 4 nhóm độ khó; tên file đúng quy ước; nạp được bằng loader.
- [ ] Màn **giải được** (có ít nhất một lời giải, kiểm bằng BFS); độ khó tăng dần hợp lý.

**Báo cáo (`Report.pdf`/bản nháp)**
- [ ] Đủ mục theo đề: phân công + % hoàn thành, mô tả thuật toán, hình thức hóa bài toán (state, action, transition, goal, cost, heuristic, visited), thực nghiệm, tài liệu tham khảo, phụ lục AI.
- [ ] Số liệu trong bảng/biểu đồ **khớp** với kết quả chạy thật; nhận xét có lập luận, không chỉ mô tả bảng.
- [ ] Công thức/ký hiệu nhất quán với code; chính tả, định dạng, đánh số hình/bảng.
- [ ] Trích dẫn đầy đủ, không có đoạn sao chép nguyên văn.

**Video**
- [ ] Đủ hai phần: giao diện (bố cục, các loại ô, các tư thế, nút điều khiển) và tính năng (chơi tay: lăn khối, bật công tắc, thắng/thua; chạy solver, replay lời giải).
- [ ] Có phụ đề hoặc thuyết minh rõ; âm thanh/hình ảnh nhìn rõ; link YouTube công khai và đã ghi vào báo cáo.

## 5. Khi nào được Approve
Approve khi **tất cả** đúng:
1. Chạy được và test xanh trên máy người review.
2. Không còn `[must]` nào chưa được xử lý.
3. Người review **hiểu và giải thích được** những gì PR làm.

## 6. Cách viết nhận xét tốt
Dùng nhãn ở đầu mỗi nhận xét:
- `[must]` bắt buộc sửa trước khi merge (sai logic, thiếu test quan trọng, vi phạm hợp đồng...).
- `[suggest]` nên sửa, tác giả có thể từ chối nếu có lý do.
- `[question]` hỏi để hiểu, chưa phải yêu cầu sửa.
- `[nit]` chỗ lặt vặt (đặt tên, định dạng), không chặn merge.

Nguyên tắc: **nói về code, không nói về người**; **cụ thể** (dòng nào, vì sao, gợi ý cách sửa); **lịch sự**; **một nhận xét một ý**.

| Nên | Không nên |
|---|---|
| `[must] Ở dòng 42, nước đi lên ô dễ vỡ khi khối đứng vẫn được trả về, nên bỏ nó khỏi successors. Test mẫu: ...` | "Code này sai." |
| `[question] Vì sao đếm expanded trước khi kiểm tra đích? Có ảnh hưởng số liệu so sánh không?` | "Làm lại đi." |
| `[nit] Đổi tên biến x2 thành next_row cho dễ đọc.` | "LGTM" mà chưa chạy thử. |

## 7. Dành cho tác giả khi nhận review
- Cảm ơn và **trả lời từng nhận xét**: đã sửa (kèm commit), hoặc giải thích vì sao không sửa.
- Đừng tranh luận qua nhiều vòng bằng chữ: không thống nhất sau 1–2 lượt thì **gọi nhau 5 phút** hoặc hỏi trưởng nhóm.
- Sau khi sửa xong, báo người review và đổi trạng thái trong Excel.

## 8. Ý kiến khác nhau
Không thống nhất được trong 24 giờ → hỏi **trưởng nhóm**. Trưởng nhóm quyết định và ghi lại ngắn gọn lý do trong PR.
Nếu vấn đề là về "hợp đồng" giữa các module thì áp dụng quy trình ở `CONTRIBUTING.md`, mục 7.
