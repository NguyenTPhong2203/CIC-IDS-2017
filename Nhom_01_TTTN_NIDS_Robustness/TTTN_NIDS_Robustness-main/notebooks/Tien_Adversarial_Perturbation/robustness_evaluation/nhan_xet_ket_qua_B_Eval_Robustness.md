# Nhận xét kết quả đánh giá độ bền vững của các mô hình NIDS

## 1. Tổng quan thí nghiệm

Notebook `B_Eval_Robustness.ipynb` đánh giá ba mô hình dùng cho bài toán Network Intrusion Detection System (NIDS):

- LightGBM
- Random Forest
- XGBoost

Các mô hình được kiểm tra trên một tập test sạch (`B_test_scaled.parquet`) và sáu tập dữ liệu đã biến đổi bằng Padding:

- `test_padding_random_16B`
- `test_padding_random_64B`
- `test_padding_random_256B`
- `test_padding_static_16B`
- `test_padding_static_64B`
- `test_padding_static_256B`

Dữ liệu được đánh giá theo bài toán phân loại nhị phân:

- `Benign = 0`
- `Attack = 1`

Mỗi tập có **260.632 flow**, gồm **218.463 Benign** và **42.169 Attack**. Notebook sử dụng **82 feature** làm đầu vào cho cả ba mô hình. Tổng cộng có 21 lượt đánh giá (3 mô hình × 7 tập dữ liệu).

Notebook không fit lại scaler và cũng không scale lại dữ liệu. Vì vậy, các tập Parquet đầu vào được giả định đã được biến đổi bằng đúng scaler tương ứng với quy trình huấn luyện mô hình.

**Mục tiêu của thí nghiệm** là đánh giá khả năng phát hiện Attack trên dữ liệu sạch, sau đó xem khả năng này thay đổi như thế nào khi các feature đầu vào bị tác động bởi Padding.

> **Kết luận tổng quát:** Cả ba mô hình đều đạt hiệu năng rất cao trên tập test sạch. Tuy nhiên, sau Padding, LightGBM và Random Forest không còn phát hiện được flow Attack nào; XGBoost vẫn phát hiện được một phần Attack nhưng hiệu năng giảm mạnh. Đây là dấu hiệu rõ ràng cho thấy các mô hình chưa có độ bền vững tốt trước các tập Padding đang được kiểm tra.

---

## 2. Nhận xét hiệu năng trên dữ liệu sạch (Baseline)

Kết quả trên tập `Test sạch`:

| Mô hình | ROC-AUC | PR-AUC | Precision Attack | Recall Attack | Binary F1 | FPR |
|---|---:|---:|---:|---:|---:|---:|
| LightGBM | 0,99995 | 0,99981 | 0,99702 | 0,99979 | 0,99840 | 0,00058 |
| Random Forest | 0,99999 | 0,99994 | 0,99837 | 0,99948 | 0,99892 | 0,00032 |
| XGBoost | 0,99999 | 0,99995 | 0,99747 | 0,99964 | 0,99856 | 0,00049 |

### 2.1. LightGBM

LightGBM có ROC-AUC = **0,99995**, PR-AUC = **0,99981** và Recall Attack = **99,979%**.

Mô hình phát hiện đúng 42.160 trong 42.169 flow Attack, bỏ sót 9 flow. Có 126 flow Benign bị dự đoán nhầm thành Attack.

Đây là kết quả rất tốt trên tập test sạch: khả năng phát hiện Attack cao và tỷ lệ cảnh báo nhầm thấp.

### 2.2. Random Forest

Random Forest đạt ROC-AUC = **0,99999**, PR-AUC = **0,99994** và Binary F1 = **0,99892**.

Mô hình phát hiện đúng 42.147 flow Attack, bỏ sót 22 flow. Số flow Benign bị dự đoán nhầm thành Attack là 69, thấp nhất trong ba mô hình.

Nếu xét Binary F1, Precision và FPR trên dữ liệu sạch, Random Forest có kết quả nhỉnh hơn hai mô hình còn lại.

