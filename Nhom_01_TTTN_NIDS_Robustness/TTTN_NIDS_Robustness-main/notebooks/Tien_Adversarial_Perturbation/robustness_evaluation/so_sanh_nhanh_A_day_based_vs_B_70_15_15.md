# So sánh kết quả thực nghiệm: Nhánh A (Day-based split) và Nhánh B (70-15-15 split)

## 1. Mục tiêu

Tài liệu này tổng hợp và so sánh hai nhánh thực nghiệm đánh giá độ bền vững đối kháng (*Adversarial Robustness*) của các mô hình Network Intrusion Detection System (NIDS) trước các biến đổi Padding.

- **Nhánh A – Day-based split:** dữ liệu được chia theo ngày.
- **Nhánh B – 70-15-15 split:** dữ liệu được chia theo tỷ lệ 70% Train, 15% Validation và 15% Test.

Cả hai nhánh đánh giá ba mô hình:

- LightGBM
- Random Forest
- XGBoost

Mục tiêu so sánh không chỉ là xác định mô hình nào có chỉ số cao hơn, mà còn xem cách chia dữ liệu ảnh hưởng như thế nào đến kết quả đánh giá trên dữ liệu sạch và dữ liệu bị biến đổi.

> **Phạm vi:** Các số liệu dưới đây được tổng hợp từ hai notebook đánh giá và hai tài liệu nhận xét tương ứng. Không tự suy diễn các thông tin huấn luyện chưa được ghi nhận trong những nguồn này.

---

## 2. Tổng quan hai nhánh

| Tiêu chí | Nhánh A – Day-based | Nhánh B – 70-15-15 |
|---|---:|---:|
| Chiến lược chia dữ liệu | Theo ngày | 70% Train – 15% Validation – 15% Test |
| File test sạch | `test_scaled.parquet` | `B_test_scaled.parquet` |
| Số flow trong tập test | 620.183 | 260.632 |
| Benign | 517.754 | 218.463 |
| Attack | 102.429 | 42.169 |
| Tỷ lệ Attack | Khoảng 16,52% | Khoảng 16,18% |
| Số feature perturbation được ghi nhận | 79 | 82 |
| Số mô hình | 3 | 3 |
| Số tập Padding | 6 | 6 |
| Tổng lượt đánh giá | 21 | 21 |

Cả hai nhánh đều đánh giá nhị phân:

- `Benign = 0`
- `Attack = 1`

Sáu tập Padding trong mỗi nhánh gồm:

1. `test_padding_random_16B`
2. `test_padding_random_64B`
3. `test_padding_random_256B`
4. `test_padding_static_16B`
5. `test_padding_static_64B`
6. `test_padding_static_256B`

**Lưu ý về quy mô:** Nhánh A có số flow test lớn hơn Nhánh B khoảng 2,38 lần. Hai nhánh cũng sử dụng số feature perturbation được ghi nhận khác nhau (79 và 82). Vì vậy, không nên xem đây là hai phép đo hoàn toàn tương đương nếu chưa xác minh cùng schema, cùng nguồn dữ liệu và cùng quy trình tiền xử lý.

---

## 3. So sánh hiệu năng trên dữ liệu sạch (Baseline)

### 3.1. Kết quả định lượng

| Nhánh | Mô hình | ROC-AUC | PR-AUC | Precision Attack | Recall Attack | F1 Attack / Binary F1 | FPR |
|---|---|---:|---:|---:|---:|---:|---:|
| A | LightGBM | 0,98735 | 0,97147 | 0,40000 | 0,00002 | 0,00004 | 0,00001 |
| A | Random Forest | 0,97780 | 0,96285 | 1,00000 | 0,65853 | 0,79412 | 0,00000 |
| A | XGBoost | 0,99332 | 0,97915 | 0,99376 | 0,01089 | 0,02154 | 0,00001 |
| B | LightGBM | 0,99995 | 0,99981 | 0,99702 | 0,99979 | 0,99840 | 0,00058 |
| B | Random Forest | 0,99999 | 0,99994 | 0,99837 | 0,99948 | 0,99892 | 0,00032 |
| B | XGBoost | 0,99999 | 0,99995 | 0,99747 | 0,99964 | 0,99856 | 0,00049 |

