# Nhận xét kết quả đánh giá độ bền vững của các mô hình NIDS

## 1. Mục tiêu và phạm vi đánh giá

Notebook `A_Eval_Robustness.ipynb` thực hiện đánh giá ba mô hình học máy dùng cho bài toán phát hiện xâm nhập mạng (Network Intrusion Detection System – NIDS):

- LightGBM
- Random Forest
- XGBoost

Các mô hình được đánh giá trên **1 tập test sạch** và **6 tập dữ liệu đã biến đổi bằng Padding**:

- `test_padding_random_16B`
- `test_padding_random_64B`
- `test_padding_random_256B`
- `test_padding_static_16B`
- `test_padding_static_64B`
- `test_padding_static_256B`

Mỗi tập có 620.183 flow, gồm 517.754 mẫu Benign và 102.429 mẫu Attack. Notebook dùng nhãn nhị phân `Label_binary`, trong đó Benign = 0 và Attack = 1. Tổng cộng có 21 lượt đánh giá (3 mô hình × 7 tập dữ liệu).

Mục tiêu chính là xem mô hình có phát hiện được lưu lượng tấn công trên dữ liệu bình thường hay không, và khả năng đó thay đổi như thế nào khi các đặc trưng đầu vào bị biến đổi.

> **Kết luận tổng quát:** Random Forest có kết quả baseline tốt nhất trong ba mô hình nếu xét khả năng phát hiện Attack tại ngưỡng dự đoán hiện tại. Tuy nhiên, cả ba mô hình đều suy giảm rất mạnh trên sáu tập Padding. Đây là dấu hiệu cho thấy các mô hình hiện tại chưa có độ bền vững tốt trước những biến đổi đầu vào được kiểm tra.

---

## 2. Nhận xét hiệu năng trên dữ liệu sạch (Baseline)

Kết quả trên tập `Test sạch`:

| Mô hình | ROC-AUC | PR-AUC | Precision Attack | Recall Attack | F1 Attack | FPR |
|---|---:|---:|---:|---:|---:|---:|
| LightGBM | 0,98735 | 0,97147 | 0,40000 | 0,00002 | 0,00004 | 0,00001 |
| Random Forest | 0,97780 | 0,96285 | 1,00000 | 0,65853 | 0,79412 | 0,00000 |
| XGBoost | 0,99332 | 0,97915 | 0,99376 | 0,01089 | 0,02154 | 0,00001 |

### 2.1. Random Forest

Random Forest có Recall Attack khoảng **65,85%** và F1 Attack khoảng **0,79412**. Trong 102.429 flow Attack, mô hình phát hiện đúng 67.453 flow và bỏ sót 34.976 flow. Mô hình không tạo ra false positive trên tập test sạch theo kết quả confusion matrix.

Đây là mô hình có khả năng phát hiện Attack tốt nhất trong ba mô hình tại ngưỡng dự đoán đang sử dụng. Precision = 1,00 cho thấy các mẫu được dự đoán là Attack trong tập test sạch đều là Attack theo kết quả hiện tại.

Tuy vậy, Recall vẫn còn khoảng 34,15% flow Attack bị bỏ sót. Với một hệ thống NIDS, đây vẫn là tỷ lệ bỏ sót đáng quan tâm.

### 2.2. XGBoost

XGBoost có ROC-AUC và PR-AUC cao nhất, lần lượt là **0,99332** và **0,97915**. Tuy nhiên, Recall Attack chỉ đạt khoảng **1,09%**, tương ứng phát hiện đúng 1.115 trong 102.429 flow Attack.

Điều này cho thấy điểm số xếp hạng của mô hình khá tốt, nhưng nhãn dự đoán tại ngưỡng hiện tại chưa tốt. Nói đơn giản, mô hình có thể xếp nhiều mẫu Attack ở vị trí có điểm số cao hơn mẫu Benign, nhưng ngưỡng phân loại đang dùng khiến phần lớn mẫu Attack vẫn bị gán thành Benign.