### 2.3. XGBoost

XGBoost đạt ROC-AUC = **0,99999** và PR-AUC = **0,99995**, là các giá trị cao nhất trong ba mô hình. Recall Attack đạt **99,964%**, tương ứng phát hiện đúng 42.154 flow và bỏ sót 15 flow.

Mô hình có 107 false positive trên lớp Benign. Kết quả nhìn chung rất tốt và khá cân bằng giữa khả năng phát hiện Attack với tỷ lệ cảnh báo nhầm.

### 2.4. So sánh baseline

Cả ba mô hình đều có hiệu năng gần như hoàn hảo trên tập test sạch. Khác biệt giữa các mô hình là rất nhỏ:

- XGBoost có ROC-AUC và PR-AUC cao nhất.
- Random Forest có Binary F1 cao nhất và FPR thấp nhất.
- LightGBM có Recall Attack cao nhất, nhưng chênh lệch rất nhỏ so với hai mô hình còn lại.

Ở giai đoạn này, chưa có cơ sở để nói một mô hình vượt trội rõ rệt so với hai mô hình còn lại. Cả ba đều là những mô hình có kết quả baseline rất tốt theo các chỉ số notebook đã tính.

### 2.5. Lưu ý về baseline gần như hoàn hảo

ROC-AUC và PR-AUC xấp xỉ 1, Recall gần 100% là kết quả rất cao. Đây là tín hiệu tích cực, nhưng cũng cần kiểm tra kỹ trước khi khẳng định mô hình có khả năng tổng quát hóa gần như hoàn hảo.

Nên xác minh:

1. Tập train, validation và test có được chia tách độc lập theo đúng quy trình hay không.
2. Có flow trùng lặp hoặc bản ghi gần giống nhau giữa train và test hay không.
3. Có feature nào vô tình chứa thông tin trực tiếp hoặc gián tiếp về nhãn hay không.
4. Scaler và các bước tiền xử lý có được fit trên tập train בלבד, sau đó áp dụng cho validation/test hay không.
5. Artifact mô hình có được huấn luyện đúng trên tập train của cùng phiên bản dữ liệu đang đánh giá hay không.

Đây là các bước kiểm tra để loại trừ nguy cơ data leakage hoặc trùng lặp dữ liệu. Kết quả notebook hiện tại chưa đủ để kết luận có leakage; đây là vấn đề cần xác minh vì baseline quá cao.

---

## 3. Nhận xét khả năng chống chịu trên dữ liệu Padding

Kết quả trên cả sáu tập Padding:

| Mô hình | Recall Attack trên dữ liệu sạch | Recall Attack sau Padding | Binary F1 sau Padding |
|---|---:|---:|---:|
| LightGBM | 99,979% | 0% | 0 |
| Random Forest | 99,948% | 0% | 0 |
| XGBoost | 99,964% | 61,597% | 0,36245 |

### 3.1. LightGBM

Sau Padding, LightGBM có kết quả:

- Recall Attack = 0%.
- Precision Attack = 0%.
- Binary F1 = 0.
- TP = 0, FN = 42.169.

Điều này có nghĩa là mô hình không phát hiện đúng bất kỳ flow Attack nào trong sáu tập dữ liệu Padding. Toàn bộ 42.169 flow Attack đều bị bỏ sót.

Đáng chú ý, FPR = 0 nhưng đây không phải kết quả tốt trong trường hợp này. Mô hình dự đoán toàn bộ flow là Benign nên không tạo ra false positive, nhưng đồng thời bỏ sót toàn bộ Attack.

### 3.2. Random Forest

Random Forest cũng có kết quả tương tự LightGBM:

- Recall Attack = 0%.
- Precision Attack = 0%.
- Binary F1 = 0.
- TP = 0, FN = 42.169.

Mô hình gần như mất hoàn toàn khả năng phát hiện Attack sau Padding. Mặc dù trên tập sạch Random Forest đạt Binary F1 = 0,99892, chỉ số này giảm xuống 0 trên các tập biến đổi.

