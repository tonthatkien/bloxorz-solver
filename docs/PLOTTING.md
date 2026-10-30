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
| `solvers_unit` | Time, memory, expanded nodes, path length của từng solver/từng màn |
| `solvers_weighted` | Bốn chỉ số trên và tổng path cost; ít bước không đồng nghĩa chi phí thấp |
| `heuristics_unit`, `heuristics_weighted` | Node/time/memory ratio so với A* h=0 và tightness |
| `heuristics_groups` | Heatmap node/time ratio theo G1–G4, cùng thang màu |
| `heuristics_quality` | Số màn ít node nhất (kể cả hòa), số màn có cost tối ưu |
| `all_figures.pdf` | Toàn bộ hình trong một PDF nhiều trang |
| `manifest.json` | SHA-256 ba đầu vào, số dòng, cách tổng hợp, phiên bản vẽ và nhãn màn |

Mỗi tên hình có đuôi PNG/PDF theo `--formats`. Không commit CSV gốc hoặc file
hình sinh tự động; thư mục output mặc định được Git ignore.

## Quy tắc diễn giải

- Không trộn `unit` với `weighted`. Thời gian đổi từ giây sang ms; memory của F3
  đã tính bằng bytes/1024 nên nhãn chính xác là KiB, không chia thêm lần nữa.
- Các trục time/memory/nodes dùng log khi toàn bộ giá trị hiện hữu đều dương.
  Path length/cost dùng trục tuyến tính, bắt đầu từ 0.
- Tên như G1-02 là nhãn gọn; tên JSON đầy đủ được lưu trong manifest.
- `solved=False`, giá trị thiếu hoặc timeout không trở thành lời giải 0 bước/0 cost.
  Trên hình solver, dấu × ở chân trục biểu thị điều kiện thiếu hoặc chưa giải.
- Heuristic ghép cặp trên cùng màn và cost mode với A* `zero`, không lấy runtime UCS
  ở `results.csv` làm mẫu số của phép đo heuristic chạy riêng.
- Hiệu quả heuristic dùng tập màn giải tối ưu chung cho mọi heuristic; `n` trên hình
  cho biết số mẫu hợp lệ/tổng số màn. Phép đo/ratio bằng 0 do độ phân giải CSV
  không được dùng làm log-ratio hay ghi nhận như một chiến thắng hiệu năng.
- Node/time/memory ratios dùng trung bình nhân; tightness h(start)/C* dùng trung bình
  cộng. Ratio <1 là thấp hơn mốc. Tightness gần 1 là sát hơn, không phải runtime.
- Kiểm tra lại từng ratio, optimal flag và toàn bộ summary theo quy tắc F3;
  chấp nhận sai số làm tròn bốn chữ số thập phân. Summary cũ/sai bị từ chối trước khi vẽ.
- `node_wins` tính cho mọi trường hợp hòa; tổng các heuristic có thể vượt số màn.
  `optimal` là đối chiếu cost với zero trên bộ dữ liệu đã đo.
- CSV không chứa các lần đo riêng hoặc độ lệch chuẩn: không tự tạo error bar,
  confidence interval hoặc kết luận khác biệt thời gian có ý nghĩa thống kê.

## Kiểm tra

```bash
python -m unittest tests.test_plot_data -v
python -m unittest discover -s tests -t .
```

Unit tests dữ liệu chỉ dùng standard library; không cần thêm Matplotlib vào CI.
Matplotlib chỉ được import khi thực sự xuất hình bằng CLI.