### 2.3. LightGBM

LightGBM có ROC-AUC = 0,98735 và PR-AUC = 0,97147, nhưng Recall Attack gần như bằng 0. Mô hình chỉ phát hiện đúng **2 flow Attack** trong tổng số 102.429 flow Attack; đồng thời có 3 flow Benign bị dự đoán nhầm thành Attack.

Vì vậy, dù ROC-AUC và PR-AUC cao, LightGBM gần như không sử dụng được để phát hiện Attack nếu giữ nguyên cách lấy nhãn dự đoán hiện tại.

### 2.4. Kết luận baseline

Nếu mục tiêu là phát hiện Attack tại ngưỡng dự đoán đang dùng, thứ tự kết quả là:

1. **Random Forest:** tốt nhất về Recall và F1 Attack.
2. **XGBoost:** có ROC-AUC và PR-AUC cao nhất, nhưng Recall tại ngưỡng hiện tại rất thấp.
3. **LightGBM:** gần như không phát hiện được Attack tại ngưỡng hiện tại.

Cần phân biệt rõ hai nhóm chỉ số:

- **ROC-AUC và PR-AUC:** đánh giá chất lượng điểm số/xếp hạng dự đoán trên nhiều ngưỡng.
- **Precision, Recall và F1:** phản ánh kết quả phân loại tại ngưỡng đang được mô hình sử dụng.

Do đó, không nên chỉ nhìn ROC-AUC hoặc PR-AUC để kết luận một mô hình NIDS phát hiện tấn công tốt. Recall Attack và F1 Attack đặc biệt quan trọng vì chúng phản ánh khả năng phát hiện và tỷ lệ bỏ sót tấn công.

---

## 3. Nhận xét khả năng chống chịu trên dữ liệu Padding

Trên cả sáu tập Padding, kết quả của ba mô hình gần như không thay đổi theo từng kiểu Padding và kích thước 16B, 64B, 256B.

| Mô hình | Recall Attack trên dữ liệu sạch | Recall Attack sau Padding | F1 sau Padding |
|---|---:|---:|---:|
| LightGBM | 0,00002 | 0,00000 | 0,00000 |
| Random Forest | 0,65853 | 0,00008 | 0,00013 |
| XGBoost | 0,01089 | 0,00008 | 0,00014 |

### 3.1. LightGBM

Trên dữ liệu sạch, LightGBM đã có Recall Attack gần bằng 0. Sau Padding, mô hình không phát hiện đúng flow Attack nào trong kết quả được ghi nhận.

Recall và F1 đều bằng 0 trên cả sáu tập biến đổi. Điều này cho thấy mô hình không duy trì được khả năng phát hiện Attack sau biến đổi. Tuy nhiên, vì baseline của LightGBM vốn đã rất yếu ở ngưỡng hiện tại, không nên xem riêng kết quả này là bằng chứng mạnh nhất về mức suy giảm do Padding.

### 3.2. Random Forest

Đây là trường hợp đáng chú ý nhất khi so sánh baseline với dữ liệu biến đổi.

- Recall Attack giảm từ **65,85% xuống 0,008%** (xấp xỉ).
- F1 Attack giảm từ **0,79412 xuống 0,00013**.
- Số flow Attack phát hiện đúng giảm từ 67.453 xuống còn 8.
- Số false negative tăng từ 34.976 lên 102.421.

Nói cách khác, Random Forest vốn phát hiện được phần lớn Attack trên dữ liệu sạch nhưng gần như mất hoàn toàn khả năng phát hiện sau Padding.

Đây là dấu hiệu rõ ràng cho thấy mô hình nhạy với biến đổi đặc trưng đầu vào và chưa có khả năng duy trì hiệu năng khi gặp các tập dữ liệu Padding được kiểm tra.

### 3.3. XGBoost

Recall Attack giảm từ khoảng **1,09% xuống 0,008%**. Số flow Attack phát hiện đúng giảm từ 1.115 xuống còn 8.