Đây là mức suy giảm rất nghiêm trọng và cho thấy hiệu năng baseline cao không đồng nghĩa với khả năng chống chịu tốt.

### 3.3. XGBoost

XGBoost vẫn duy trì được một phần khả năng phát hiện Attack sau Padding:

- Precision Attack = 0,25677 (khoảng 25,68%).
- Recall Attack = 0,61597 (khoảng 61,60%).
- Binary F1 = 0,36245.
- TP = 25.975, FN = 16.194.
- FP = 75.186.

Mô hình phát hiện đúng 25.975 flow Attack, nhưng bỏ sót 16.194 flow. Đồng thời, có tới 75.186 flow Benign bị dự đoán nhầm thành Attack.

Điều này cho thấy XGBoost có khả năng duy trì Recall tốt hơn hai mô hình còn lại, nhưng phải đánh đổi bằng số lượng cảnh báo nhầm rất lớn. Precision chỉ khoảng 25,68%, nghĩa là trong các flow được dự đoán là Attack, phần lớn không phải Attack theo nhãn thật.

Trong môi trường NIDS, tình trạng này có thể tạo ra lượng cảnh báo giả lớn, làm tăng khối lượng công việc cho người vận hành và khiến việc xử lý cảnh báo trở nên khó khăn.

### 3.4. So sánh ba mô hình sau Padding

- **LightGBM:** không phát hiện được Attack.
- **Random Forest:** không phát hiện được Attack.
- **XGBoost:** còn phát hiện được khoảng 61,60% Attack, nhưng tỷ lệ cảnh báo nhầm rất cao.

XGBoost là mô hình có kết quả tốt nhất trong ba mô hình trên các tập Padding nếu xét khả năng giữ lại Recall Attack. Tuy nhiên, không nên gọi đây là mô hình robust tốt theo nghĩa tổng thể, vì Precision và F1 vẫn giảm mạnh.

---

## 4. So sánh các kiểu Padding

Notebook kiểm tra hai cách Padding:

- Random Padding.
- Static Padding.

Mỗi cách được đánh giá ở ba kích thước: 16B, 64B và 256B.

Kết quả phân loại của từng mô hình gần như giống nhau trên cả sáu tập:

| Mô hình | Random 16/64/256B | Static 16/64/256B |
|---|---|---|
| LightGBM | Recall = 0%, F1 = 0 | Recall = 0%, F1 = 0 |
| Random Forest | Recall = 0%, F1 = 0 | Recall = 0%, F1 = 0 |
| XGBoost | Recall ≈ 61,60%, F1 ≈ 0,36245 | Recall ≈ 61,60%, F1 ≈ 0,36245 |

### Nhận xét

Trong kết quả hiện tại, sự khác biệt giữa Random Padding và Static Padding là rất nhỏ. Thay đổi kích thước từ 16B lên 64B hoặc 256B cũng không làm thay đổi đáng kể các chỉ số phân loại.

Điều này cho thấy các biến thể Padding đang tạo ra tác động tương tự nhau đối với đầu vào của mô hình trong thí nghiệm này.

Tuy nhiên, không nên kết luận rằng kích thước Padding hoặc phương pháp Padding không quan trọng trong mọi trường hợp. Kết luận chỉ giới hạn ở sáu tập dữ liệu, cách tạo Padding và pipeline tiền xử lý đang được sử dụng.

---

## 5. Nhận xét Attack Success Rate (ASR)

Notebook định nghĩa ASR theo cách tính có đối chiếu từng flow:

1. Chọn các flow có nhãn thật là Attack.
2. Chỉ giữ các flow mà mô hình dự đoán đúng là Attack trên tập sạch.
3. Kiểm tra các flow đó trên tập Padding.
4. Đếm số flow bị chuyển từ dự đoán Attack sang dự đoán Benign.
5. Chia cho tổng số flow đủ điều kiện ở bước 2.

