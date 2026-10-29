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
Mục III thay lựa chọn h=0 này bằng các cận chặt hơn mà vẫn admissible và consistent.

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
h(s) ≤ c(s,a,s') + h(s'). Với split mechanics, hai giá trị heuristic đều bằng 0.

---

## 2.2 So sánh

| Heuristic | Admissible | Consistent | Chất lượng cận dưới | Chi phí tính toán |
|:---|:---:|:---:|:---|:---|
| h_0 | Có | Có | Luôn bằng 0 | O(1) |
| h_manhattan | Có | Có | Cận tâm khối, mẫu số 2 | O(1) |
| h_manhattan_orient | Có | Có | Cận tâm khối chặt hơn, mẫu số 1.5 | O(1) |
| h_relaxed_maze | Có | Có | Tính khoảng cách có xét đường đi trên lưới | O(R×C) lần đầu, O(1) tra cứu sau đó |
| h_switch_aware (mục III) | Có | Có | Đồ thị khối thật, theo đúng cầu đang đóng/mở, tính cả đoạn ghé công tắc | O(R×C) mỗi bitmask cầu lần đầu, O(1) sau đó |
| h_split_cubes (mục III) | Có | Có | Cận ghép hai cube rồi khối ghép tới đích | O(R×C) cho mỗi cặp vị trí cube lần đầu |
| h_advanced (mục III) | Có | Có | h_split_cubes khi đang tách, h_switch_aware khi chưa tách | như hai hàm thành phần |

Ba hàm hình học đầu trả 0 trên màn có split mechanics; ba hàm ở mục III không có hạn chế này.
Trên màn không có split:

$$h_0(s) \le h_{manhattan}(s) \le h_{manhattan\_orient}(s).$$

h_relaxed_maze và hai heuristic Manhattan nhìn chung không so sánh được: BFS xét vật
cản của lưới nhưng dùng ô gần goal nhất, còn Manhattan dùng tâm khối. Nếu cần một heuristic kết
hợp, max(h_manhattan_orient,  h_relaxed_maze) vẫn admissible và consistent khi cả hai hàm thành
phần có các tính chất đó trên cùng màn chơi.

---

## III. Heuristic nâng cao

Các heuristic ở mục II bỏ qua cầu và công tắc, và trả 0 trên màn có split. Mục này thêm ba
heuristic dùng được trên mọi nhóm màn. 

### 1. Phép nới lỏng dùng chung: đồ thị khối

| Ký hiệu | Ý nghĩa |
|:---|:---|
| $G_m$ | Đồ thị khối ứng với bitmask cầu m. Đỉnh là (r, c, tư thế) của khối 1×1×2, cạnh là phép lăn thật U/D/L/R. Đỉnh hợp lệ khi mọi ô khối chiếm là sàn (ô cầu chỉ là sàn nếu bit của nó trong m bằng 1) và khối không đứng trên ô dễ vỡ. Công tắc bị bỏ qua. |
| $G_{open}$ | Như $G_m$ nhưng mọi cầu đều mở. Hiển nhiên $G_m \subseteq G_{open}$. |
| $d_m(s, X)$ | Số lần lăn ít nhất trong $G_m$ từ s tới một đỉnh thuộc X ($\infty$ nếu không có). |
| T | Tập đích nới lỏng: {khối đứng trên goal} ∪ {khối đứng trên một công tắc split}. |
| P | Các vị trí khối kích hoạt công tắc có `targets`: công tắc mềm khi **bất kỳ** ô nào của khối nằm trên nó, công tắc nặng khi khối **đứng** trên nó. Công tắc split không thuộc P vì đã nằm trong T. |

**Hai tính chất của đồ thị khối.**

- (P1) Phép lăn nghịch đảo được (lăn rồi lăn ngược về đúng chỗ cũ) và tính hợp lệ chỉ phụ thuộc
  đỉnh đích, nên $G_m$ vô hướng. Vì vậy có thể chạy Dijkstra từ T ngược lại.
- (P2) **Bổ đề T.** Xét một đường đi thật từ trạng thái chưa tách s tới khi thắng. Tính đến lần
  đầu khối đứng trên một ô của T, mọi bước đều là phép lăn hợp lệ trong $G_{open}$ (luật thật chỉ
  chặt hơn: cầu có thể đóng, có thể rơi sau hiệu ứng công tắc). Đường đi chắc chắn chạm T: hoặc
  tới thẳng goal, hoặc phải đứng lên một công tắc split trước, vì đó là cách duy nhất để rời đồ
  thị khối (teleport). Mỗi lần lăn tốn ít nhất COST\_MIN, nên chi phí của đoạn đó
  $\ge \text{COST\_MIN} \cdot d_{open}(s, T)$.

### 2. h_switch_aware: khối chưa tách, theo đúng trạng thái cầu

Gọi m = bridges(s). Khi s chưa tách:

$$
h_{sw}(s) = \text{COST\_MIN} \cdot \min\Big( d_m(s, T),\ \min_{p \in P} \big[\, d_m(s, p) + d_{open}(p, T) \,\big] \Big)
$$