XGBoost cũng suy giảm mạnh. Mặc dù có ROC-AUC và PR-AUC cao nhất trên tập sạch, lợi thế này không được duy trì trên các tập Padding.

### 3.4. So sánh các kiểu Padding

Kết quả trên `random` và `static`, cũng như giữa 16B, 64B và 256B, gần như giống nhau đối với từng mô hình.

Điều này gợi ý rằng trong các tập dữ liệu hiện tại, tác động của Padding lên đầu vào mô hình có thể lớn hơn khác biệt giữa cách tạo Padding hoặc kích thước Padding.

Tuy nhiên, chưa thể kết luận rằng kích thước Padding không ảnh hưởng đến mô hình trong mọi trường hợp. Kết luận này chỉ đúng với sáu tập dữ liệu và cách tạo dữ liệu đang được đánh giá.

---

## 4. Nhận xét Attack Success Rate (ASR)

Notebook tính ASR theo flow:

1. Chỉ chọn các flow có nhãn thật là Attack.
2. Trong số đó, chỉ giữ các flow mà mô hình đã dự đoán đúng là Attack trên dữ liệu sạch.
3. Đếm số flow trong nhóm trên bị dự đoán thành Benign sau biến đổi.
4. Chia số flow bị evasion cho số flow đủ điều kiện ở bước 2.

Kết quả ASR của cả ba mô hình đều bằng **1,0 (100%)** trên sáu tập Padding.

Có thể hiểu rằng: trong nhóm Attack mà từng mô hình đã phát hiện đúng trên dữ liệu sạch, toàn bộ các flow đó đều bị phân loại thành Benign sau Padding theo kết quả notebook.

### Cần đặc biệt lưu ý khi diễn giải ASR

Mặc dù cả ba mô hình đều có ASR = 100%, số lượng flow đủ điều kiện để tính ASR không giống nhau:

| Mô hình | Flow Attack được phát hiện đúng trên dữ liệu sạch (mẫu số ASR) |
|---|---:|
| LightGBM | 2 |
| Random Forest | 67.453 |
| XGBoost | 1.115 |

Vì vậy:

- Với Random Forest, ASR = 100% được tính trên 67.453 flow. Đây là bằng chứng có sức nặng hơn về số lượng mẫu so với hai mô hình còn lại.
- Với XGBoost, ASR = 100% được tính trên 1.115 flow.
- Với LightGBM, ASR = 100% chỉ được tính trên 2 flow. Không nên diễn giải kết quả này như thể mô hình đã bị đánh lừa trên một lượng lớn flow Attack.

**Nhận xét:** ASR cho thấy Padding đã làm mất khả năng phát hiện các flow Attack mà mô hình từng phát hiện đúng trên dữ liệu sạch. Tuy nhiên, cần báo cáo kèm mẫu số ASR để người đọc hiểu quy mô thực tế của kết quả.

---

## 5. Nhận xét mức độ thay đổi đặc trưng (Perturbation)

Notebook sử dụng ba chỉ số để đo độ lớn biến đổi:

- **L0:** số lượng feature bị thay đổi trung bình trên mỗi flow đã thay đổi.
- **L2:** độ lớn biến đổi Euclidean của vector feature.
- **L∞ (Linf):** độ thay đổi tuyệt đối lớn nhất trong các feature của một flow.

Kết quả trên sáu tập Padding gần như giống nhau:

| Chỉ số | Kết quả trung bình |
|---|---:|
| Số flow có thay đổi | 620.183 |
| L0 | 79 feature |
| L2 | khoảng 48.465.870 |
| L∞ | khoảng 28.309.940 |

### Diễn giải

- Có **620.183/620.183 flow** được ghi nhận có ít nhất một feature thay đổi.
- L0 = 79 cho thấy trung bình 79 feature thay đổi trên mỗi flow đã thay đổi. Theo kết quả này, toàn bộ 79 feature đầu vào được tính trong phép đo đều bị thay đổi.
- L2 và L∞ có giá trị rất lớn, cho thấy độ biến đổi trong không gian feature là đáng kể theo thang đo đang dùng.

