# Quy định làm việc nhóm

Đọc hết file này trước khi viết dòng code đầu tiên. Có 6 người cùng sửa một repo, nên các quy định dưới đây
là để **không ai làm hỏng việc của ai** và để **ai cũng giải thích được code của mình khi bị vấn đáp**.

Tài liệu đi kèm: [`docs/GIT_GUIDE.md`](docs/GIT_GUIDE.md) (hướng dẫn Git từng bước),
[`docs/CODING_STANDARDS.md`](docs/CODING_STANDARDS.md) (quy ước viết code),
[`docs/REVIEW_GUIDE.md`](docs/REVIEW_GUIDE.md) (cách review),
[`docs/REVIEW_ASSIGNMENTS.md`](docs/REVIEW_ASSIGNMENTS.md) (ai làm gì, ai review ai),
[`docs/AI_USAGE_LOG.md`](docs/AI_USAGE_LOG.md) và [`docs/REFERENCES.md`](docs/REFERENCES.md) (ghi nhận AI và nguồn tham khảo cho báo cáo).

---

## 1. Năm quy tắc không được vi phạm

1. **Không push thẳng lên `main`.** Mọi thay đổi đi qua nhánh + Pull Request (PR).
2. **Không tự merge PR của mình** khi chưa có người review (ghi trong file Excel) bấm *Approve*.
3. **Không tự ý đổi "hợp đồng"** giữa các module: `State` (`game/state.py`), 3 hàm của `Game`
   (`initial_state`, `is_goal`, `get_successors`), `SearchResult` (`solvers/base.py`), định dạng JSON màn chơi.
   Muốn đổi → xem mục 7.
4. **Không push code không chạy được** vào `main`: test phải xanh, `python main.py` phải chạy.
5. **Không commit file rác / bí mật**: `.venv/`, `__pycache__/`, file CSV kết quả lớn, token, file cá nhân.

---

## 2. Quy trình cho một việc (từ lúc nhận đến lúc xong)

Mỗi việc trong file Excel có ID (ví dụ `A3`), **một người làm**, **một người review**.

| Bước | Ai | Làm gì |
|---|---|---|
| 1 | Người làm | Đổi trạng thái việc trong Excel thành **Đang làm**. `git checkout main && git pull`. |
| 2 | Người làm | Tạo nhánh `feature/<tên>-<ID>` (ví dụ `feature/an-A3`). |
| 3 | Người làm | Code + viết test + chạy `python -m unittest discover -s tests -t .` cho tới khi xanh. |
| 4 | Người làm | Commit nhỏ, rõ (xem mục 3), `git push`, mở **Pull Request** vào `main`, điền đủ mẫu PR. |
| 5 | Người làm | Nhắn người review trong nhóm chat (kèm link PR). Đổi cột **Trạng thái review** thành *Chưa review*. |
| 6 | Người review | Review trong **24 giờ** (xem `docs/REVIEW_GUIDE.md`). Chuyển *Đang review* → *Cần sửa* hoặc *Đã duyệt*. |
| 7 | Người làm | Nếu *Cần sửa*: sửa trong **24 giờ**, push thêm commit vào cùng nhánh, báo lại. |
| 8 | Người làm | Khi *Đã duyệt* + CI xanh: bấm **Squash and merge**, xóa nhánh, đổi trạng thái việc thành **Xong**. |

**Một PR = một việc** (hoặc 2–3 việc rất nhỏ liền nhau). PR nên **dưới ~300 dòng thay đổi**; to hơn thì tách ra.

---

## 3. Nhánh, commit, Pull Request

- **Nhánh:** `feature/<tên>-<ID>` (thêm tính năng), `fix/<tên>-<mô-tả-ngắn>` (sửa lỗi),
  `docs/<tên>-<mô-tả>` (tài liệu / báo cáo). Ví dụ: `feature/an-A3`, `fix/binh-bfs-visited`.
- **Commit message:** `[ID] Động từ + nội dung ngắn`, ví dụ `[A3] Add orientation transition table`.
  Commit nhỏ, mỗi commit làm một ý, **không** commit kiểu `update`, `fix`, `abc`.
- **Tiêu đề PR:** `[ID] Tên việc` (ví dụ `[A3] Bảng chuyển tư thế`). Điền theo mẫu có sẵn
  (`.github/pull_request_template.md`): làm gì, cách kiểm tra, checklist.
- **Merge:** dùng **Squash and merge** để lịch sử `main` gọn (một việc = một commit).
- **Trước khi mở PR:** `git fetch && git merge origin/main` vào nhánh của mình, giải quyết conflict ở máy mình.

---

## 4. Review (tóm tắt, chi tiết ở `docs/REVIEW_GUIDE.md`)

- **Người review** của từng việc được chỉ định trong cột *Người review* của file Excel. Không ai review việc của chính mình.
- Review phải **chạy code thật** (checkout nhánh, chạy test), không chỉ đọc lướt. Không được "LGTM" suông:
  mỗi lần Approve phải ghi **ít nhất một câu** nói đã kiểm tra điều gì.
- Gắn nhãn nhận xét: `[must]` (bắt buộc sửa), `[suggest]` (nên sửa), `[question]` (hỏi để hiểu), `[nit]` (lặt vặt, không chặn).
- Ý kiến khác nhau mà không thống nhất được trong 24 giờ → hỏi **trưởng nhóm**, trưởng nhóm quyết định.
- **Quan trọng cho vấn đáp:** người review cũng phải giải thích được đoạn code mình đã duyệt.
- Việc không phải code (báo cáo, video, bộ test) cũng được review: người review đọc/xem và kiểm tra theo checklist trong `REVIEW_GUIDE.md`.

