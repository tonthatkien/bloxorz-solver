# B2 Implementation Report

> Cập nhật hiện tại — 24/10/2026, theo D1–D4 của PR #9 và yêu cầu của Gia Hân.
> Đã merge dependency B1 mới vào B2 theo chiều B1 → B2, không rewrite/force-push/conflict.
> Các phần mô tả overlap và số liệu trước ngày này bên dưới là lịch sử.
>
> - Runtime game/tiles.py giữ nguyên vì đã đáp ứng hợp đồng sau loader validation.
> - Sáu test/fixture chồng loại ô được thay bằng sàn/switch/fragile/bridge ở các ô riêng.
>   Giữ coverage trọng lượng, toàn bộ footprint, support trước và sau switch effects.
> - Thêm regression ID63: mở/đóng đúng bit, giữ bit0, State vẫn hashable.
> - Giữ đủ bảy test dùng A1 roll thật và test snapshot độc lập dữ liệu đầu vào.
>
> Kiểm chứng: toàn suite **118 pass, 0 fail/skip**; riêng B2 **55 pass**, B1 **63 pass**.
> Ba fixtures có sẵn vẫn load được, smoke và diff/style pass. Game A2/C3 chưa tích hợp.
> PR #8 vẫn base B1; không merge B2 vào B1. Hợp đồng phụ thuộc PR #9 đang mở;
> Duy/Bảo cần xác nhận D3 trong chat như tài liệu yêu cầu, chưa xác nhận thay nhóm.

> Trạng thái sau tách ngày 23/10/2026: feature/han-B2-review dựa trên B1 đã sửa
> a7d81db. B2 code/tests được phục hồi nguyên bản từ backup 7308a83, gồm cả hai test
> bổ sung sau merge cũ. Toàn suite thực tế: 115 pass, 0 fail/skip (đã có A1).
> Các bảng số liệu 21/10 bên dưới là lịch sử; xem phần Git/PR cập nhật ở cuối.