Đây là một điểm rất quan trọng: Padding 16B, 64B hay 256B không đồng nghĩa với việc vector feature chỉ thay đổi một lượng nhỏ tương ứng 16, 64 hay 256 đơn vị. Kích thước Padding ở mức dữ liệu gốc và độ thay đổi sau tiền xử lý/scale là hai khái niệm khác nhau.

### Vấn đề cần kiểm tra

Giá trị L2 và L∞ rất lớn trong khi notebook mô tả dữ liệu đầu vào là dữ liệu đã scale. Vì vậy, cần kiểm tra lại:

1. Các feature được đưa vào mô hình có thực sự ở cùng thang đo như dữ liệu lúc huấn luyện hay không.
2. Quy trình tạo sáu tập Padding có áp dụng đúng scaler đã dùng khi huấn luyện hay không.
3. Có feature nào mang giá trị rất lớn hoặc bị biến đổi ngoài dự kiến hay không.
4. Việc tính norm có đang dùng đúng danh sách feature đầu vào của mô hình hay không.

Không nên vội kết luận các norm lớn là sai, nhưng cần xác minh trước khi dùng chúng để khẳng định mức độ nhiễu là nhỏ hay lớn.

---

## 6. Nhận xét tính hợp lệ của dữ liệu (Validity)

Kết quả notebook ghi nhận:

- `Validity_Ratio = 1.0` trên cả sáu tập Padding.
- `Constraint_Violation_Rate = 0.0`.
- Tất cả sáu tập đều được xác nhận alignment với tập sạch thông qua cột `__orig_row`.

### Ý nghĩa

**Alignment** cho biết notebook có cơ sở để đối chiếu flow trước và sau biến đổi theo thứ tự dòng. Đây là điều kiện cần để tính ASR và perturbation norms theo từng flow.

**Validity** trong notebook được tính từ cột `__validation_failed`. Tỷ lệ vi phạm bằng 0 cho biết không có dòng nào bị đánh dấu là thất bại theo cơ chế validation được cung cấp trong dữ liệu.

### Giới hạn khi diễn giải

Validity = 100% không tự động chứng minh rằng dữ liệu sau Padding hoàn toàn hợp lệ về mặt mạng máy tính hoặc có thể xuất hiện trong môi trường thực tế.

Kết quả này phụ thuộc vào các quy tắc validation đã được áp dụng trước đó. Vì vậy, cần mô tả rõ những ràng buộc nào đã được kiểm tra, chẳng hạn kiểu dữ liệu, miền giá trị, quan hệ giữa các feature và tính nhất quán của flow.

---

## 7. Ý nghĩa đối với hệ thống Network Intrusion Detection

Từ kết quả hiện tại, có thể rút ra ba nhận xét chính:

### 7.1. Hiệu năng trên dữ liệu sạch chưa phản ánh đầy đủ độ bền vững

Một mô hình có ROC-AUC hoặc PR-AUC cao trên dữ liệu sạch chưa chắc có khả năng chống chịu tốt trước biến đổi đầu vào.

XGBoost là ví dụ rõ ràng: có ROC-AUC = 0,99332 và PR-AUC = 0,97915 trên tập sạch, nhưng Recall Attack sau Padding gần như bằng 0.

### 7.2. Padding có thể làm giảm nghiêm trọng khả năng phát hiện xâm nhập

Sau Padding, phần lớn flow Attack bị phân loại thành Benign. Nếu hiện tượng này xuất hiện trong môi trường triển khai thực tế, NIDS có thể bỏ sót lưu lượng độc hại.

Đối với hệ thống phát hiện xâm nhập, đây là rủi ro đáng quan tâm vì false negative có thể khiến hoạt động tấn công không được cảnh báo.

