# F4 — Biểu đồ từ dữ liệu F3

Gia Hân triển khai; Bảo Bảo review. Chạy từ thư mục gốc repository:

```bash
python -m pip install -r requirements.txt
python -m experiments.plot --results experiments/results/results.csv \
  --heuristics experiments/results/heuristics.csv \
  --summary experiments/results/heuristics_summary.csv
```

PowerShell: viết lệnh thành một dòng hoặc dùng dấu backtick để xuống dòng.
Các đường dẫn có khoảng trắng cần đặt trong dấu nháy. Có thể truyền trực tiếp
ba CSV nhận từ F3 ở vị trí khác; không cần copy vào repository.

Mặc định xuất vào `experiments/results/f4/`, PNG 300 dpi và PDF vector.
Thêm `--out-dir <folder>`, `--formats png pdf svg` hoặc `--dpi 600` nếu cần.
Nếu chỉ có kết quả solver, bỏ hai tham số `--heuristics` và `--summary`.
Không sửa mã/đổi tên cột F3, không chạy lại solver khi vẽ.

## Các hình được xuất

| Tên | Nội dung |
|---|---|
| `solvers_unit`, `solvers_weighted` | Cột nhóm G1–G4: trung bình nhân node/time/memory/cost ratio so với UCS; trục log, mốc 1 |
| `appendix_solvers_unit`, `appendix_solvers_weighted` | Phụ lục: time/memory/nodes/length/cost tuyệt đối từng màn |
| `heuristics_unit`, `heuristics_weighted` | Node/time/memory ratio so với A* h=0 và tightness |
| `heuristics_groups` | Heatmap node/time ratio theo G1–G4, cùng thang màu |
| `all_figures.pdf` | 5 hình chính, sau đó 2 phụ lục khi đủ cả hai chế độ và heuristic |
| `manifest.json` | SHA-256 đầu vào, số dòng, quy tắc, nhãn màn và số liệu tối ưu heuristic |

Mỗi tên hình có đuôi PNG/PDF theo `--formats`. Không commit CSV gốc hoặc file
hình sinh tự động; thư mục output mặc định được Git ignore. Bộ đầy đủ gồm 7 PNG,
7 PDF riêng và PDF tổng hợp 7 trang. Sau khi vẽ thành công, công cụ xóa
`heuristics_quality.png/pdf/svg` cũ trong output để tránh dùng nhầm hình đã bỏ.

## Quy tắc diễn giải

- Không trộn `unit` với `weighted`. Thời gian đổi từ giây sang ms; memory của F3
  đã tính bằng bytes/1024 nên nhãn chính xác là KiB, không chia thêm lần nữa.
- Hình solver chính: tính tỉ số trên từng màn với UCS cùng cost mode, rồi lấy
  trung bình nhân theo nhóm. Mỗi chỉ số dùng tập màn giải được, có giá trị dương
  chung cho mọi solver; nhãn `n` cho biết số màn dùng / tổng số màn trong nhóm.
  Giữ lời giải chưa tối ưu của DFS/BFS, không loại chúng khỏi phép so sánh cost.
  Không tính tỉ số giữa hai trung bình, không thay dữ liệu thiếu/0 bằng epsilon.
  Cần có series UCS; UCS thiếu/thất bại ở một màn thì màn đó bị loại cho mọi solver.
- Node/time/memory/cost ratio dùng trục log, mốc ngang 1. Ở unit, cost ratio cũng
  là length ratio. Ở weighted, cost ratio dùng cost của UCS làm mốc tối ưu tham
  chiếu; BFS không được giả định bằng 1 vì ít bước nhất không bảo đảm cost thấp nhất.
- Phụ lục giữ đơn vị tuyệt đối: time/memory/nodes dùng log khi mọi giá trị dương;
  length/cost dùng trục tuyến tính. Đường nối chỉ để tra cứu, không biểu thị xu
  hướng giữa các màn độc lập; dùng hình cột nhóm để so sánh chính.
- Tên như G1-02 là nhãn gọn; tên JSON đầy đủ được lưu trong manifest.
- `solved=False`, giá trị thiếu hoặc timeout không trở thành lời giải 0 bước/0 cost.
  Trên phụ lục, dấu × ở chân trục biểu thị điều kiện thiếu hoặc chưa giải.
  Trên cột nhóm, `N/A` là không đủ mẫu ghép cặp hợp lệ, không phải tỉ số bằng 0.
- Heuristic ghép cặp trên cùng màn và cost mode với A* `zero`, không lấy runtime UCS
  ở `results.csv` làm mẫu số của phép đo heuristic chạy riêng.
- Hiệu quả heuristic dùng tập màn giải tối ưu chung cho mọi heuristic; `n` trên hình
  cho biết số mẫu hợp lệ/tổng số màn. Phép đo/ratio bằng 0 do độ phân giải CSV
  không được dùng làm log-ratio hay ghi nhận như một chiến thắng hiệu năng.
- Node/time/memory ratios dùng trung bình nhân; tightness h(start)/C* dùng trung bình
  cộng. Ratio <1 là thấp hơn mốc. Tightness gần 1 là sát hơn, không phải runtime.
- Kiểm tra lại từng ratio, optimal flag và toàn bộ summary theo quy tắc F3;
  chấp nhận sai số làm tròn bốn chữ số thập phân. Summary cũ/sai bị từ chối trước khi vẽ.
- Bỏ hình `heuristics_quality` để tránh lặp node ratio và thanh tối ưu bằng nhau.
  `manifest.json/heuristic_optimality` ghi riêng optimal/non_optimal/unconfirmed/total
  cho từng heuristic, từng cost mode; số liệu là quan sát trên tập đã đo,
  không phải chứng minh admissibility trên mọi trạng thái. Summary F3 vẫn được
  kiểm tra đầy đủ, kể cả `node_wins` (hòa vẫn tính), không thay đổi schema F3.
- CSV không chứa các lần đo riêng hoặc độ lệch chuẩn: không tự tạo error bar,
  confidence interval hoặc kết luận khác biệt thời gian có ý nghĩa thống kê.

## Kiểm tra

```bash
python -m unittest tests.test_plot_data -v
python -m unittest discover -s tests -t .
```

Unit tests dữ liệu chỉ dùng standard library; không cần thêm Matplotlib vào CI.
Matplotlib chỉ được import khi thực sự xuất hình bằng CLI.
