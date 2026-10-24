# Hàm chi phí & Heuristic


## 1. Hàm chi phí bước không đồng nhất (Non-Uniform Step Cost)

### 1.1. Lý do

Nếu chi phí mọi bước = 1, UCS suy biến thành BFS (chi phí = độ sâu), không còn thể hiện sự khác biệt về mức độ rủi ro và chi phí chiến thuật của từng hành động. Yêu cầu đề bài quy định phải thiết kế hàm chi phí không đồng nhất có ý nghĩa vật lý/chiến thuật rõ ràng.

### 1.2. Bảng phân bổ chi phí

| Hành động / Tình huống | Hằng số | Giá trị | Lý do thiết kế |
|:---|:---|:---:|:---|
| Lăn bình thường trên ô sàn | `COST_NORMAL` | 1.0 | Chi phí cơ sở đơn vị. |
| Lăn khiến **khối 1×1×2** đè lên ô dễ vỡ (`split(s')=None`) | `COST_FRAGILE` | 1.5 | Ô dễ vỡ giới hạn nghiêm trọng các nước đi kế tiếp (không thể đứng lên), đại diện cho nguy cơ chiến thuật cao hơn. Cube đơn 1×1×1 (split≠None) không áp dụng. |
| Lăn kích hoạt công tắc (soft/heavy/split) | `COST_SWITCH` | 1.2 | Kích hoạt cơ chế môi trường (mở/đóng cầu, dịch khối) — thay đổi cấu trúc bản đồ nên chi phí cao hơn lăn thường. |
| Hoán đổi quyền điều khiển cube (`"S"`) | `COST_SWAP` | 0.5 | Không di chuyển vị trí vật lý trên bàn cờ → chi phí thấp nhất. |

### 1.3. Đảm bảo hội tụ

Mọi hằng số chi phí đều dương và $c_{min} = 1.0 > 0$. Điều này đảm bảo:
- UCS không bị vòng lặp vô hạn với chi phí 0.
- A* với heuristic admissible sẽ luôn hội tụ tới lời giải tối ưu.

### 1.4. Định nghĩa

Hàm chi phí áp dụng theo thứ tự ưu tiên:

$$c(s, a, s') = \begin{cases}
0.5 & \text{nếu } a = \texttt{"S"} \text{ (hoán đổi cube)} \\[6pt]
1.2 & \text{nếu công tắc được kích hoạt:} \\
    & \quad bridges(s) \ne bridges(s') \\
    & \quad \text{hoặc } split(s) = \varnothing \wedge split(s') \ne \varnothing \\[6pt]
1.5 & \text{nếu } split(s') = \varnothing \;\wedge\; \exists \text{ ô thuộc khối mới} \in \text{fragile} \\
    & \quad \text{(chỉ áp dụng khối 1×1×2; cube đơn không bị)} \\[6pt]
1.0 & \text{trường hợp còn lại (lăn thông thường)}
\end{cases}$$


## 2. Các hàm Heuristic cho A*

### Ký hiệu chung

| Ký hiệu | Ý nghĩa |
|:---|:---|
| $h(s)$ | Giá trị heuristic tại trạng thái $s$ |
| $h^*(s)$ | Chi phí thực tế tối ưu từ $s$ đến đích gần nhất |
| $(r_c, c_c)$ | Tâm hình học (centroid) của khối gỗ |
| $(r_g, c_g)$ | Tọa độ ô đích (goal) |
| $D(s) = \lvert r_c - r_g \rvert + \lvert c_c - c_g \rvert$ | Khoảng cách Manhattan từ centroid đến goal |
| $c_{min} = 1.0$ | Chi phí bước tối thiểu cho một bước dịch chuyển vị trí |

---

### 2.1. $h_0$ — Baseline

$$h_0(s) = 0 \quad \forall s$$

Mục đích: Đối chiếu — khi dùng $h_0$, A* tương đương hoàn toàn với UCS.

Admissible: Rõ ràng $0 \le h^*(s)$ vì $c > 0$ với mọi bước.  
Consistent: $0 \le c(s,a,s') + 0$ với mọi $c > 0$.

---

### 2.2. $h_{manhattan}$ — Khoảng cách Manhattan tỷ lệ hoá

$$h_{manhattan}(s) = \left\lceil \frac{D(s)}{2} \right\rceil \times c_{min}$$

Chia 2 là vì:  
Khối gỗ $1\times 1\times 2$ khi lăn có thể dịch chuyển tối đa 2 đơn vị Manhattan trong một bước (ví dụ: STAND tại $(r,c)$ lăn phải → HORIZ chiếm $(r,c)$ và $(r,c+1)$, centroid dịch 0.5 ô → thực tế khối dịch chuyển). Do đó số bước tối thiểu $\ge \lceil D/2 \rceil$.

#### Chứng minh Admissible:

Bổ đề: Mỗi bước lăn làm $D(s)$ giảm tối đa 2.

Chứng minh: Centroid $(r_c, c_c)$ dịch chuyển tối đa 1 ô theo hàng và 1 ô theo cột trong một bước → $\Delta D \le |1| + |1| = 2$.

Định lý: $h_{manhattan}(s) \le h^*(s)$.

Chứng minh: Gọi $k$ là số bước trong đường đi tối ưu từ $s$ đến đích. Từ bổ đề:
$$D(s) \le 2k \implies k \ge \left\lceil \frac{D(s)}{2} \right\rceil$$

Vì mọi chi phí bước $c_i \ge c_{min} = 1.0$:
$$h^*(s) = \sum_{i=1}^k c_i \ge k \cdot c_{min} \ge \left\lceil \frac{D(s)}{2} \right\rceil \times c_{min} = h_{manhattan}(s) \quad \square$$

#### Chứng minh Consistent:

Với bất kỳ bước từ $s \to s'$ với chi phí $c \ge c_{min}$:
$$D(s) \le D(s') + 2$$
$$\left\lceil \frac{D(s)}{2} \right\rceil \le \left\lceil \frac{D(s')+2}{2} \right\rceil = \left\lceil \frac{D(s')}{2} \right\rceil + 1$$
$$h_{manhattan}(s) \le h_{manhattan}(s') + c_{min} \le h_{manhattan}(s') + c $$

---

### 2.3. $h_{manhattan\_orient}$ — Manhattan tăng cường bởi phạt tư thế

Khối phải ở tư thế STAND mới thắng được tại ô đích. Nếu khối đang nằm (HORIZ/VERT) và đã kề ngay ô đích ($D(s) \le 2$), khối cần ít nhất 1 bước lăn thêm để dựng đứng lên.

$$h_{manhattan\_orient}(s) = h_{manhattan}(s) + \text{penalty}(s)$$

$$\text{penalty}(s) = \begin{cases}
c_{min} & \text{nếu } orient(s) \ne STAND \text{ và } D(s) \le 2 \\
0 & \text{ngược lại}
\end{cases}$$

#### Chứng minh Admissible:

- Trường hợp 1 ($orient = STAND$ hoặc $D > 2$): penalty = 0, thu gọn về $h_{manhattan}$.  
- Trường hợp 2 ($orient \ne STAND$ và $D \le 2$):  
  Khối cần ít nhất 1 bước đứng dậy + các bước di chuyển. Số bước tối thiểu $\ge \lceil D/2 \rceil + 1$.  
  $$h^*(s) \ge \left(\left\lceil \frac{D}{2} \right\rceil + 1\right) \times c_{min} = h_{manhattan}(s) + c_{min} = h_{manhattan\_orient}(s) $$

Consistent: penalty tăng tối đa $c_{min}$, không phá vỡ bất đẳng thức tam giác đã chứng minh ở mục 2.2

---

### 2.4. $h_{relaxed\_maze}$ — BFS hạ biên trên lưới nới lỏng

Tạo bài toán nới lỏng: coi khối như điểm đơn $1\times 1$, bỏ qua tư thế và trạng thái cầu đóng. Chạy BFS ngược từ ô goal trên toàn bộ ô sàn hợp lệ để tính bảng khoảng cách $dist_{BFS}(r,c)$.

$$h_{relaxed}(s) = \left\lceil \frac{dist_{BFS}(r_{ref}, c_{ref})}{2} \right\rceil \times c_{min}$$

Trong đó $(r_{ref}, c_{ref})$ là ô tham chiếu của trạng thái $s$ (ô STAND, ô gần goal hơn trong HORIZ/VERT, hoặc cube đang điều khiển khi split).

#### Chứng minh Admissible:

Bài toán nới lỏng loại bỏ ràng buộc cầu đóng và tư thế → không gian di chuyển rộng hơn không gian gốc → $dist_{BFS} \le 2 \times (\text{số bước tối thiểu thực tế})$.

$$h^*(s) \ge \left\lceil \frac{dist_{BFS}}{2} \right\rceil \times c_{min} = h_{relaxed}(s) $$

#### Chứng minh Consistent:

$dist_{BFS}$ thỏa bất đẳng thức tam giác trên lưới:
$$dist_{BFS}(s) \le 1 + dist_{BFS}(s')$$
$$\left\lceil \frac{dist_{BFS}(s)}{2} \right\rceil \le \left\lceil \frac{dist_{BFS}(s')+1}{2} \right\rceil \le \left\lceil \frac{dist_{BFS}(s')}{2} \right\rceil + 1$$
$$h_{relaxed}(s) \le h_{relaxed}(s') + c_{min} \le h_{relaxed}(s') + c(s,a,s') $$

---

## 3. So sánh các heuristic

| Heuristic | Admissible | Consistent | Chất lượng cận dưới | Chi phí tính toán |
|:---|:---:|:---:|:---|:---|
| $h_0$ (Baseline) | Có | Có | Thấp nhất — h=0 (không cung cấp thông tin) | O(1) |
| $h_{manhattan}$ | Có | Có | Trung bình — Manhattan không phản ánh vật cản | O(1) |
| $h_{manhattan\_orient}$ | Có | Có | Tốt hơn — cộng phạt tư thế khi gần goal | O(1) |
| $h_{relaxed\_maze}$ | Có | Có | Chặt nhất — BFS trên lưới nới lỏng | O(R×C) preprocessing , O(1) tra cứu |

Heuristic chặt hơn tức $h_2(s) \ge h_1(s)$ $\forall s$ → A* với $h_2$ mở rộng ít nút hơn hoặc bằng A* với $h_1$.  
Thứ tự domination: $h_{relaxed\_maze} \ge h_{manhattan\_orient} \ge h_{manhattan} \ge h_0$.