*Ghi chú:* Nhánh A báo cáo `F1 Attack`; Nhánh B báo cáo `Binary F1`. Do Attack là lớp positive trong cả hai notebook, các giá trị được đặt cạnh nhau để tham khảo. Tuy nhiên, cần kiểm tra lại cách tính và cấu hình metric trước khi coi chúng là hoàn toàn đồng nhất.

### 3.2. Nhận xét Nhánh A

- **Random Forest** có kết quả phân loại Attack tốt nhất tại threshold đang sử dụng: Recall = 65,853%, F1 = 0,79412 và Precision = 1,0.
- **XGBoost** có ROC-AUC và PR-AUC cao nhất, nhưng Recall chỉ đạt 1,089%. Điều này cho thấy khả năng xếp hạng score tốt không đồng nghĩa với khả năng phát hiện Attack tốt tại threshold hiện tại.
- **LightGBM** gần như không phát hiện được Attack: chỉ đúng 2 flow trong 102.429 flow Attack.

Như vậy, trên baseline của Nhánh A, Random Forest là mô hình có khả năng phát hiện Attack tốt nhất tại threshold đang dùng. XGBoost có chất lượng ranking cao nhưng kết quả phân loại nhị phân tại threshold hiện tại còn yếu.

### 3.3. Nhận xét Nhánh B

Cả ba mô hình đều đạt kết quả gần như hoàn hảo trên tập test sạch:

- LightGBM có Recall Attack = 99,979%.
- Random Forest có Binary F1 cao nhất = 0,99892 và FPR thấp nhất = 0,00032.
- XGBoost có PR-AUC cao nhất = 0,99995.

Khác biệt giữa ba mô hình trong Nhánh B rất nhỏ. Cả ba đều phát hiện gần như toàn bộ Attack trên tập test sạch.

### 3.4. Khác biệt nổi bật giữa hai nhánh

Sự khác biệt lớn nhất xuất hiện ở baseline:

- Nhánh A: chỉ Random Forest có Recall Attack ở mức tương đối tốt; LightGBM và XGBoost có Recall rất thấp.
- Nhánh B: cả ba mô hình đều có Recall gần 100% và F1 gần 1.

Đây là khác biệt đáng chú ý về mặt thực nghiệm. Tuy nhiên, **không thể kết luận chỉ riêng phương pháp chia dữ liệu đã tạo ra khác biệt này**. Cần xác minh thêm artifact mô hình, dữ liệu train/validation/test, threshold, schema feature, scaler và quy trình tiền xử lý của từng nhánh.

---

## 4. So sánh khả năng chống chịu sau Padding

### 4.1. Recall và F1 sau Padding

| Nhánh | Mô hình | Recall sạch | Recall sau Padding | F1 sau Padding |
|---|---|---:|---:|---:|
| A | LightGBM | 0,00002 | 0,00000 | 0,00000 |
| A | Random Forest | 0,65853 | 0,00008 | 0,00013 |
| A | XGBoost | 0,01089 | 0,00008 | 0,00014 |
| B | LightGBM | 0,99979 | 0,00000 | 0,00000 |
| B | Random Forest | 0,99948 | 0,00000 | 0,00000 |
| B | XGBoost | 0,99964 | 0,61597 | 0,36245 |

Các giá trị sau Padding được ghi nhận gần như giống nhau giữa sáu biến thể Random/Static và 16B/64B/256B trong từng nhánh.

### 4.2. Nhánh A

- LightGBM vốn đã có Recall gần 0 trên dữ liệu sạch và tiếp tục không phát hiện được Attack sau Padding.
- Random Forest giảm Recall từ 65,853% xuống khoảng 0,008%; số Attack phát hiện đúng giảm từ 67.453 xuống còn 8.
- XGBoost giảm Recall từ 1,089% xuống khoảng 0,008%; số Attack phát hiện đúng giảm từ 1.115 xuống còn 8.

Random Forest là trường hợp thể hiện rõ nhất sự suy giảm giữa baseline và dữ liệu Padding, vì mô hình có baseline tốt hơn đáng kể so với hai mô hình còn lại.

### 4.3. Nhánh B

- LightGBM giảm Recall từ 99,979% xuống 0%.
- Random Forest giảm Recall từ 99,948% xuống 0%.
- XGBoost giảm Recall từ 99,964% xuống 61,597%.

LightGBM và Random Forest không phát hiện được flow Attack nào trên sáu tập Padding. XGBoost vẫn phát hiện đúng 25.975 flow Attack, nhưng có 16.194 false negative và 75.186 false positive; Precision Attack chỉ còn khoảng 25,68%.