---

## 5. "Xong" nghĩa là gì (Definition of Done)

Một việc chỉ được đánh dấu **Xong** khi đủ tất cả:

- [ ] Code chạy được, không còn `TODO [ID]` của việc đó trong code.
- [ ] Có unit test cho phần logic mới (game, solver) và `python -m unittest discover -s tests -t .` **xanh**.
- [ ] Tuân thủ `docs/CODING_STANDARDS.md` (type hint, docstring cho hàm công khai, đặt tên đúng).
- [ ] PR đã được người review **Approve** và CI xanh, đã merge vào `main`.
- [ ] Cập nhật trạng thái trong file Excel (cột *Trạng thái* và *Trạng thái review*).
- [ ] Nếu dùng AI hoặc tài liệu ngoài: đã ghi vào `docs/AI_USAGE_LOG.md` / `docs/REFERENCES.md`.

---

## 6. Test

- Logic game và solver **bắt buộc có unit test** (thư mục `tests/`, tên file `test_*.py`).
- Test không phụ thuộc GUI, không đọc file ngoài `levels/` và `tests/`.
- Mỗi solver phải có test trên `DummyGame` hoặc một màn nhỏ **và** kiểm tra lời giải thật sự hợp lệ
  (đi theo `path` từ `initial_state` bằng `get_successors` phải tới trạng thái đích).
- BFS và A*/UCS với chi phí đều phải ra cùng độ dài lời giải tối ưu trên cùng một màn: dùng để đối chiếu chéo.
- CI (GitHub Actions) tự chạy test mỗi khi có PR. **PR đỏ thì không merge.**

---

## 7. Đổi "hợp đồng" giữa các module

Áp dụng cho `State`, `Game`, `SearchResult`, định dạng JSON màn chơi, quy ước tọa độ và tư thế.

1. Người muốn đổi nhắn vào nhóm chat: *đổi gì, vì sao, ai bị ảnh hưởng*.
2. **Cả 6 người** phản hồi (✅ hoặc ý kiến) trong 24 giờ. Không phản hồi coi như chưa đồng ý, nhắc lại.
3. Tạo PR **riêng** chỉ chứa thay đổi này, cần **2 người duyệt** (người review + người dùng thay đổi nhiều nhất).
4. Sau khi merge, thông báo cả nhóm để mọi người `git pull` và sửa phần của mình.

---

## 8. Giao tiếp và tiến độ

- **Cập nhật hàng ngày** (nhắn trong nhóm chat, một tin ngắn): *hôm qua làm gì – hôm nay làm gì – đang vướng gì*.
- **Họp:** 1 buổi khởi động (Bước 0), sau đó 2 buổi mỗi tuần (khoảng 20–30 phút, đầu tuần và giữa tuần) để xem lịch trong file Excel.
- **Vướng việc → báo trong vòng 24 giờ.** Đừng im lặng rồi trễ hạn.
- **Sắp trễ hạn → báo trước ít nhất 1 ngày** để nhóm chia lại việc. Chia lại việc thì sửa cột *Mã người* trong Excel
  và ghi chú lý do, để lúc báo cáo tính % đóng góp cho chính xác.
- Hỏi giúp là bình thường. Nhưng **mỗi người vẫn phải tự hiểu** code mình nộp.

---

## 9. AI, nguồn tham khảo và liêm chính học thuật

Đề cho phép dùng AI nhưng giảng viên có thể **phỏng vấn ngẫu nhiên** và **đạo văn = 0 điểm môn**.

- Dùng AI (ChatGPT, Claude, Copilot...) cho việc gì đáng kể thì **ghi vào `docs/AI_USAGE_LOG.md`** (prompt, kết quả, cách kiểm chứng).
  Báo cáo bắt buộc có phụ lục này.
- Code lấy từ GitHub / StackOverflow / bài viết: **ghi nguồn vào `docs/REFERENCES.md` và để comment link ngay trên đoạn code**.
  Cấm copy nguyên repo/bài của người khác nộp như của mình. Solver phải tự cài đặt.
- Code do AI sinh ra phải được **đọc hiểu, chạy thử, có test** trước khi commit. Không commit thứ mình không giải thích được.
- Trước hạn nộp, mỗi người tự kiểm tra: *"mình có giải thích được từng file mình viết và từng PR mình review không?"*

---

## 10. Xung đột, lỗi và khẩn cấp

- **Merge conflict:** tự giải quyết ở nhánh của mình (xem `docs/GIT_GUIDE.md`, mục 6). Không hiểu thì gọi người vừa sửa file đó.
- **`main` bị hỏng** (test đỏ / không chạy): báo ngay vào nhóm chat. Người merge PR gây lỗi ưu tiên sửa hoặc `git revert` trong vòng vài giờ.
- **Không dùng** `git push --force` lên `main`, không xóa nhánh của người khác, không rewrite lịch sử đã merge.

---

## 11. Chốt code và nộp bài

- **Code freeze:** 1 ngày trước hạn nộp (xem ngày trong sheet *Tổng quan* của Excel). Sau mốc này chỉ sửa lỗi nghiêm trọng, và vẫn qua PR + review.
- Người phụ trách nộp bài tạo tag `v1.0-submission` trên commit cuối, rồi nén thư mục đúng định dạng đề (`MSSV1_MSSV2_...`),
  chạy thử `README.md` trên một máy sạch (tạo venv mới, `pip install -r requirements.txt`, `python main.py`).
- Link video YouTube và phần phân công %/đóng góp phải có trong `Report.pdf`.
