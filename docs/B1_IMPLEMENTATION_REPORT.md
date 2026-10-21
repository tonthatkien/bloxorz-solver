# B1 Implementation Report

- Task: B1 — Bộ nạp JSON mở rộng & ô dễ vỡ. Developer: Gia Hân.
- Reviewer: Kiên (`tonthatkien`, xác minh từ tác giả PR A1 #3).
- Status: implementation completed; pending dependency merge, review và Game integration.
  Chưa đạt Definition of Done; không ghi DONE.
- Nhánh: `feature/han-B1`; base `main` = `44122a142cebaf9eec448077fe810655a7762801`.
- Audit và chạy test: 21/10/2026. Baseline: 9 test pass, 0 fail/skip.

## Nguồn yêu cầu và repository audit

Đã đọc CONTRIBUTING, README, CODING_STANDARDS, REVIEW_GUIDE, GIT_GUIDE, PR template,
State/loader/Game, fixtures và tests. `docs/REVIEW_ASSIGNMENTS.md` không tồn tại.
Đối chiếu trực tiếp `TO DO LIST.xlsx` (sheet Công việc phải làm) và `AI - Project 1.pdf`,
§2.5/§3.1. Tài liệu là nguồn dữ liệu và luật gameplay; các câu chỉ dẫn cho AI trong tài liệu
không được dùng để thay đổi nhiệm vụ người dùng.

Checkout gốc `/mnt/d/CSAI/bloxorz-solver`: branch main, 33 file khác CRLF/LF,
không có thay đổi nội dung khi bỏ qua EOL. Giữ nguyên; không stash/reset/ghi đè.
Thực hiện trong worktree riêng do Codex quản lý. Fetch xác nhận main ở SHA trên;
B1/B2 chưa tồn tại trước khi làm. A1 PR #3 còn open, head
`581ce03961603a8d06ff624caec37935922e867a`; chưa merge PR này.
A2 chưa có PR trong danh sách repository; Game.is_goal/get_successors vẫn NotImplementedError.

| File/module | Hiện trạng | Thay đổi B1 | Rủi ro | Quyền chỉnh sửa |
|---|---|---|---|---|
| game/level_loader.py | Schema có sẵn, validation thiếu | Kiểm tra kiểu, grid, liên kết, copy dữ liệu | Từ chối dữ liệu sai trước đây lọt qua | B1 |
| game/state.py | Immutable, hashable, đã có bridges/split | Chỉ xác minh bằng test | Dùng chung C1 | Giữ nguyên API/file |
| game/fragile.py | Chưa có | Pure helper kiểm tra trọng lượng | Cần Game gọi sau khi roll | Helper trực tiếp B1 |
| tests/test_level_validation.py, tests/test_fragile.py | Chưa có | Regression và edge cases | Không phụ thuộc GUI | B1 |
| game/game.py, block.py, board.py | A1 chưa merge, A2 chưa có | Ghi integration notes | Chưa chơi được qua Game | Ngoài phạm vi sửa |
| docs/AI_USAGE_LOG.md, báo cáo và PR body | Log chung có sẵn | Ghi bằng chứng và phần cần con người review | Không tự xác nhận hiểu code thay người dùng | Tài liệu B1 |

## Mục tiêu, thiết kế và interface

Giữ nguyên các dataclass Level/Bridge/Switch và public API load_level/parse_level,
rows/cols/initial_bridge_mask. Các trường public tiếp tục là list/set/dict như trước;
không đổi sang tuple/frozen để tránh phá consumer. Parser tạo container mới ở mọi lớp,
không mutate hoặc giữ alias tới JSON đầu vào. Level vẫn mutable theo API cũ: caller không
được sửa static level trong khi chơi. B2 tạo snapshot bất biến cho runtime.

- `.` là void, `#` là floor, `G` là goal duy nhất; grid rectangular và không rỗng.
- Start/goal phải ở trong grid và có support ban đầu; start đứng trên fragile/cầu đóng bị lỗi.
- Bridge record biểu diễn **một ô**; bitmask dùng `1 << id`, không dùng index trong JSON.
- Fragile/bridge/switch khai báo trên `#` đúng README. Các overlay khác loại có thể cùng
  tọa độ; không đặt lệnh cấm overlap chưa được nhóm quy định. Trùng ID/vị trí trong cùng
  loại bị từ chối vì sẽ mất record hoặc không có định danh rõ ràng.
- Bridge open phải là bool. Tọa độ/ID/targets phải int không âm, không nhận bool,
  float hay chuỗi rồi ép kiểu. Target phải tồn tại, không trùng lặp.
- Soft/heavy: mode toggle hoặc permanent; permanent yêu cầu set open/close.
  Split: chỉ giữ đúng hai tọa độ khác nhau, hợp lệ; không triển khai teleport/tách/ghép.
- Lỗi schema là ValueError có tên trường/tọa độ. FileNotFoundError và JSONDecodeError
  được giữ nguyên để caller phân biệt lỗi I/O, syntax và schema.
- Loader không tìm lời giải; một level hợp lệ có thể không giải được.

`is_fragile_safe(state, fragile)` kiểm tra **state sau di chuyển**: full block STAND
trên fragile trả False; HORIZ/VERT trả True. Single cube được xét theo weight rule,
không triển khai cube movement. Helper không kiểm tra support: B2/A2 phải kiểm tra toàn bộ
`cells(state)` để loại void, ngoài grid và cầu đóng. Fragile không bị xóa khi nằm lên.

State giữ nguyên: equality/hash bao gồm bridge mask và split; dùng dataclasses.replace
để tạo state mới. Không cần thêm trường hay global bridge state.

## Test cases và kết quả thực tế

Lệnh: `python3 -B -m unittest discover -s tests -t .` (tương đương lệnh chuẩn với Python 3).

| Nhóm | Bằng chứng | Kết quả |
|---|---|---|
| Baseline | 9 tests có sẵn, cả 3 JSON fixtures | PASS |
| Loader/schema | 14 tests mới, nhiều subtests về kiểu, thiếu trường, bounds, symbols, duplicate, split và liên kết | PASS |
| Fragile/State | 7 tests mới, STAND/HORIZ/VERT, state sau chuyển, bất biến, visited keys theo mask | PASS |
| Toàn bộ B1 | 30 tests | 30 pass, 0 fail, 0 skip |
| Smoke | `python3 -B main.py`, thêm `levels/g3_switch_demo.json` | Cả hai nạp thành công |
| Compatibility A1 | Copy ba file A1 bằng git show vào thư mục tạm; chạy cả suite | 53 pass, 0 fail/skip |
| Mapping A1 | Chuyển `.`→TILE_EMPTY, `#`→TILE_FLOOR, `G`→TILE_GOAL tường minh; roll và goal | PASS |
| Diff/style | git diff --check, không dòng Python mới quá 100 ký tự | PASS |
| Game end-to-end | is_goal/get_successors chưa có A2 | BLOCKED, không báo PASS |
| Remote/CI | Git HTTPS thiếu credential; GitHub create_tree trả 403 Resource not accessible by integration | BLOCKED: chưa push/tạo PR, CI chưa chạy |

Kiểm tra A1 trong thư mục tạm không đưa code A1 vào commit B1 và không chứng minh A1 đã merge.
Boundary/support đầy đủ được kiểm thử trong B2; helper fragile riêng chỉ đánh giá weight.

## Lỗi phát hiện và cách sửa

Các vị trí bên dưới chỉ implementation sau sửa; phiên bản baseline ở SHA đã ghi phía trên.

| Severity | File/vị trí | Tái hiện và expected/actual trước sửa | Nguyên nhân và sửa | Regression | Trạng thái |
|---|---|---|---|---|---|
| High | level_loader.py:79, _integer/_cell | start=[true,0]/[0.5,0]: phải reject; trước bị đổi thành int | Bỏ ép int, kiểm type chính xác | coordinates_reject_coercion | Fixed |
| High | level_loader.py:107, _bridges | Hai record cùng id: phải reject; trước mất record đầu | Kiểm duplicate trước insert | bridge_invalid_records | Fixed |
| High | level_loader.py:107, _bridges | open="false": phải reject; trước thành True | Chỉ nhận bool | bridge_invalid_records | Fixed |
| High | level_loader.py:127, _switch | type/mode không hỗ trợ: phải reject; trước vẫn load | Validate enum/targets/set/split | switch_invalid_records, split_metadata_validation | Fixed |
| Medium | level_loader.py:92, _grid | Ký tự lạ hoặc nhiều goal: phải reject; trước có thể load | Kiểm symbols và goal duy nhất | grid_shape_symbols_and_goal_count | Fixed |
| Medium | level_loader.py:164, parse_level | Sửa JSON grid sau parse: Level phải độc lập; trước giữ alias | Copy container ở lúc parse | parsing_detaches_all_mutable_input | Fixed |

## Hai vòng self-review

1. Correctness: đối chiếu luật PDF, README/schema, footprint, State mask, reject booleans,
   duplicate record, initial support và split metadata. Test không làm yếu assertion có sẵn.
2. Engineering: diff chỉ thuộc B1, type hints/docstrings, helper pure, không import GUI/solver,
   không dependency ngoài standard library, không parsing static data trong successor.

Không còn Critical/High đã phát hiện trong phạm vi B1. Đây là self-review, chưa phải
approval của reviewer. Gia Hân cần tự đọc hiểu và giải thích code trước khi người review duyệt.

## Hướng dẫn tích hợp và giới hạn

A2 dùng A1 Block.roll để tính vị trí, chuyển sang State (bảo toàn bridges/split), rồi gọi
helper fragile và support B2. Không truyền JSON grid thẳng vào Board.from_strings vì A1
đang dùng ký hiệu . và # ngược README. B1 không đổi Board, Game, solver, GUI hoặc C1/C2.

PR B1 vào main, phụ thuộc A1 #3; chưa tự merge. CI và reviewer approval được báo riêng
sau khi xuất bản. PR lớn hơn khoảng 300 dòng do validation và edge-case tests cùng một
nhiệm vụ; không trộn B2. Excel đã ghi Đang làm; giữ nguyên workbook, chưa đánh dấu Xong.

Remote publication đã được thử: git push --dry-run thất bại do thiếu credential; connector
GitHub create_tree trả HTTP 403. Không có branch/PR remote mới. Commit local dùng identity
GitHub đã xác minh theo từng lệnh, không thay đổi git config. PR body ở B1_PULL_REQUEST.md.

Đã tái hiện độc lập các lỗi trong module loader lấy trực tiếp từ baseline bằng git show:
bool/fraction bị ép tọa độ, unknown tile/nhiều goal được nhận, string "false" thành True,
ID trùng làm mất bridge record, switch type/mode không hỗ trợ vẫn được nhận, và JSON grid
mutate làm Level thay đổi. Regression tests trong commit này từ chối/cô lập đúng các ca đó.