### 4.4. Nhận xét so sánh

Cả hai nhánh đều cho thấy hiệu năng phát hiện Attack suy giảm nghiêm trọng khi đầu vào bị Padding.

Điểm khác biệt là:

- Nhánh A: sau Padding, Recall của cả ba mô hình đều gần bằng 0.
- Nhánh B: LightGBM và Random Forest mất hoàn toàn khả năng phát hiện Attack; XGBoost vẫn duy trì Recall khoảng 61,60%, dù Precision và F1 giảm mạnh.

XGBoost là mô hình giữ lại Recall tốt nhất trong Nhánh B. Tuy nhiên, với Precision khoảng 25,68%, không nên xem kết quả này là robustness tốt về tổng thể vì số cảnh báo nhầm rất lớn.

---

## 5. So sánh Attack Success Rate (ASR)

ASR trong hai notebook được tính theo cùng ý tưởng: chỉ xét các flow có nhãn thật là Attack và đã được mô hình dự đoán đúng là Attack trên dữ liệu sạch; sau đó đo tỷ lệ các flow này bị dự đoán thành Benign trên dữ liệu Padding.

| Nhánh | Mô hình | ASR | Số flow đủ điều kiện tính ASR |
|---|---|---:|---:|
| A | LightGBM | 100% | 2 |
| A | Random Forest | 100% | 67.453 |
| A | XGBoost | 100% | 1.115 |
| B | LightGBM | 100% | 42.160 |
| B | Random Forest | 100% | 42.147 |
| B | XGBoost | 38,402% | 42.154 |

### Nhận xét

**Nhánh A:**

- Cả ba mô hình có ASR = 100%.
- Tuy nhiên, mẫu số ASR rất khác nhau. Đặc biệt, LightGBM chỉ có 2 flow đủ điều kiện, nên không thể diễn giải ASR = 100% của mô hình này như bằng chứng evasion trên số lượng lớn flow.
- Random Forest có mẫu số 67.453 flow, do đó kết quả ASR có quy mô mẫu đáng kể hơn.

**Nhánh B:**

- LightGBM và Random Forest có ASR = 100% trên hơn 42 nghìn flow đủ điều kiện mỗi mô hình.
- XGBoost có ASR = 38,402%, nghĩa là khoảng 38,40% nhóm Attack được phát hiện đúng trên dữ liệu sạch bị chuyển thành Benign sau Padding.

**Kết luận:** ASR của Nhánh A và Nhánh B không nên được so sánh đơn thuần bằng con số phần trăm. Cần xem đồng thời mẫu số ASR. Trong Nhánh B, số mẫu đủ điều kiện lớn và tương đối đồng đều giữa các mô hình; trong Nhánh A, số mẫu phụ thuộc mạnh vào khả năng phát hiện baseline của từng mô hình.

---

## 6. So sánh mức độ thay đổi đặc trưng (Perturbation)

| Chỉ số | Nhánh A – Day-based | Nhánh B – 70-15-15 |
|---|---:|---:|
| Tổng flow trong mỗi tập Padding | 620.183 | 260.632 |
| Flow có thay đổi | 620.183 | 260.632 |
| Số feature đầu vào được ghi nhận | 79 | 82 |
| L0 trung bình | 79 | 82 |
| L2 trung bình | Khoảng 48.465.870 | Khoảng 62.617.920 |
| L∞ trung bình | Khoảng 28.309.940 | Khoảng 43.515.650 |

### Nhận xét

- Cả hai nhánh đều ghi nhận toàn bộ flow trong các tập Padding có thay đổi.
- Theo kết quả L0, toàn bộ số feature được đưa vào phép đo đều thay đổi trung bình trên mỗi flow đã thay đổi.
- L2 và L∞ của Nhánh B lớn hơn Nhánh A theo số liệu notebook.

Tuy nhiên, không nên kết luận Padding ở Nhánh B mạnh hơn Nhánh A chỉ dựa trên L2 và L∞. Hai nhánh đang ghi nhận số feature khác nhau (82 so với 79), quy mô dữ liệu khác nhau và có thể sử dụng scaler hoặc pipeline tiền xử lý khác nhau.

Các giá trị L2 và L∞ đều rất lớn so với kỳ vọng thông thường khi mô tả đầu vào là dữ liệu đã scale. Cần kiểm tra:

1. Cùng danh sách feature và cùng thứ tự feature hay không.
2. Cùng scaler đã fit trên tập train tương ứng hay không.
3. Các tập Padding có được biến đổi bằng đúng scaler của nhánh hay không.
4. Có feature nào chứa giá trị bất thường hoặc bị biến đổi ngoài dự kiến hay không.
5. Phép tính norm có sử dụng cùng định nghĩa và cùng tập feature hay không.

Vì vậy, kết quả perturbation hiện tại hỗ trợ nhận định rằng đầu vào bị thay đổi trên diện rộng, nhưng chưa đủ cơ sở để so sánh trực tiếp cường độ biến đổi giữa hai nhánh.

---

## 7. So sánh Alignment và Validity

| Tiêu chí | Nhánh A | Nhánh B |
|---|---|---|
| Alignment với dữ liệu sạch | Được xác nhận | Được xác nhận |
| Cơ chế đối chiếu | `__orig_row` / row identifier và thứ tự nhãn | `__orig_row` / row identifier và thứ tự nhãn |
| Validity Ratio | 100% | 100% |
| Constraint Violation Rate | 0% | 0% |
| Ý nghĩa giới hạn | Theo cờ validation hiện có | Theo cờ validation hiện có |

Hai notebook xác nhận khả năng đối chiếu flow sạch và flow Padding để tính ASR và perturbation norms. Validity Ratio = 100% cho biết không có dòng nào bị đánh dấu thất bại theo cột `__validation_failed` được sử dụng.

Cần phân biệt rõ: **Validity = 100% không đồng nghĩa dữ liệu Padding chắc chắn hợp lệ về mặt vật lý hoặc có thể xuất hiện trong lưu lượng mạng thực tế.** Kết quả chỉ phản ánh các quy tắc validation đã được áp dụng.

---

## 8. Những điểm tương đồng và khác biệt chính

### 8.1. Điểm tương đồng

1. Cùng đánh giá LightGBM, Random Forest và XGBoost.
2. Cùng sử dụng bài toán phân loại nhị phân Benign/Attack.
3. Cùng kiểm tra một tập test sạch và sáu tập Padding.
4. Cùng đánh giá hai kiểu Random Padding và Static Padding ở 16B, 64B và 256B.
5. Cùng tính ASR theo các flow Attack được phát hiện đúng trên dữ liệu sạch.
6. Cả hai đều cho thấy hiệu năng suy giảm nghiêm trọng sau Padding.
7. Cả hai đều ghi nhận perturbation tác động đến toàn bộ flow và nhiều feature đầu vào.

### 8.2. Điểm khác biệt

| Khía cạnh | Nhánh A – Day-based | Nhánh B – 70-15-15 |
|---|---|---|
| Baseline | Không đồng đều; Random Forest tốt nhất | Cả ba mô hình gần như hoàn hảo |
| Mô hình tốt nhất trên clean tại threshold hiện tại | Random Forest | Khác biệt nhỏ; RF có F1 cao nhất |
| Mô hình có ROC-AUC/PR-AUC cao nhất | XGBoost | XGBoost |
| Robust Recall sau Padding | Cả ba gần 0 | XGBoost còn khoảng 61,60% |
| ASR | Cả ba 100%, mẫu số không đồng đều | LGBM/RF 100%; XGBoost 38,402% |
| Quy mô test | 620.183 flow | 260.632 flow |
| Feature perturbation | 79 | 82 |

---

## 9. Ý nghĩa của hai chiến lược chia dữ liệu đối với NIDS

### 9.1. Day-based split (Nhánh A)

Chia theo ngày có thể phản ánh bài toán đánh giá theo thời gian: mô hình được huấn luyện trên một giai đoạn và kiểm tra trên dữ liệu thuộc ngày hoặc giai đoạn khác.

Cách chia này có ý nghĩa khi muốn nghiên cứu khả năng tổng quát hóa trước sự thay đổi lưu lượng theo thời gian (*temporal distribution shift*).

Tuy nhiên, để xác nhận đúng ý nghĩa này, cần kiểm tra cụ thể:

- Những ngày nào được dùng cho Train, Validation và Test.
- Thứ tự thời gian có được giữ đúng không.
- Có flow hoặc bản ghi trùng lặp giữa các tập không.
- Các bước tiền xử lý có chỉ fit trên Train không.