- Task: B2 — Ô cầu, công tắc mềm/nặng. Developer: Gia Hân.
- Reviewer: Bảo Bảo (`BB1311`, xác minh từ tác giả PR E1 #1).
- Nhánh hiện tại: `feature/han-B2-review`, từ B1 `a7d81db2516c0e9ede539a6e157d9f2d57bf8d5d`.
- Nhánh B2 cũ `feature/han-B2` tại 1040144 và PR #5 giữ nguyên lịch sử.
- Status: implementation completed, pending review/dependency merge/Game integration.
  Chưa đạt Definition of Done; không ghi DONE.
- Môi trường test: Python 3.12.3, Linux/WSL, 21/10/2026.

## Mục tiêu và phạm vi

Cung cấp support/bridge/switch rules dùng chung trong `game/tiles.py`, độc lập Game/GUI/solver,
unit tests và test tích hợp dùng chuyển động thật từ A1. Không sửa `game/state.py`,
`game/game.py`, A1, GUI hoặc solver; không triển khai split switch gameplay, teleport,
cube movement, tách/ghép hay công việc C1/C2/C3.

Nguồn: README/CONTRIBUTING/CODING_STANDARDS/REVIEW_GUIDE/GIT_GUIDE, PR template,
`TO DO LIST.xlsx` xác nhận B2 phụ thuộc B1, PDF §2.5 xác định gameplay.
`docs/REVIEW_ASSIGNMENTS.md` chưa có; reviewer lấy từ Excel rồi đối chiếu GitHub.

| File | Thay đổi | Quyền/phạm vi |
|---|---|---|
| game/tiles.py | Snapshot static terrain, support, event/effect, resolve_landing | B2 |
| tests/test_tiles.py | 45 test methods về bridge/switch/landing | B2 |
| tests/test_tiles_a1.py | 7 test methods dùng A1 Block.roll; skip rõ nếu thiếu A1 | Integration trực tiếp B2 |
| docs/B2_IMPLEMENTATION_REPORT.md | Thiết kế, bằng chứng và handoff | B2 |
| docs/B2_PULL_REQUEST.md | PR body sẵn dùng khi B1 merge | B2 |
| docs/AI_USAGE_LOG.md | Bổ sung mục B2, không sửa mục B1 | Quy định nhóm |

## Thiết kế dữ liệu và API

`TileRules.from_level(level)` chạy một lần sau `parse_level`: snapshot floor/fragile thành
frozenset, bridge coordinate→ID thành mappingproxy, switch config thành tuple các
`SwitchEffect` frozen. Targets là tuple; target bitmask được tính trước một lần.
Không parsing JSON, copying Level hoặc xây lại bảng static trong mỗi successor.
Level gốc giữ public API mutable để tương thích; mutation sau snapshot không ảnh hưởng rules.

| API | Trách nhiệm |
|---|---|
| is_bridge_open(pos, bridge_mask) | Tra đúng bit theo bridge ID tại tọa độ, kể cả ID 0 và ID thưa |
| is_supported(state) | Tất cả cells có static floor/goal, cầu runtime mở và fragile weight hợp lệ |
| detect_triggered_switches(old, landed) | Activation edges của soft/heavy, thứ tự tọa độ |
| apply_switch_effects(mask, events) | Toggle/set các target bits, giữ nguyên bits ngoài targets |
| resolve_landing(old, landed) | Thực hiện cả pipeline support→events→effects→support, trả State mới hoặc None |

Static floor dùng trực tiếp quy ước JSON `#`/`G`; `.` là void. Không gọi Board.from_strings
của A1; mapping #/. của A1 hiện đã được sửa để khớp JSON. Một bridge record là một ô và bit i biểu diễn bridge ID i.
Không lấy initial_bridge_mask để ghi đè runtime. Mask âm/bool/float/string bị từ chối;
unknown orientation không được coi là supported. Không đổi State equality/hash.

## Quy tắc sự kiện và thứ tự transition

Người dùng đã xác nhận trong chat: **vừa đi vào vùng kích hoạt mới kích hoạt**, giữ tiếp xúc
không kích hoạt lại, rời rồi quay lại có sự kiện mới. Đây là quyết định đã xác nhận,
không diễn giải thành câu quy định nguyên văn của đề bài.

Soft xét mọi cell (cả ô thứ hai khi HORIZ/VERT); heavy chỉ xét full block STAND.
Lying→STAND ở cùng vị trí chuyển từ không đè nặng sang đè nặng nên có activation edge.
Cube đơn có thể đè soft nhưng không heavy. Thay cube đang điều khiển không tạo sự kiện
nếu footprint vẫn giữ tiếp xúc. Split switches được bỏ qua để C2 xử lý.

Trình tự cho A2/C3 tích hợp:

1. A1/C1 tính pose/cells sau action.
2. `resolve_landing(old, pose)` dùng bridge mask của **old** làm nguồn đúng.
3. Kiểm tra toàn bộ support và fragile trước hiệu ứng; unsupported trả None.
4. Phát hiện activation edges từ old→pose.
5. Xử lý switch theo `(row, column)` tăng dần, độc lập thứ tự JSON/dictionary.
6. Toggle dùng XOR; permanent open dùng OR, close dùng AND với complement.
7. Kiểm tra support sau hiệu ứng; cầu vừa đóng dưới khối khiến nước đi trả None.
8. A2/C3 loại None khỏi successors, tính step_cost trên state mới và giữ thứ tự U,D,L,R,S.

Hai toggle cùng target triệt tiêu; mixed toggle/permanent có ưu tiên theo tọa độ đã mô tả.
Permanent là phép gán trạng thái, không phải khóa vĩnh viễn chống mọi switch khác;
không cần thêm history vào State. Support trước và sau effects là thiết kế tích hợp rõ ràng;
PDF không đặc tả vi thứ tự này. Reviewer cần kiểm tra khi nối Game; chưa có engine khác
để đối chiếu hành vi đóng/mở cầu giữa animation frames.

## Bằng chứng test thực tế

Lệnh chuẩn: `python -m unittest discover -s tests -t .`.
Tại môi trường này executable là `python3`; thêm `-B` để không sinh bytecode.

| Test suite | Passed | Failed | Skipped | Ý nghĩa |
|---|---:|---:|---:|---|
| Baseline main | 9 | 0 | 0 | Trước B1/B2 |
| B1 | 30 | 0 | 0 | Loader/fragile/State/regression |
| B2 riêng (test_tiles + test_tiles_a1) | 45 | 0 | 7 | A1 chưa có trong branch |
| Toàn bộ branch B2 | 75 | 0 | 7 | 82 discovered; skip do thiếu A1, không tính là pass |
| B1+B2 và ba file A1 từ PR #3 trong bản sao tạm | 105 | 0 | 0 | Gồm 23 test A1 và 7 real-roll integration tests |
| main.py level fragile/switch | 2 lệnh thành công | 0 | 0 | Smoke loader, không phải GUI/gameplay |
| Game/solver end-to-end | — | — | — | BLOCKED vì A2 và solver còn TODO |
| GitHub CI | — | — | — | BLOCKED vì chưa push/tạo PR được |

12 support tests kiểm toàn footprint, void/bounds, fragile/cầu overlap, runtime vs initial,
bridge ID 0/thưa, mask sai. 11 event tests kiểm soft/heavy, second cell, sustained/reentry,
cube pressure/control swap và split metadata không kích hoạt gameplay.
8 effect tests kiểm toggle, permanent, nhiều targets, cùng target và thứ tự deterministic.
14 landing tests kiểm bất biến, pre/post support, đóng cầu đang đỡ, fragile sau roll,
mask source đúng, visited hash và reset về initial bridges.

Các test trong `test_tiles.py` truyền pose vào API landing, không khẳng định pose đó là
kết quả của một action hợp lệ. `test_tiles_a1.py` kiểm bằng bảng roll thật của A1:
standing→lying fragile, lying→standing fragile, soft ở second cell mở cầu cho bước sau,
heavy không kích hoạt khi nằm rồi kích hoạt khi đứng, đóng cầu dưới footprint,
rời/quay lại toggle và rơi ngoài grid.

### Log regression thực tế

Branch B2 hiện tại:

```text
...........................................................................sssssss
----------------------------------------------------------------------
Ran 82 tests in 0.009s

OK (skipped=7)
```

Compatibility với A1 trong bản sao tạm:

```text
.........................................................................................................
----------------------------------------------------------------------
Ran 105 tests in 0.011s

OK
```

## Hai vòng self-review, phát hiện và xử lý

| Vòng/severity | Vị trí | Phát hiện, cách tái hiện và expected/actual | Xử lý | Test/bằng chứng |
|---|---|---|---|---|
| Correctness / High risk covered | tiles.py:111 | Nếu chỉ kiểm support trước effects, switch có thể đóng cầu dưới cell thứ hai nhưng vẫn trả State | Thiết kế post-effect support; không ghi là bug cũ đã tồn tại vì B2 chưa có code baseline | switch_closing_occupied_bridge, real_roll_closing_bridge |
| Correctness / High risk covered | tiles.py:65, :81 | Anchor-only bỏ sót second cell; initial-mask thay runtime làm cầu sai; heavy không được nhận single cube | Kiểm cells đầy đủ, old.bridges là nguồn đúng, split guard | soft_second_cell, old_mask_is_authoritative, single_cube |
| Engineering / Low, fixed | tests/test_tiles.py:134 | Tên test ban đầu ngụ ý có sideways roll thật, nhưng dữ liệu là synthetic pose comparison | Đổi tên/comment đúng ý nghĩa; thêm file test A1 roll thật | 7 integration tests pass cùng A1 |
| Engineering / Medium, addressed | tiles.py:27, :102 | Target mask là static config, không cần dựng lại ở mỗi event | Chuẩn hóa target_mask trong immutable snapshot | multiple_sparse_targets, permanent_multiple_targets |

Vòng 1 kiểm gameplay, dữ liệu/schema B1, footprint, bridge masks, event edges và pre/post
support. Vòng 2 kiểm diff/scope, types/docstrings, naming, duplication, tính bất biến,
không circular import, không GUI/solver dependency và không thêm thư viện ngoài.
Kiểm tra AST, Python mới không quá 100 ký tự/dòng, `git diff --check` đều thành công.
Không phát hiện Critical/High chưa xử lý trong phạm vi B2. Chưa có independent human review;
không tự approve và không tuyên bố code hoàn hảo.

## Verified / Assumed / Pending / Blocked

- **Verified:** test results và logs ở trên; target IDs/masks; no mutation; coordinate order;
  State/Game/JSON API giữ nguyên; checkout gốc được bảo toàn; scope diff B2 so B1.
- **Confirmed by user:** entry-trigger và thứ tự nhiều switches theo tọa độ như câu hỏi đã trả lời.
- **Design policy, pending integration review:** support trước/sau effects; permanent set có thể
  được switch khác thay đổi sau đó. Không có engine A2 để kiểm tra end-to-end.
- **Pending integration:** A2 tạo TileRules một lần, gọi resolve_landing sau roll; C2/C3 tự
  xử lý split/merge/teleport rồi phối hợp tile rules. Không đổi Game interface.
- **Blocked:** A1 #3 chưa merge; B1 chưa review/merge; Git HTTPS thiếu credential và GitHub
  create_tree trả 403 Resource not accessible by integration; chưa tạo PR/CI/request-review.
- **Not tested:** GUI/animation, solver paths và BFS/UCS/A* optimality (các module còn TODO),
  restart GUI; chỉ Game.initial_state restart bridge mask đã test.

## Git, PR và handoff — cập nhật 23/10/2026

PR #5 cũ đã merge B2 vào B1; giữ nguyên PR và branch cũ để bảo toàn lịch sử.
B1 đã revert nội dung merge đó bằng ee81296 và giữ các sửa B1 mới nhất từ 7308a83.
B1 đã cập nhật main/A1; suite B1 riêng 61 pass. Nhánh feature/han-B2-review tạo từ B1
đã sửa, phục hồi đúng B2-owned files từ backup/han-B1-before-fix, không merge nhánh B2 cũ.
Điều này cần thiết vì commit B2 cũ vẫn là ancestor của B1 nhưng nội dung đã được revert.

Code game/tiles.py, tests/test_tiles.py (418 dòng), tests/test_tiles_a1.py khớp byte-for-byte
với 7308a83, giữ đủ hai regression soft/heavy trên fragile. Không thay API hoặc gameplay.
CI cho base feature/han-B1 chỉ được thêm trên B2-review. AI log B1 giữ nguyên phần B1;
B2-review bổ sung riêng lịch sử B2, không thay phiên bản cũ của file dùng chung.

PR mới: feature/han-B2-review → feature/han-B1, thay thế phần review B2 của PR #5.
Reviewer B2 Bảo Bảo (BB1311), B1 Kiên (tonthatkien) đã được Gia Hân xác nhận lại.
**Không merge PR B2 mới vào B1.** Chỉ dùng base B1 để tách diff khi review.
Sau B1 merge vào main, fetch và đánh giá ancestry/diff; chỉ retarget khi main...B2-review
chỉ còn B2. Nếu cần rewrite branch đã chia sẻ thì phải xin phép, không force-push/reset.
Không xóa backup hoặc branch cũ, không tự approve/merge hoặc resolve review threads.

Kiểm tra branch B2 mới: `python3 -B -m unittest discover -s tests -t .` **115 pass,
0 fail/skip**. Không dùng số liệu B2 làm kết quả B1. Smoke main.py, diff check và so
sánh blobs thành công. CI sẽ đọc sau push và tạo PR. Không đánh dấu DONE trước review.

### Tái hiện compatibility suite A1 mà không sửa checkout

Sau `git fetch origin`, chạy trong Bash tại repository (Python có thể là python3):

```bash
python -B - <<'PY'
import pathlib, shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as name:
    target = pathlib.Path(name)
    for folder in ('game', 'tests', 'levels', 'solvers'):
        shutil.copytree(folder, target / folder,
                        ignore=shutil.ignore_patterns('__pycache__'))
    for file in ('game/block.py', 'game/board.py', 'tests/test_core.py'):
        (target / file).write_bytes(subprocess.check_output(
            ['git', 'show', 'origin/main:' + file]))
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                    'tests', '-t', '.'], cwd=target, check=True)
PY
```

Ở snapshot 21/10 là 105 pass; branch sau tách hiện tại chạy trực tiếp 115 pass. Đây là compatibility với đúng head A1 đã audit, không phải bằng
chứng A1 đã merge hoặc bằng chứng pipeline Game cuối cùng đã hoàn thành.
