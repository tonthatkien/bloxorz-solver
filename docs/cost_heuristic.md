# Hàm chi phí và Heuristic

## I. Hàm chi phí bước không đồng nhất

### 1. Ý nghĩa các mức chi phí

Mỗi hành động có chi phí dương. Các mức dưới đây là quy ước chiến thuật của nhóm để UCS có thể
phân biệt các loại bước đi:

| Hành động / tình huống | Hằng số | Chi phí | Ý nghĩa |
|:---|:---|---:|:---|
| Lăn bình thường | COST_NORMAL | 1.0 | Mức cơ sở cho một lần lăn. |
| Lăn khối 1×1×2 lên ô dễ vỡ | COST_FRAGILE | 1.5 | Đại diện cho rủi ro và hạn chế nước đi tiếp theo. |
| Làm thay đổi trạng thái cầu hoặc kích hoạt split | COST_SWITCH | 1.2 | Đại diện cho việc thay đổi cơ chế bàn chơi. |
| Đổi cube đang điều khiển bằng S | COST_SWAP | 0.5 | Đổi quyền điều khiển mà không dịch chuyển cube. |

Chi phí mọi hành động đều lớn hơn 0 (COST_SWAP là mức thấp nhất), nên trên không gian trạng thái
hữu hạn UCS vẫn kết thúc. Riêng các chứng minh heuristic hình học dưới đây dùng
COST\_MIN = COST_NORMAL = 1.0 làm cận dưới cho một lần lăn. Đây không phải là cận dưới
cho mọi hành động, vì hành động S chỉ tốn 0.5.

### 2. Định nghĩa theo trạng thái

Hàm chi phí áp dụng theo thứ tự ưu tiên:

$$
c(s,a,s') =
\begin{cases}
0.5 & a = \texttt{"S"} \\
1.2 & bridges(s) \ne bridges(s') \\
1.2 & split(s) = \varnothing \text{ và } split(s') \ne \varnothing \\
1.5 & split(s') = \varnothing \text{ và khối mới chiếm ô fragile} \\
1.0 & \text{các trường hợp lăn còn lại}
\end{cases}
$$

Ô fragile chỉ làm tăng chi phí khi khối 1×1×2 chiếm ô đó. Cube đơn trong trạng thái split không
làm tăng chi phí fragile. Nếu một bước vừa đổi cầu vừa chạm ô fragile, quy tắc switch được xét
trước và chi phí là 1.2.

### 3. Gắn hàm chi phí vào Game

Game gọi callback với ba tham số (old_state, action, new_state), còn step_cost cần biết màn
chơi. make_cost_fn(level) tạo callback đã gắn với Level:

    game = Game(level, cost_fn=make_cost_fn(level))

Vì vậy callback truyền cho Game có đúng chữ ký và không gây TypeError khi tính chi phí successor.

---

## II. Phạm vi áp dụng heuristic

### 1. Màn có cơ chế split

Ba heuristic hình học (h_manhattan, h_manhattan_orient, h_relaxed_maze) trả về 0.0 nếu
màn có split switch hoặc trạng thái hiện tại đã split. Split switch có thể dịch chuyển cube tới
các tọa độ định sẵn, nên khoảng cách hình học trước và sau khi kích hoạt không tuân theo giới hạn
dịch chuyển của một lần lăn. Khi split, S có thể đổi cube active với chi phí 0.5 trong khi
heuristic chỉ đo cube active; giá trị heuristic vì thế có thể giảm mạnh chỉ sau một lần đổi điều
khiển.

Đặt h=0 trên các trạng thái này bảo đảm admissible và consistent. A* khi đó tương đương UCS trên
màn có split switch. Đây là lựa chọn để giữ tính tối ưu.

### 2. Màn không có split switch

Trên các màn này, trạng thái split không thể được tạo bởi luật chơi và hành động S không xuất
hiện. Do đó, mọi chuyển trạng thái mà các heuristic hình học xét đều là lần lăn, có chi phí ít nhất
COST\_MIN = 1.0. Các chứng minh đều áp dụng cho màn chơi không có split switch.

Ký hiệu:

| Ký hiệu | Ý nghĩa |
|:---|:---|
| h(s) | Chi phí còn lại được heuristic ước lượng tại trạng thái s. |
| h*(s) | Chi phí tối ưu thật từ s tới goal. |
| (r_c, c_c) | Tâm hình học của khối; phụ thuộc vào STAND, HORIZ, VERT. |
| (r_g, c_g) | Tọa độ goal. |
| D(s) = abs(r_c - r_g) + abs(c_c - c_g) | Khoảng cách Manhattan từ tâm khối tới goal. |
| c_roll_min | Cận dưới chi phí một lần lăn; bằng COST\_MIN = 1.0. |

Với STAND, tâm là (r, c); với HORIZ, tâm là (r, c + 0.5); với VERT, tâm là (r + 0.5, c).
Một lần lăn đi theo đúng một trục và làm tâm dịch tối đa 1.5 ô theo trục đó.

---

### 2.1. Các heuristic

### a) h_0 — baseline

$$h_0(s)=0 \quad \forall s$$

Admissible: mọi chi phí còn lại không âm, nên $0 \le h^*(s)$.
Consistent: với mọi chuyển trạng thái, $0 \le c(s,a,s') + 0$.

Khi dùng h_0, A* tương đương UCS.

### b) h_manhattan — Manhattan tỷ lệ hóa

$$
h_{manhattan}(s) =
\begin{cases}
0 & \text{nếu có split} \\
\left\lceil D(s)/2 \right\rceil \cdot \text{COST\_MIN} & \text{các trường hợp còn lại}
\end{cases}
$$

#### Admissibility

Gọi s' là trạng thái sau một lần lăn. Tâm khối dịch tối đa 1.5 ô theo một trục, do đó khoảng
cách Manhattan không thể giảm quá 1.5; dùng cận lỏng hơn là 2:

$$D(s) \le D(s')+2.$$

Nếu một lời giải cần k lần lăn để tới goal thì D(goal)=0, nên D(s)≤2k và
k≥ceil(D(s)/2). Mỗi lần lăn tốn ít nhất COST\_MIN, vì vậy:

$$
h^*(s) \ge k\cdot COST\_MIN
\ge \left\lceil D(s)/2 \right\rceil\cdot COST\_MIN
=h_{manhattan}(s).
$$

Trên màn có split mechanics, heuristic bằng 0 nên vẫn không vượt quá chi phí tối ưu.

#### Consistency

Trên màn không có split, mọi chuyển tiếp là lần lăn có chi phí c≥COST\_MIN. Từ
D(s)≤D(s')+2:

$$
\left\lceil D(s)/2 \right\rceil
\le \left\lceil (D(s')+2)/2 \right\rceil
= \left\lceil D(s')/2 \right\rceil+1.
$$

Nhân với COST\_MIN thu được h(s)≤c(s,a,s')+h(s'). Trên màn có split, hai đầu chuyển tiếp
đều có h=0, nên bất đẳng thức consistency cũng đúng.

### c) h_manhattan_orient — Manhattan theo tâm và tư thế

Tư thế được phản ánh trong tọa độ tâm. Không cộng thêm phạt “đứng dậy”: một lần lăn có thể vừa
đưa khối tới goal vừa đổi khối sang STAND.

$$
h_{manhattan\_orient}(s) =
\begin{cases}
0 & \text{nếu có split} \\
\left\lceil D(s)/1.5 \right\rceil \cdot \text{COST\_MIN} & \text{các trường hợp còn lại}
\end{cases}
$$

#### Admissibility

Mỗi lần lăn làm tâm dịch tối đa 1.5 ô theo một trục, nên D giảm tối đa 1.5. Nếu cần k lần
lăn để tới goal thì D(s) ≤ 1.5k, suy ra k ≥ ceil(D(s)/1.5). Mỗi lần lăn tốn ít nhất
COST\_MIN, do đó h_manhattan_orient(s) ≤ h*(s). Với split mechanics, hàm trả 0 nên cũng
admissible.

#### Consistency

Với một lần lăn s→s', ta có D(s) ≤ D(s')+1.5. Vì vậy:

$$
\left\lceil D(s)/1.5 \right\rceil
\le \left\lceil (D(s')+1.5)/1.5 \right\rceil
= \left\lceil D(s')/1.5 \right\rceil+1.
$$

Nhân với COST\_MIN và dùng c(s,a,s')≥COST\_MIN suy ra consistency. Trên màn split, cả
hai giá trị heuristic bằng 0.

### d) h_relaxed_maze — khoảng cách BFS trên lưới nới lỏng

Chạy BFS từ goal trên lưới, coi mọi ô khác "." là đi được. Cách này bỏ qua tư thế và trạng thái
cầu đóng, nên không gian đường đi được nới rộng hơn luật Bloxorz.

Với khối đứng, ô tham chiếu là ô đang chiếm. Với khối nằm ngang hoặc dọc, ô tham chiếu là ô trong
hai ô đang chiếm có khoảng cách BFS tới goal nhỏ hơn. Gọi khoảng cách đó là d(s):

$$
h_{relaxed\_maze}(s) =
\begin{cases}
0 & \text{nếu có split} \\
\left\lceil d(s)/2 \right\rceil \cdot \text{COST\_MIN} & \text{các trường hợp còn lại}
\end{cases}
$$

Khoảng cách BFS được cache theo lưới và tọa độ goal. Nếu ô tham chiếu không nối tới goal ngay cả
trên lưới nới lỏng, hàm trả math.inf; khi đó không có đường hợp lệ trong luật đầy đủ.

#### Admissibility

Trong một lần lăn, ô tham chiếu gần goal nhất có thể đổi sang ô kia của khối và dịch tối đa hai
cạnh trên lưới. Do đó d(s) ≤ d(s')+2. Sau k lần lăn tới trạng thái goal, d(goal) = 0, nên
d(s) ≤ 2k và k ≥ ceil(d(s)/2). Mỗi lần lăn có chi phí ít nhất COST\_MIN, suy ra:

$$
h^*(s) \ge k \cdot \text{COST\_MIN}
\ge \left\lceil d(s)/2 \right\rceil \cdot \text{COST\_MIN}
=h_{relaxed\_maze}(s).
$$

Lưới nới lỏng có thể làm đường ngắn hơn luật thật, không thể làm cận dưới này lớn hơn chi phí
đường đi thật. Trên màn split, hàm trả 0.

#### Consistency

Với một lần lăn, d(s) ≤ d(s')+2, nên:

$$
\left\lceil d(s)/2 \right\rceil
\le \left\lceil (d(s')+2)/2 \right\rceil
= \left\lceil d(s')/2 \right\rceil+1.
$$

Nhân với COST\_MIN và dùng c(s,a,s') ≥ COST\_MIN cho mọi lần lăn, ta có
x`h(s) ≤ c(s,a,s') + h(s'). Với split mechanics, hai giá trị heuristic đều bằng 0.

---

## 2.2 So sánh

| Heuristic | Admissible | Consistent | Chất lượng cận dưới | Chi phí tính toán |
|:---|:---:|:---:|:---|:---|
| h_0 | Có | Có | Luôn bằng 0 | O(1) |
| h_manhattan | Có | Có | Cận tâm khối, mẫu số 2 | O(1) |
| h_manhattan_orient | Có | Có | Cận tâm khối chặt hơn, mẫu số 1.5 | O(1) |
| h_relaxed_maze | Có | Có | Tính khoảng cách có xét đường đi trên lưới | O(R×C) lần đầu, O(1) tra cứu sau đó |

Các hàm hình học trả 0 trên màn có split mechanics. Trên màn không có split:

$$h_0(s) \le h_{manhattan}(s) \le h_{manhattan\_orient}(s).$$

h_relaxed_maze và hai heuristic Manhattan nhìn chung không so sánh được: BFS xét vật
cản của lưới nhưng dùng ô gần goal nhất, còn Manhattan dùng tâm khối. Nếu cần một heuristic kết
hợp, max(h_manhattan_orient,  h_relaxed_maze) vẫn admissible và consistent khi cả hai hàm thành
phần có các tính chất đó trên cùng màn chơi.