Kết quả ASR:

| Mô hình | ASR trên sáu tập Padding |
|---|---:|
| LightGBM | 100% |
| Random Forest | 100% |
| XGBoost | 38,402% |

### 5.1. LightGBM

ASR = 100% nghĩa là toàn bộ các flow Attack được LightGBM phát hiện đúng trên tập sạch đều bị phân loại thành Benign sau Padding.

Trên tập sạch, LightGBM phát hiện đúng 42.160 flow Attack. Sau Padding, mô hình không phát hiện đúng flow Attack nào.

### 5.2. Random Forest

Random Forest có ASR = 100%. Có 42.147 flow Attack được phát hiện đúng trên dữ liệu sạch, nhưng các flow này đều bị phân loại thành Benign sau Padding.

### 5.3. XGBoost

XGBoost có ASR = 38,402%. Điều này có nghĩa là trong nhóm flow Attack được mô hình phát hiện đúng trên tập sạch, khoảng 38,40% bị phân loại thành Benign sau Padding.

XGBoost vẫn phát hiện được một phần Attack sau biến đổi, vì vậy ASR thấp hơn đáng kể so với LightGBM và Random Forest.

### 5.4. Cách diễn giải ASR

ASR của LightGBM và Random Forest bằng 100% cho thấy hai mô hình này bị evasion hoàn toàn trên nhóm Attack đủ điều kiện tính ASR.

XGBoost có ASR thấp hơn, nhưng vẫn bị ảnh hưởng đáng kể. Khoảng 38,40% nhóm Attack được phát hiện đúng ban đầu đã bị phân loại sai thành Benign.

Cần phân biệt:

- **ASR:** đo tỷ lệ evasion trong nhóm Attack được phát hiện đúng trên dữ liệu sạch.
- **Robust Recall:** đo tỷ lệ Attack được phát hiện trên toàn bộ Attack của tập Padding.

Hai chỉ số trả lời hai câu hỏi khác nhau và không nên thay thế cho nhau.

---

## 6. Nhận xét mức độ thay đổi đặc trưng (Perturbation)

Notebook tính các chỉ số trên 82 feature đầu vào đã scale:

- **L0:** số lượng feature thay đổi trung bình trên mỗi flow có thay đổi.
- **L2:** độ lớn biến đổi Euclidean của vector feature.
- **L∞ (Linf):** độ thay đổi tuyệt đối lớn nhất trong các feature của một flow.

Kết quả trên sáu tập Padding gần như giống nhau:

| Chỉ số | Kết quả |
|---|---:|
| Số flow có thay đổi | 260.632 |
| Tổng số flow | 260.632 |
| Số feature đầu vào | 82 |
| L0 trung bình | 82 |
| L2 trung bình | khoảng 62.617.920 |
| L∞ trung bình | khoảng 43.515.650 |

### 6.1. L0 = 82 có ý nghĩa gì?

L0 = 82 trong khi mô hình sử dụng 82 feature. Điều này cho thấy trung bình cả 82 feature đều thay đổi trên mỗi flow có thay đổi.

Ngoài ra, số flow có thay đổi là 260.632, bằng đúng tổng số flow. Như vậy, toàn bộ flow trong từng tập Padding đều có ít nhất một feature thay đổi; và theo L0 trung bình, toàn bộ 82 feature đều thay đổi.

Đây là một biến đổi rộng trên không gian feature, không phải chỉ thay đổi một vài feature riêng lẻ.

### 6.2. L2 và L∞ rất lớn

L2 khoảng 62,6 triệu và L∞ khoảng 43,5 triệu là các giá trị rất lớn nếu so với cách hiểu thông thường về dữ liệu đã scale.

Điều này cần được kiểm tra kỹ trước khi kết luận về cường độ biến đổi. Có thể xem xét:

1. Dữ liệu sạch và dữ liệu Padding có cùng thang đo hay không.
2. Các feature có được scale bằng đúng scaler dùng trong quá trình huấn luyện hay không.
3. Có feature nào chứa giá trị bất thường hoặc bị thay đổi ngoài dự kiến hay không.
4. Phép đo norm có đang sử dụng đúng 82 feature đầu vào hay không.
5. Các giá trị Padding ở dữ liệu gốc đã được chuyển đổi sang feature như thế nào.

Lưu ý rằng notebook ghi rõ các norm được tính trên chênh lệch feature đã scale. Vì vậy, cần xác minh quy trình tiền xử lý và cách tạo dữ liệu trước khi sử dụng các giá trị norm này để khẳng định mức nhiễu là nhỏ hay lớn.

### 6.3. Ý nghĩa đối với kết quả mô hình

Việc cả 82 feature đều thay đổi giúp giải thích vì sao hiệu năng mô hình suy giảm mạnh: mô hình không chỉ phải xử lý một vài giá trị nhiễu cục bộ mà nhận được vector đầu vào thay đổi trên toàn bộ các chiều feature.

Tuy nhiên, chỉ số norm không tự chứng minh nguyên nhân gây suy giảm. Cần phân tích thêm từng feature và quy trình tạo Padding để xác định mối liên hệ cụ thể.

---

## 7. Nhận xét tính hợp lệ và Alignment

Notebook ghi nhận trên cả sáu tập Padding:

- `Aligned_with_clean = True`.
- Alignment được xác nhận bằng `__orig_row`.
- `Validity_Ratio = 1.0`.
- `Constraint_Violation_Rate = 0.0`.

### 7.1. Alignment

Tất cả sáu tập Padding đều có 260.632 dòng, nhãn `Label_binary` cùng thứ tự với tập sạch và cột `__orig_row` khớp thứ tự dòng gốc.

Điều này cho phép notebook đối chiếu từng flow giữa dữ liệu sạch và dữ liệu đã biến đổi. Đây là điều kiện quan trọng để tính ASR và perturbation norms theo từng mẫu.

### 7.2. Validity

Validity Ratio = 100% và Constraint Violation Rate = 0% cho biết không có dòng nào bị đánh dấu là thất bại theo cột `__validation_failed` được sử dụng trong notebook.

Đây là kết quả tích cực theo cơ chế validation hiện có.

Tuy nhiên, notebook cũng nêu rõ rằng validity được tính từ cờ `__validation_failed`; không tự suy diễn tính hợp lệ vật lý từ các feature đã scale.

Vì vậy, không nên diễn giải Validity = 100% thành việc dữ liệu Padding chắc chắn có thể xuất hiện hợp lệ trong lưu lượng mạng thực tế. Cần biết cụ thể các ràng buộc nào đã được kiểm tra, chẳng hạn miền giá trị, quan hệ giữa các feature và tính nhất quán của flow.

---

## 8. Nhận xét về Inference Latency

Notebook đo thời gian dự đoán trung bình trên mỗi flow. Trên tập test sạch, kết quả ghi nhận:

| Mô hình | Inference time (ms/flow) |
|---|---:|
| LightGBM | 0,00202 |
| XGBoost | 0,00221 |
| Random Forest | 0,00787 |

Theo số liệu này, LightGBM có thời gian dự đoán trung bình thấp nhất, tiếp theo là XGBoost. Random Forest có thời gian dự đoán cao hơn hai mô hình còn lại.

Đây là chỉ số tham khảo về chi phí dự đoán, không phải kết luận đầy đủ về tốc độ triển khai thực tế. Thời gian có thể phụ thuộc phần cứng, tải hệ thống, số luồng xử lý, trạng thái bộ nhớ và cách đo.

Nếu muốn so sánh latency một cách chặt chẽ, nên warm-up mô hình, đo lặp nhiều lần trên cùng điều kiện và báo cáo trung vị hoặc trung bình kèm độ phân tán.

---

## 9. Những điểm cần kiểm tra và cải thiện

### 9.1. Kiểm tra nguy cơ data leakage