Kết quả Nhánh A cho thấy baseline thấp ở LightGBM và XGBoost tại threshold hiện tại, trong khi Random Forest có Recall tốt hơn. Đây là thông tin quan trọng khi đánh giá mô hình trong bối cảnh chia dữ liệu theo ngày.

### 9.2. Random 70-15-15 split (Nhánh B)

Chia ngẫu nhiên theo tỷ lệ 70-15-15 tạo ra tập Train, Validation và Test theo tỷ lệ đã định. Cách chia này có thể giúp các tập có phân phối gần nhau hơn nếu dữ liệu được lấy mẫu ngẫu nhiên phù hợp.

Tuy nhiên, nếu dữ liệu có nhiều flow tương quan, flow trùng lặp hoặc các bản ghi từ cùng phiên/nguồn, chia ngẫu nhiên có thể khiến các mẫu liên quan xuất hiện ở nhiều tập. Điều này có thể làm kết quả test lạc quan hơn.

Baseline gần như hoàn hảo trong Nhánh B là dấu hiệu cần kiểm tra kỹ, nhưng **chưa đủ để kết luận có data leakage**.

Cần xác minh:

- Cách thực hiện random split và `random_state`.
- Có stratify theo nhãn hay không.
- Có nhóm theo session, source, destination hoặc thời gian trước khi chia hay không.
- Có duplicate hoặc near-duplicate giữa Train, Validation và Test không.
- Scaler và các bước chọn feature có chỉ fit trên Train không.
- Artifact mô hình có đúng được huấn luyện từ split tương ứng không.

### 9.3. Không nên kết luận nhánh nào tốt hơn chỉ dựa vào metric

Hai nhánh khác nhau cả về chiến lược chia dữ liệu, số lượng test flow, số feature được ghi nhận và kết quả baseline. Vì vậy, đây không phải một phép so sánh chỉ thay đổi duy nhất biến số “phương pháp chia dữ liệu”.

Muốn kết luận tác động của split strategy, cần kiểm soát các yếu tố còn lại và xác minh pipeline của hai nhánh.

---

## 10. Các vấn đề cần ưu tiên xác minh

| Mức ưu tiên | Vấn đề | Lý do |
|---|---|---|
| Rất cao | Data leakage / duplicate / near-duplicate | Baseline Nhánh B gần như hoàn hảo, cần loại trừ khả năng đánh giá lạc quan |
| Rất cao | Quy trình fit scaler | Hai nhánh phải dùng scaler đúng với tập Train tương ứng |
| Rất cao | Danh sách và thứ tự feature | Nhánh A ghi nhận 79 feature, Nhánh B ghi nhận 82 feature |
| Cao | Ngưỡng phân loại | A và B có thể đang sử dụng threshold khác nhau hoặc mô hình có phân phối score khác nhau |
| Cao | Alignment của dữ liệu Padding | Cần chắc chắn so sánh đúng cùng một flow trước/sau biến đổi |
| Cao | Cách tạo Padding | Cần xác nhận hai nhánh dùng cùng thuật toán và cấu hình biến đổi |
| Trung bình | Perturbation norms | L2 và L∞ rất lớn, cần kiểm tra thang đo và cách tính |
| Trung bình | Phân tích theo loại Attack | Đánh giá nhị phân chưa cho biết loại tấn công nào bị ảnh hưởng nhiều nhất |
| Trung bình | Inference latency | Cần đo lặp và cùng điều kiện phần cứng nếu muốn so sánh |

Một lưu ý quan trọng: cả hai notebook đều không fit lại scaler trong giai đoạn đánh giá. Các tập Parquet đầu vào được giả định đã scale bằng scaler tương ứng với quá trình huấn luyện. Vì vậy, tính đúng đắn của bước scale cần được xác nhận ở pipeline tạo dữ liệu.

---

## 11. Kết luận tổng hợp

Hai nhánh thực nghiệm cùng cho thấy các mô hình NIDS có thể suy giảm nghiêm trọng khi đầu vào bị biến đổi bằng Padding, nhưng mức độ và biểu hiện suy giảm khác nhau.

Ở Nhánh A (Day-based split), Random Forest có baseline tốt nhất với Recall Attack = 65,85% và F1 = 0,79412. LightGBM và XGBoost có Recall rất thấp tại threshold hiện tại. Sau Padding, Recall của cả ba mô hình đều gần bằng 0. ASR đạt 100%, nhưng mẫu số tính ASR khác nhau đáng kể; đặc biệt LightGBM chỉ có 2 flow đủ điều kiện.

