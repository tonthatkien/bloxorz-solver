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

Mặc định xuất vào `experiments/results/f4/`, PNG 300 dpi, PDF vector và SVG.
Thêm `--out-dir <folder>`, `--formats png pdf svg` hoặc `--dpi 600` nếu cần.
Nếu chỉ có kết quả solver, bỏ hai tham số `--heuristics` và `--summary`.
Không sửa mã/đổi tên cột F3, không chạy lại solver khi vẽ.

## Các hình được xuất

| Tên | Nội dung |
|---|---|
| `solvers_{unit,weighted}_efficiency` | Hai panel số nút và thời gian / UCS, theo G1–G4 |
| `solvers_{unit,weighted}_memory_cost` | Hai panel bộ nhớ và chi phí / UCS, theo G1–G4 |
| `heuristics_{unit,weighted}_efficiency` | Hai panel số nút và thời gian / A* h=0 |
| `heuristics_{unit,weighted}_memory_tightness` | Hai panel bộ nhớ / A* h=0 và độ sát |
| `heuristics_groups` | Heatmap node/time ratio theo G1–G4, cùng thang màu |
| `appendix_solvers_{unit,weighted}_resources` | Hai panel thời gian, bộ nhớ tuyệt đối từng màn |
| `appendix_solvers_{unit,weighted}_search` | Hai panel số nút, độ dài tuyệt đối từng màn |
| `appendix_solvers_weighted_cost` | Chi phí tuyệt đối từng màn ở weighted |
| `all_figures.pdf` | 9 hình chính, sau đó 5 trang phụ lục |
| `manifest.json` | SHA-256 đầu vào, số dòng, quy tắc, nhãn màn và số liệu tối ưu heuristic |

Mỗi tên hình có đuôi theo `--formats`. Bộ đầy đủ gồm 14 PNG 300 dpi,
14 PDF vector, 14 SVG và PDF tổng hợp 14 trang (43 file hình).
Không commit CSV gốc hoặc hình sinh tự động; output mặc định được Git ignore.
Sau khi vẽ thành công, công cụ xóa các tên hình bốn panel và phụ lục rộng cũ,
cùng `heuristics_quality.png/pdf/svg`, để tránh chèn nhầm bản cũ vào báo cáo.

## Bố cục cho A4

- Mỗi hình chính và phụ lục có tối đa hai panel xếp dọc; chiều rộng 7.2 inch,
  chiều cao 8.3 inch (phụ lục một panel: 5.4 inch). Khi chèn bằng
  `\includegraphics[width=\linewidth]{...pdf}`, cỡ chữ trục chính còn khoảng 10 pt.
- Trục log ghi nhãn mốc lũy thừa 10 bằng `LogLocator` và `LogFormatterMathtext`;
  `NullFormatter` ẩn nhãn minor. Tăng lề trái, tick padding, label padding và khoảng
  cách giữa các panel; không đặt cận log bằng 0.
- Nhãn cột dùng năm chữ số có nghĩa, xoay dọc để tách bốn cột hẹp mỗi nhóm.
  Tỉ số như 1.0134 vẫn khác 1; chỉ định dạng hiển thị, không làm tròn dữ liệu tính.
  Đo kích thước nhãn sau render và mở thêm khoảng trống trên trục khi cần.
- Giá trị thiếu/0 không được đổi thành epsilon. Hình solver dùng cohort dương
  chung và N/A khi không đủ mẫu; phụ lục chuyển sang tuyến tính nếu có phép đo 0.
- Hình heuristic giữ trục tuyến tính để hiển thị độ sát bằng 0 và các tỉ số gần
  nhau; không thay đổi thang log của so sánh solver hoặc phụ lục có giá trị dương.
- Ưu tiên PDF vector trong LaTeX; SVG giữ chữ tiếng Việt dưới dạng text,
  PNG 300 dpi dành cho phần mềm không đọc vector. Kiểm tra cả PDF A4 sau biên dịch.

## Quy tắc diễn giải

- Không trộn `unit` với `weighted`. Thời gian giữ đơn vị giây; memory của F3
  lưu bằng bytes/1024 (KiB). Khi xuất phụ lục, đổi sang MB thập phân bằng
  `peak_memory_kb * 1024 / 1_000_000`, đúng quy ước báo cáo; time giữ đơn vị giây.
- Hình solver chính: tính tỉ số trên từng màn với UCS cùng cost mode, rồi lấy
  trung bình nhân theo nhóm. Mỗi chỉ số dùng tập màn giải được, có giá trị dương
  chung cho mọi solver; nhãn `n` cho biết số màn dùng / tổng số màn trong nhóm.
  Giữ lời giải chưa tối ưu của DFS/BFS, không loại chúng khỏi phép so sánh cost.
  Không tính tỉ số giữa hai trung bình, không thay dữ liệu thiếu/0 bằng epsilon.
  Cần có series UCS; UCS thiếu/thất bại ở một màn thì màn đó bị loại cho mọi solver.
- Màu theo tên thuật toán, không theo vị trí series: BFS `#1F77B4`, DFS `#FF7F0E`,
  UCS `#2CA02C`, A* `#D62728`; thiếu một thuật toán không làm đổi màu thuật toán khác.
- Hình chính dùng một cột, tối đa hai panel; heatmap có một panel mỗi chế độ,
  bốn cột Nút G1–G4 rồi bốn cột TG G1–G4 (TG = thời gian), cùng thang màu.
  Giá trị trên cột solver dùng năm chữ số có nghĩa; dữ liệu tính không làm tròn lại.
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
- Kiểm tra `unit` có cost bằng length (sai số tuyệt đối 1e-6). Dòng heuristic
  thất bại không được nhận optimal/node_ratio/time_ratio; mốc zero chưa giải
  thì mọi optimal_cost/tightness/ratio/optimal phải trống, theo đúng đầu ra F3.
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
python -m unittest tests.test_plot_data tests.test_plot_style -v
python -m unittest discover -s tests -t .
```

Unit tests dữ liệu chỉ dùng standard library; không cần thêm Matplotlib vào CI.
Matplotlib chỉ được import khi thực sự xuất hình bằng CLI.