### 7.3. Cần đánh giá robustness song song với detection performance

Không nên chỉ chọn mô hình dựa trên kết quả test sạch. Một mô hình NIDS cần được đánh giá ít nhất trên:

- Khả năng phát hiện Attack trên dữ liệu sạch.
- Recall và F1 của lớp Attack.
- Khả năng duy trì hiệu năng sau biến đổi.
- ASR và mẫu số dùng để tính ASR.
- Mức độ thay đổi feature.
- Tính hợp lệ của dữ liệu sau biến đổi.

---

## 8. Những điểm cần kiểm tra và cải thiện trong thí nghiệm

Các kết quả hiện tại cho thấy xu hướng suy giảm rất mạnh, nhưng để kết luận khoa học chặt chẽ hơn, nên kiểm tra các vấn đề sau.

### 8.1. Xác minh quy trình scale dữ liệu

Notebook ghi rõ không fit lại scaler và không scale lại dữ liệu. Các file Parquet phải được scale bằng scaler tương ứng với quá trình huấn luyện mô hình.

Cần xác nhận rằng sáu tập Padding thực sự dùng đúng scaler và đúng thứ tự feature. Đây là bước quan trọng vì nếu dữ liệu sau biến đổi không cùng cách tiền xử lý với dữ liệu huấn luyện, mô hình có thể nhận đầu vào ngoài phân phối.

### 8.2. Kiểm tra từng feature bị thay đổi

L0 = 79 trên tất cả các tập là kết quả cần được kiểm tra kỹ. Nên bổ sung bảng thống kê cho từng feature:

- Giá trị trung bình và độ lệch chuẩn trước/sau biến đổi.
- Min, max trước/sau biến đổi.
- Số lượng flow mà feature bị thay đổi.
- Mức thay đổi tuyệt đối trung bình của feature.

Việc này giúp xác định Padding đang tác động trực tiếp đến những feature nào và mức độ tác động ra sao.

### 8.3. Bổ sung phân tích theo từng loại Attack

Notebook hiện đánh giá theo nhãn nhị phân Benign/Attack. Cách này phù hợp để đánh giá khả năng phát hiện tổng thể, nhưng chưa cho biết loại tấn công nào bị ảnh hưởng nhiều nhất.

Nếu dữ liệu còn nhãn đa lớp hoặc nhãn loại tấn công ban đầu, nên phân tích Recall theo từng loại Attack trước và sau Padding.

### 8.4. Phân tích ngưỡng phân loại

XGBoost và LightGBM có ROC-AUC, PR-AUC cao nhưng Recall tại ngưỡng hiện tại rất thấp.

Nên đánh giá thêm đường Precision–Recall và thử lựa chọn threshold trên tập validation độc lập. Không nên điều chỉnh threshold dựa trên tập test rồi dùng chính tập test đó để báo cáo kết quả cuối cùng.

Việc điều chỉnh threshold có thể cải thiện Recall trên dữ liệu sạch, nhưng không được mặc định rằng nó sẽ giải quyết được vấn đề suy giảm trên dữ liệu Padding.

### 8.5. Bổ sung đánh giá lặp lại và độ ổn định

Latency hiện tại được đo trong một lần gọi `predict` trên từng dataset. Đây chỉ nên xem là số liệu tham khảo, vì thời gian chạy có thể phụ thuộc phần cứng, tải hệ thống và trạng thái bộ nhớ.

Nếu muốn so sánh tốc độ triển khai, nên warm-up, đo lặp nhiều lần và báo cáo trung vị hoặc trung bình kèm độ phân tán.

### 8.6. Làm rõ giới hạn của TSR

Notebook để `TSR = NaN` và ghi nhận `TSR_available = False`.

Đây không phải lỗi tính toán. TSR không được tính vì chưa có kết quả surrogate và target tương ứng để đánh giá transferability. Nếu nghiên cứu không thực hiện tấn công chuyển giao giữa mô hình, có thể giữ chỉ số này ngoài phạm vi kết quả hoặc giải thích rõ là chưa đánh giá.