Ở Nhánh B (70-15-15 split), cả ba mô hình có baseline gần như hoàn hảo. Tuy nhiên, sau Padding, LightGBM và Random Forest không phát hiện được Attack, trong khi XGBoost giữ được Recall khoảng 61,60% nhưng Precision chỉ khoảng 25,68% và F1 khoảng 0,36245. ASR của LightGBM và Random Forest là 100%, còn XGBoost là 38,402%.

Như vậy, kết quả không ủng hộ việc chỉ dựa vào baseline để lựa chọn mô hình NIDS. Khả năng duy trì Recall, Precision, F1 và ASR trên dữ liệu biến đổi cần được xem xét đồng thời. XGBoost ở Nhánh B giữ được Recall tốt hơn hai mô hình còn lại, nhưng tỷ lệ false positive cao khiến hiệu năng tổng thể vẫn chưa tốt.

**Kết luận quan trọng về phương pháp:** Nhánh A và Nhánh B cung cấp hai góc nhìn đánh giá khác nhau: chia theo ngày hướng đến bối cảnh thay đổi theo thời gian, còn chia ngẫu nhiên 70-15-15 phản ánh kết quả trên một phép chia ngẫu nhiên. Tuy nhiên, chưa thể khẳng định chênh lệch kết quả là do chiến lược chia dữ liệu gây ra, vì cần xác minh tính tương đương của nguồn dữ liệu, feature, scaler, artifact mô hình, threshold và quy trình tạo Padding.

Trước khi đưa ra kết luận cuối cùng trong báo cáo nghiên cứu, nên ưu tiên kiểm tra data leakage, duplicate/near-duplicate, scaler và sự khác biệt 79/82 feature. Sau đó, có thể thực hiện lại hai nhánh với pipeline được kiểm soát thống nhất để đánh giá công bằng ảnh hưởng của chiến lược chia dữ liệu.

---

## 12. Đoạn nhận xét ngắn dùng trong báo cáo

Nghiên cứu thực hiện hai nhánh đánh giá độ bền vững đối kháng của các mô hình NIDS, gồm Nhánh A sử dụng chiến lược chia dữ liệu theo ngày và Nhánh B sử dụng tỷ lệ chia ngẫu nhiên 70-15-15. Cả hai nhánh đều đánh giá LightGBM, Random Forest và XGBoost trên dữ liệu sạch cùng sáu tập dữ liệu được biến đổi bằng Random Padding và Static Padding ở các kích thước 16B, 64B và 256B. Kết quả cho thấy baseline giữa hai nhánh có sự khác biệt đáng kể. Ở Nhánh A, Random Forest có Recall Attack cao nhất, đạt 65,85%, trong khi LightGBM và XGBoost có Recall rất thấp tại threshold hiện tại. Ngược lại, ở Nhánh B, cả ba mô hình đều đạt Recall gần 100% trên dữ liệu sạch. Tuy nhiên, sau Padding, hiệu năng của các mô hình suy giảm nghiêm trọng ở cả hai nhánh. Tại Nhánh A, Recall của cả ba mô hình đều gần bằng 0; tại Nhánh B, LightGBM và Random Forest không phát hiện được Attack, còn XGBoost duy trì Recall khoảng 61,60% nhưng Precision chỉ còn khoảng 25,68%. Các kết quả cho thấy hiệu năng trên dữ liệu sạch không bảo đảm khả năng chống chịu trước biến đổi đầu vào. Đồng thời, sự khác biệt baseline giữa hai nhánh cho thấy cần xem xét ảnh hưởng của chiến lược chia dữ liệu và kiểm tra tính nhất quán của pipeline. Đặc biệt, cần xác minh nguy cơ data leakage, dữ liệu trùng lặp, scaler, threshold và sự khác biệt về số feature trước khi quy kết nguyên nhân cho phương pháp chia dữ liệu.

---

## 13. Nguồn kết quả

- `A_Eval_Robustness.ipynb`
- `nhan_xet_ket_qua_A_Eval_Robustness.md`
- `B_Eval_Robustness.ipynb`
- `nhan_xet_ket_qua_B_Eval_Robustness.md`

**Quy ước:** A = Day-based split; B = Random 70-15-15 split.