Baseline gần như hoàn hảo là điểm cần xác minh đầu tiên. Cần kiểm tra cách chia train/test, bản ghi trùng lặp, feature có chứa thông tin nhãn và quy trình fit scaler.

Nếu baseline bị ảnh hưởng bởi leakage, các kết luận về hiệu năng thực tế của mô hình sẽ không đáng tin cậy.

### 9.2. Xác minh scaler và quy trình tạo Padding

Notebook không fit lại scaler và không scale lại dữ liệu. Vì vậy, cần bảo đảm tất cả tập Padding được biến đổi bằng đúng scaler, đúng thứ tự feature và đúng quy trình tiền xử lý như dữ liệu huấn luyện.

Đây là bước quan trọng để tránh việc mô hình nhận dữ liệu ngoài thang đo hoặc ngoài schema dự kiến.

### 9.3. Phân tích theo từng feature

L0 = 82 cho thấy toàn bộ feature đều thay đổi. Nên bổ sung bảng thống kê theo từng feature:

- Mean và standard deviation trước/sau Padding.
- Min và max trước/sau Padding.
- Số lượng flow có feature thay đổi.
- Độ thay đổi tuyệt đối trung bình.
- Những feature có mức thay đổi lớn nhất.

Phân tích này sẽ giúp xác định feature nào bị tác động mạnh và có thể liên quan đến sự suy giảm của mô hình.

### 9.4. Phân tích theo từng loại Attack

Notebook hiện chỉ đánh giá nhị phân Benign/Attack. Cách này phù hợp để đánh giá khả năng phát hiện tổng thể, nhưng chưa cho biết loại tấn công nào bị ảnh hưởng nhiều nhất.

Nếu dữ liệu còn nhãn loại Attack ban đầu, nên đánh giá Recall và F1 theo từng loại tấn công trước và sau Padding.

### 9.5. Bổ sung Precision–Recall và phân tích threshold

XGBoost vẫn giữ Recall khoảng 61,60% nhưng Precision chỉ khoảng 25,68%. Điều này cho thấy mô hình tạo ra rất nhiều cảnh báo nhầm.

Có thể phân tích đường Precision–Recall và lựa chọn threshold trên tập validation độc lập để tìm điểm cân bằng giữa Recall và Precision. Không nên điều chỉnh threshold trên tập test rồi dùng chính tập test đó để báo cáo kết quả cuối cùng.

Việc điều chỉnh threshold cũng không được mặc định là sẽ giải quyết được vấn đề robustness.

### 9.6. Bổ sung TSR nếu nghiên cứu có đánh giá transfer attack

Notebook ghi `TSR_available = False` và để TSR = NaN vì không có kết quả surrogate-to-target tương ứng.

Đây không phải lỗi tính toán. Nếu nghiên cứu muốn đánh giá khả năng chuyển giao của tấn công giữa các mô hình, cần cung cấp kết quả tấn công từ surrogate và dự đoán trên target. Nếu không nằm trong phạm vi nghiên cứu, nên ghi rõ TSR chưa được đánh giá.

### 9.7. Kiểm tra ý nghĩa của các norm

L2 và L∞ rất lớn dù dữ liệu được mô tả là đã scale. Nên xác minh thang đo, đơn vị, feature đầu vào và cách tính norm trước khi dùng các giá trị này để so sánh cường độ biến đổi giữa các thí nghiệm.

---

## 10. Kết luận tổng hợp

Kết quả trên tập test sạch cho thấy cả ba mô hình LightGBM, Random Forest và XGBoost đều đạt hiệu năng rất cao, với ROC-AUC và PR-AUC gần bằng 1, Recall Attack xấp xỉ 100% và Binary F1 trên 0,998. Random Forest có Binary F1 cao nhất và FPR thấp nhất, trong khi XGBoost có PR-AUC cao nhất. Khác biệt baseline giữa ba mô hình là không lớn.