Khi s đang tách, hàm trả 0 (đã có $h_{split}$ ở mục 3). Hai số hạng ứng với hai khả năng của
một đường đi thật:

1. **(i)** tới T mà bitmask cầu chưa đổi: cầu đứng yên nên mọi bước là phép lăn trong $G_m$.
2. **(ii)** bitmask cầu đổi lần đầu khi khối tới vị trí kích hoạt $p \in P$: trước đó cầu đứng
   yên (đoạn $s \to p$ nằm trong $G_m$), sau đó chỉ cần cận "mọi cầu mở" $d_{open}(p, T)$.

Cả hai gộp thành **một** lần Dijkstra nhiều nguồn trên $G_m$: nguồn $t \in T$ với độ lệch 0,
nguồn $p \in P$ với độ lệch $d_{open}(p, T)$. Bảng kết quả được cache theo từng bitmask m.

**Ví dụ.** Màn dưới đây (`BRIDGE_LEVEL` trong test), khối bắt đầu ở (3,3), goal ở (1,4), cầu (2,3)
đóng, công tắc nặng ở (1,5):

```
######
####G#      Nếu coi cầu như đã mở thì chỉ cần 6 lần lăn.
######      Cầu đóng chắn đường nên phải đứng lên công tắc (1,5) trước:
##.###      h_sw(đầu) = 11 = h*(đầu).
```

Khi bit cầu đã bằng 1 (cầu đã mở) thì $h_{sw}$ giảm về 6, đúng khoảng cách trong $G_{open}$.

#### Admissibility

Xét đường tối ưu thật từ s. Gọi $\tau$ là thời điểm đầu tiên xảy ra một trong hai việc: khối đứng
trên ô của T, hoặc bitmask cầu đổi.

- Nếu xảy ra việc thứ nhất trước: đến $\tau$ cầu đứng yên, nên mọi bước là phép lăn hợp lệ trong
  $G_m$, chi phí $\ge \text{COST\_MIN} \cdot d_m(s, T)$.
- Nếu bitmask đổi trước, tại vị trí $p \in P$: đoạn tới p tốn $\ge \text{COST\_MIN} \cdot d_m(s, p)$.
  Phần còn lại từ p tốn $\ge \text{COST\_MIN} \cdot d_{open}(p, T)$ theo Bổ đề T.

Chi phí thật không nhỏ hơn số hạng tương ứng, nên không nhỏ hơn giá trị nhỏ nhất của hai số
hạng: $h_{sw}(s) \le h^*(s)$.

#### Consistency

Xét một bước $s \to s'$ chi phí $c \ge \text{COST\_MIN}$ (hoặc 1.2 khi bước bật công tắc).

