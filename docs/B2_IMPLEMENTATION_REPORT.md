# B2 Implementation Report

- Task: B2 — Ô cầu, công tắc mềm/nặng. Developer: Gia Hân.
- Reviewer: Bảo Bảo (`BB1311`, xác minh từ tác giả PR E1 #1).
- Nhánh: `feature/han-B2`, từ HEAD B1 `faa1ad6b5e2d744234e99863d431323f13caa9f7`.
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
của A1 vì ký hiệu đang ngược. Một bridge record là một ô và bit i biểu diễn bridge ID i.
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

## Git, PR và handoff

Cập nhật audit: cả B1 và B2 đã được người dùng push. B1 PR #4 vào main đã được tạo,
request reviewer `tonthatkien`, CI Tests thành công. Người dùng đã xác nhận tạo stacked PR
B2 với base `feature/han-B1`; đây là ngoại lệ được cho phép cho quy trình PR vào main.
Diff PR B2 chỉ chứa B2. Reviewer B2: `BB1311`.

Bổ sung `feature/han-B1` vào pull_request.branches trong `.github/workflows/tests.yml`
trên riêng nhánh B2 để CI chạy cho stacked PR; push.branches vẫn chỉ có main.
PR body trong B2_PULL_REQUEST.md phản ánh đúng dependency **B1 #4**, test evidence và
checklist chưa có xác nhận con người. Không tự approve hoặc merge.

Sau khi B1 merge, phải fetch và kiểm tra lịch sử trước khi chuyển base B2 sang main.
Nếu B1 squash merge, không mặc nhiên đổi base hoặc rebase shared branch; cần bảo đảm
diff so main chỉ chứa B2. Nếu cần rewrite lịch sử hay có conflict, hỏi người dùng trước.
Không force-push/reset/ghi đè thay đổi chưa commit. PR B2 giữ chờ cho tới khi dependency
và integration được xử lý. B1/B2 hiện đã publish, nên ghi chú 403/credential ở phần audit
phía trên chỉ mô tả thời điểm viết report ban đầu, không còn là blocker push hiện tại.

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
            ['git', 'show', '581ce03961603a8d06ff624caec37935922e867a:' + file]))
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                    'tests', '-t', '.'], cwd=target, check=True)
PY
```

Kết quả hiện tại 105 pass. Đây là compatibility với đúng head A1 đã audit, không phải bằng
chứng A1 đã merge hoặc bằng chứng pipeline Game cuối cùng đã hoàn thành.