---

## 9. Kết luận tổng hợp

Kết quả thực nghiệm cho thấy Random Forest là mô hình có hiệu năng phát hiện Attack tốt nhất trên tập test sạch, với Recall đạt 65,85% và F1 đạt 0,79412. XGBoost đạt ROC-AUC và PR-AUC cao nhất, nhưng Recall Attack tại ngưỡng hiện tại chỉ đạt 1,09%. LightGBM gần như không phát hiện được Attack ngay cả trên dữ liệu sạch.

Khi đánh giá trên sáu tập dữ liệu Padding, cả ba mô hình đều suy giảm nghiêm trọng. Recall Attack của Random Forest giảm từ 65,85% xuống khoảng 0,008%; XGBoost giảm từ 1,09% xuống khoảng 0,008%; còn LightGBM không phát hiện được Attack trong các tập biến đổi. ASR đều đạt 100%, nhưng cần đặt trong bối cảnh số flow đủ điều kiện tính ASR của từng mô hình, đặc biệt LightGBM chỉ có 2 flow.

Phân tích perturbation cho thấy toàn bộ flow đều có thay đổi và trung bình 79 feature bị thay đổi trên mỗi flow. Các giá trị L2 và L∞ rất lớn, do đó cần xác minh lại thang đo và quy trình tiền xử lý trước khi đưa ra kết luận về cường độ biến đổi. Các tập dữ liệu được xác nhận alignment và có Validity Ratio bằng 100% theo cờ validation hiện có, nhưng điều này chưa đủ để khẳng định tính hợp lệ hoàn toàn trong môi trường mạng thực tế.

**Nhìn chung, thí nghiệm cho thấy ba mô hình đang được đánh giá có độ bền vững thấp trước các tập Padding hiện tại.** Tuy nhiên, trước khi khẳng định Padding là nguyên nhân duy nhất gây suy giảm, cần xác minh quy trình tạo dữ liệu, scaler, danh sách feature và ý nghĩa của các norm. Sau khi hoàn tất các kiểm tra này, kết quả sẽ có cơ sở vững chắc hơn để sử dụng trong báo cáo nghiên cứu về Adversarial Robustness của NIDS.

---

## 10. Đoạn nhận xét ngắn có thể đưa vào báo cáo

Thực nghiệm đánh giá ba mô hình LightGBM, Random Forest và XGBoost trên tập dữ liệu sạch và sáu tập dữ liệu được biến đổi bằng Padding. Kết quả trên dữ liệu sạch cho thấy Random Forest có khả năng phát hiện Attack tốt nhất với Recall đạt 65,85% và F1 đạt 0,79412. Mặc dù XGBoost có ROC-AUC và PR-AUC cao nhất, Recall Attack tại ngưỡng phân loại hiện tại chỉ đạt 1,09%. Khi chuyển sang các tập dữ liệu Padding, hiệu năng của cả ba mô hình suy giảm nghiêm trọng. Đáng chú ý, Recall của Random Forest giảm từ 65,85% xuống khoảng 0,008%, trong khi XGBoost giảm từ 1,09% xuống khoảng 0,008%. ASR đạt 100% trên cả sáu tập biến đổi, cho thấy các flow Attack được phát hiện đúng trên dữ liệu sạch đều bị phân loại thành Benign sau Padding trong phạm vi mẫu đủ điều kiện của từng mô hình. Tuy nhiên, cần lưu ý số mẫu dùng để tính ASR khác nhau đáng kể giữa các mô hình. Kết quả bước đầu cho thấy các mô hình chưa duy trì được khả năng phát hiện xâm nhập trước những biến đổi Padding đang xét. Cần kiểm tra thêm quy trình scale, mức thay đổi của từng feature và tính hợp lệ thực tế của dữ liệu để củng cố kết luận về độ bền vững đối kháng.