- **Bitmask không đổi.** Cạnh $s \to s'$ nằm trong $G_m$. $h_{sw}/\text{COST\_MIN}$ là khoảng cách
  trong $G_m$ tính từ tập nguồn có độ lệch, nên thỏa bất đẳng thức tam giác:
  $h_{sw}(s) \le \text{COST\_MIN} + h_{sw}(s')$.
- **Bitmask đổi (m thành m').** Vị trí mới $p' = s'$ kích hoạt công tắc nên $p' \in P$, và phép lăn
  hợp lệ trong $G_m$, suy ra $d_m(s, p') \le 1$. Do đó
  $h_{sw}(s) \le \text{COST\_MIN}\,(1 + d_{open}(p', T))$. Mặt khác mọi số hạng của $h_{sw}(s')$ đều
  $\ge \text{COST\_MIN} \cdot d_{open}(s', T)$ vì $G_{m'} \subseteq G_{open}$ và bất đẳng thức tam giác
  trong $G_{open}$, nên $h_{sw}(s') \ge \text{COST\_MIN} \cdot d_{open}(p', T)$. Ghép lại:
  $h_{sw}(s) \le \text{COST\_MIN} + h_{sw}(s') \le c + h_{sw}(s')$.
- **Bước đứng lên công tắc split** (s' là trạng thái tách). Khi đó s cách một vị trí thuộc T đúng
  một lần lăn, nên $h_{sw}(s) \le \text{COST\_MIN} \le c$, còn $h_{sw}(s') \ge 0$.

#### Vì sao không cộng "phí bật công tắc"

Bước đổi cầu tốn 1.2, hơn lăn thường 0.2. Nhưng khoản này chỉ có khi dùng `make_cost_fn`; với
`Game` mặc định (mỗi bước 1.0) cộng thêm 0.2 sẽ vượt chi phí thật, mất admissible. Bước vừa chạm
ô dễ vỡ vừa đổi cầu cũng chỉ tốn 1.2 (quy tắc công tắc xét trước) nên không thể tính 1.5. Heuristic
chỉ dùng COST\_MIN, đúng với mọi hàm chi phí của nhóm.

### 3. h_split_cubes: trạng thái đang tách

Với hai cube ở $c_1, c_2$, để thắng phải ghép lại thành khối 1×1×2 (hai cube kề nhau) rồi khối
ghép đứng trên goal. Gọi $d(c, x)$ là khoảng cách 4 hướng của một cube đơn trên các ô không phải
ô trống (cầu coi như sàn, cube đứng được trên ô dễ vỡ), và $m(a,b)$ là khối nằm trên hai ô kề
nhau a, b. Khi s đang tách:

$$
h_{split}(s) = \text{COST\_MIN} \cdot \min_{(a,b)\ \text{kề nhau}}
\Big( \min\big[d(c_1,a)+d(c_2,b),\ d(c_1,b)+d(c_2,a)\big] + d_{open}(m(a,b), T) \Big)
$$

Khi s chưa tách, $h_{split}(s) = h_{sw}(s)$.

#### Admissibility

Đường thật từ trạng thái tách phải ghép cube ít nhất một lần; xét lần ghép đầu, tại cặp ô kề
$(a^*, b^*)$. Mỗi bước di chuyển một cube đi đúng 1 ô và tốn $\ge \text{COST\_MIN}$; hai cube di
chuyển độc lập nhau trong phép nới lỏng, nên cần $\ge d(c_1,a^*)+d(c_2,b^*)$ bước (hoặc hoán đổi
vai trò hai cube). Hành động S không di chuyển nên không được tính, vì vậy chi phí 0.5 của S không
làm cận quá tay. Sau khi ghép, phần còn lại bắt đầu bằng khối $m(a^*, b^*)$ và tốn
$\ge \text{COST\_MIN} \cdot d_{open}(m(a^*, b^*), T)$ theo Bổ đề T. Lấy min theo mọi cặp ô kề thì
$h_{split}(s) \le h^*(s)$.

#### Consistency

- **Một cube đi 1 ô** (chi phí $c \ge \text{COST\_MIN}$, vẫn tách): mọi $d(c_i, \cdot)$ đổi tối đa 1,
  nên $h_{split}(s) \le \text{COST\_MIN} + h_{split}(s')$.
- **Hành động S**: hoán đổi $c_1, c_2$. Công thức đối xứng theo hai cube nên $h_{split}$ không đổi,
  còn $c \ge 0$.
- **Bước ghép** (cube di chuyển làm hai cube kề nhau, s' là khối $m^* = m(a, b)$): chọn đúng cặp
  (a, b) đó thì $h_{split}(s) \le \text{COST\_MIN}\,(1 + d_{open}(m^*, T))$, và
  $h_{sw}(s') \ge \text{COST\_MIN} \cdot d_{open}(m^*, T)$ như ở mục 2.

### 4. h_advanced: heuristic mặc định

$$
h_{advanced}(s) =
\begin{cases}
h_{split}(s) & \text{nếu s đang tách} \\
h_{sw}(s) & \text{ngược lại}
\end{cases}
$$

Bốn loại chuyển trạng thái (chưa tách sang chưa tách, chưa tách sang tách, tách sang tách, tách
sang chưa tách) đều đã xét ở mục 2 và 3, nên $h_{advanced}$ admissible và consistent trên mọi
màn.

**So với các heuristic ở mục II.** Mọi $d_m(s,T) \ge d_{open}(s,T)$ và
$d_m(s,p)+d_{open}(p,T) \ge d_{open}(s,T)$ (bất đẳng thức tam giác), nên
$h_{sw}(s) \ge \text{COST\_MIN} \cdot d_{open}(s,T)$. Trên màn không có split, T chỉ có goal, và
một dãy phép lăn trong $G_{open}$ cũng là dãy phép lăn hợp lệ trên lưới các ô không trống, nên
độ dài của nó thỏa các cận $\lceil D/2 \rceil$, $\lceil D/1.5 \rceil$ và $\lceil d/2 \rceil$ đã
chứng minh ở mục II.2.1. Suy ra
$h_{advanced}(s) \ge \max(h_{manhattan}, h_{manhattan\_orient}, h_{relaxed\_maze})(s)$. Trên màn có
split hoặc với trạng thái đang tách, ba heuristic cũ bằng 0 nên bất đẳng thức hiển nhiên đúng.
Heuristic lớn hơn mà vẫn admissible thì A\* mở rộng ít nút hơn.

Trên màn chỉ có sàn và ô dễ vỡ (không cầu, công tắc, split), đồ thị khối trùng với đồ thị thật nên
$h_{advanced} = h^*$ khi chi phí đồng đều.

### 5. Chi phí tính toán, giới hạn

- **Tính toán:** mỗi bitmask cầu gặp phải cần một lần Dijkstra O(R×C) (cache theo bitmask); mỗi
  cặp vị trí cube mới cần O(R×C) (cache theo cặp). Mọi lần gọi sau đó là tra bảng O(1). Dữ liệu
  cache gắn với từng đối tượng `Level` và dựng ở lần gọi đầu, nên thời gian đo của lần chạy đầu
  tiên có cả phần dựng bảng.
- **Giới hạn:** trên màn có cầu hoặc split, các heuristic này chỉ là cận dưới (không chính xác).
  Chúng không dùng phí 1.2 và 1.5 của hàm chi phí (xem mục 2) và bỏ qua thứ tự bật công tắc của
  nhiều công tắc. 
