# Hướng dẫn Git từng bước (cho cả nhóm)

Dành cho người chưa quen Git/GitHub. Làm đúng theo thứ tự là không sai.

## 1. Cài đặt một lần
```bash
git --version                          # chưa có thì cài Git: https://git-scm.com
git config --global user.name  "Tên của bạn"
git config --global user.email "email-dung-cho-github@example.com"
```
Windows: nên dùng Git Bash hoặc terminal của VS Code. Nên cài thêm VS Code + tiện ích Python.

## 2. Lấy code về máy (một lần)
```bash
git clone <link-repo>
cd <thư-mục-repo>
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -t .      # phải thấy OK
```

## 3. Làm một việc (lặp lại cho mỗi ID)
```bash
git checkout main
git pull                                # luôn lấy bản mới nhất trước khi bắt đầu
git checkout -b feature/an-A3           # tên nhánh: feature/<tên>-<ID>

# ... sửa code, viết test ...

python -m unittest discover -s tests -t .      # chạy test cho tới khi xanh
git status                              # xem đã sửa những file nào
git add game/state.py tests/test_state.py       # thêm TỪNG file (tránh "git add ." khi chưa kiểm tra)
git commit -m "[A3] Add orientation transition table"
git push -u origin feature/an-A3        # lần đầu push nhánh mới
```
Làm tiếp trên cùng nhánh thì chỉ cần `git add`, `git commit`, `git push`.

## 4. Mở Pull Request trên GitHub
1. Vào repo trên GitHub → thường có nút vàng **Compare & pull request** (hoặc tab *Pull requests* → *New pull request*).
2. Base: `main`, compare: nhánh của bạn.
3. Tiêu đề: `[A3] Bảng chuyển tư thế`. Điền đủ mẫu PR (làm gì, cách kiểm tra, checklist).
4. Ở khung bên phải chọn **Reviewers** = người review của việc đó (xem file Excel / `docs/REVIEW_ASSIGNMENTS.md`).
5. Nhắn người review trong nhóm chat.

## 5. Khi bị yêu cầu sửa (Request changes)
```bash
git checkout feature/an-A3
# sửa theo nhận xét
git add <file> && git commit -m "[A3] Fix hợp lệ khi ra ngoài bản đồ"
git push                                # PR tự cập nhật, không cần mở PR mới
```
Trả lời từng nhận xét trên GitHub (bấm *Resolve conversation* khi đã sửa xong), rồi báo lại người review.

## 6. Cập nhật nhánh theo `main` và xử lý conflict
Khi `main` có thay đổi mới (người khác vừa merge), hoặc GitHub báo PR có conflict:
```bash
git fetch origin
git checkout feature/an-A3
git merge origin/main
```
Nếu có conflict, Git báo `CONFLICT (content): Merge conflict in <file>`. Mở file đó, tìm các đoạn:
```
<<<<<<< HEAD
code của bạn
=======
code của người khác
>>>>>>> origin/main
```
Giữ lại phần đúng (thường là **cả hai**, ghép cho hợp lý), xóa 3 dòng đánh dấu, rồi:
```bash
python -m unittest discover -s tests -t .      # chạy lại test
git add <file-đã-sửa>
git commit                               # để nguyên message có sẵn
git push
```
Không chắc nên giữ phần nào thì **hỏi người vừa sửa file đó**, đừng đoán.

## 7. Sau khi PR được merge
```bash
git checkout main
git pull
git branch -d feature/an-A3             # xóa nhánh cục bộ
```

## 8. Các tình huống hay gặp
| Tình huống | Cách xử lý |
|---|---|
| Lỡ sửa code khi đang ở `main` (chưa commit) | `git checkout -b feature/<tên>-<ID>` rồi commit như bình thường: thay đổi theo sang nhánh mới. |
| Muốn bỏ hết thay đổi chưa commit của một file | `git checkout -- <file>` (mất thay đổi, cân nhắc kỹ). |
| Cần chuyển nhánh nhưng đang sửa dở | `git stash` (cất tạm) → chuyển nhánh → `git stash pop` (lấy lại). |
| Lỡ commit sai message (chưa push) | `git commit --amend -m "[A3] Message đúng"`. |
| Lỡ commit file không nên commit (ví dụ `.venv`) | Xóa khỏi Git: `git rm -r --cached .venv`, kiểm tra `.gitignore`, commit lại. |
| Lỡ merge code hỏng vào `main` | Báo nhóm. Dùng `git revert <mã-commit>` để hoàn tác (không dùng `--force`). |
| `git pull` báo lỗi về "divergent branches" | `git pull --no-rebase` (merge) hoặc nhờ người biết Git. |
| Xem lịch sử gọn | `git log --oneline --graph --decorate -20` |

## 9. Điều tuyệt đối không làm
- `git push --force` lên `main` hoặc nhánh của người khác.
- Commit thẳng vào `main`.
- `git add .` rồi commit mà không xem `git status` (dễ kéo theo file rác / file cá nhân).
- Commit mật khẩu, token, file cá nhân.

## 10. Dành cho trưởng nhóm: bật bảo vệ nhánh `main` (làm một lần)
GitHub → repo → **Settings → Branches → Add branch ruleset / rule** cho `main`:
- Require a pull request before merging (yêu cầu **1 approval**).
- Require status checks to pass before merging (chọn workflow **Tests**).
- Dismiss stale approvals when new commits are pushed (tùy chọn).
- Block force pushes.

Mời 5 người còn lại: **Settings → Collaborators → Add people**. Nếu repo private, mỗi người cần chấp nhận lời mời qua email.
Repo GitHub nên có gốc là thư mục `Source` (chứa `main.py`, `README.md`...), để file `.github/workflows/tests.yml` chạy đúng.