Tuy nhiên, khi đánh giá trên sáu tập dữ liệu Padding, hiệu năng của cả ba mô hình suy giảm rõ rệt. LightGBM và Random Forest không phát hiện được flow Attack nào, khiến Recall và Binary F1 đều bằng 0. XGBoost duy trì được Recall khoảng 61,60% và phát hiện đúng 25.975 flow Attack, nhưng Precision chỉ còn khoảng 25,68% do có 75.186 flow Benign bị dự đoán nhầm thành Attack.

ASR của LightGBM và Random Forest đều bằng 100%, trong khi XGBoost đạt 38,402%. Kết quả này cho thấy Padding có thể làm các mô hình mất khả năng nhận diện những flow Attack mà chúng đã phát hiện đúng trên dữ liệu sạch. XGBoost có khả năng chống chịu tương đối tốt hơn hai mô hình còn lại trong thí nghiệm này, nhưng vẫn chưa đạt hiệu năng đủ cân bằng để có thể xem là robust tốt.

Phân tích perturbation cho thấy toàn bộ 260.632 flow đều bị thay đổi và trung bình cả 82 feature đầu vào đều thay đổi. Các giá trị L2 và L∞ rất lớn, do đó cần xác minh lại scaler và quy trình tạo dữ liệu trước khi diễn giải mức độ nhiễu. Các tập Padding được xác nhận alignment bằng `__orig_row` và đạt Validity Ratio = 100% theo cờ validation hiện có; tuy nhiên, kết quả này chưa chứng minh tính hợp lệ hoàn toàn trong môi trường mạng thực tế.

**Nhìn chung, thí nghiệm cho thấy hiệu năng cao trên dữ liệu sạch không bảo đảm khả năng chống chịu trước biến đổi Padding.** Trong ba mô hình, XGBoost giữ lại được một phần khả năng phát hiện Attack, nhưng phải đánh đổi bằng tỷ lệ cảnh báo nhầm lớn. Trước khi đưa ra kết luận cuối cùng về độ bền vững đối kháng, cần xác minh nguy cơ data leakage, quy trình scale, cách tạo Padding và mức thay đổi của từng feature.

---

## 11. Đoạn nhận xét ngắn có thể đưa vào báo cáo

Thực nghiệm đánh giá ba mô hình LightGBM, Random Forest và XGBoost trên tập test sạch và sáu tập dữ liệu được biến đổi bằng Random Padding và Static Padding ở các kích thước 16B, 64B và 256B. Trên tập test sạch, cả ba mô hình đều đạt hiệu năng rất cao với ROC-AUC, PR-AUC gần bằng 1 và Recall Attack xấp xỉ 100%. Tuy nhiên, sau khi áp dụng Padding, hiệu năng của các mô hình suy giảm đáng kể. LightGBM và Random Forest không phát hiện được flow Attack nào, khiến Recall và Binary F1 giảm xuống 0. XGBoost duy trì Recall khoảng 61,60% và phát hiện đúng 25.975 flow Attack, nhưng Precision chỉ còn khoảng 25,68% do xuất hiện 75.186 false positive. ASR của LightGBM và Random Forest đều đạt 100%, trong khi XGBoost đạt 38,402%, cho thấy các biến đổi Padding đã làm suy giảm khả năng nhận diện những flow Attack được phát hiện đúng trên dữ liệu sạch. Phân tích perturbation cho thấy toàn bộ flow đều bị thay đổi và trung bình cả 82 feature đầu vào đều thay đổi. Mặc dù XGBoost có khả năng duy trì Recall tốt hơn hai mô hình còn lại, tỷ lệ cảnh báo nhầm cao khiến hiệu năng tổng thể vẫn chưa đáp ứng tốt yêu cầu của một hệ thống NIDS robust. Do đó, kết quả bước đầu cho thấy cả ba mô hình chưa có độ bền vững tốt trước các tập Padding đang xét. Cần kiểm tra thêm nguy cơ data leakage, quy trình scale và tính hợp lệ thực tế của dữ liệu để củng cố kết luận nghiên cứu.
