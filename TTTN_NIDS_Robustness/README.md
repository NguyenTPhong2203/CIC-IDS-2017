# NIDS Robustness

Demo Streamlit cho thực nghiệm NIDS theo phương pháp chia dữ liệu theo ngày
(nhánh A). Ứng dụng sử dụng các model bundle đã lưu, scaler được fit trên tập
train, cùng logic Padding và Validator từ notebook. Ứng dụng không huấn luyện
lại model và không tạo số liệu giả.

Giao diện được tổ chức theo luồng trình diễn: **Tổng quan → Phát hiện xâm
nhập → Áp dụng biến đổi dữ liệu → Đánh giá độ bền vững của mô hình**. Thiết kế
dark cybersecurity/SOC làm nổi bật mục tiêu thí nghiệm, trạng thái Validator và
so sánh clean/perturbed. Nội dung dùng tiếng Việt, giữ các thuật ngữ ML/NIDS
phổ biến như Benign, Attack, Recall, F1 và FPR.

Trong các luồng dự đoán, có thể chọn threshold `fpr0.1%`, `fpr1%` hoặc `0.5`.
`fpr0.1%` là mặc định theo mục tiêu thí nghiệm và ưu tiên giảm False Positive,
vì vậy có thể bỏ sót nhiều Attack. Chọn `fpr1%` khi cần một kịch bản demo bắt
được nhiều Attack hơn; lựa chọn threshold được áp dụng nhất quán cho Detection,
Padding batch và Robustness evaluation.

## Cấu trúc dự án

```text
web_demo/
├── app.py                  # Entrypoint Streamlit
├── src/                    # Data, model, evaluation, padding và validator
├── data/                   # Dataset demo và scaler
├── artifacts/models/       # Model bundles đã huấn luyện
├── notebooks/              # Notebook nghiên cứu và đánh giá
├── requirements.txt        # Dependency ghim phiên bản
└── README.md
```

`.venv/`, cache Python và checkpoint của Jupyter là file cục bộ, đã được đưa
vào `.gitignore` và không thuộc source cần chia sẻ.

Trong **Phát hiện xâm nhập**, có thể tải file CSV hoặc Parquet nhỏ (tối đa
10 MB và 10.000 dòng) nếu có đủ 82 feature theo đúng tên. File tải lên được
coi là dữ liệu chưa scale; app sẽ dùng scaler trong model bundle trước khi
dự đoán. Detection hỗ trợ dự đoán một flow, một lô tùy chọn số dòng hoặc toàn
bộ dữ liệu; kết quả lô hiển thị preview và cho tải xuống toàn bộ CSV. Trong
**Áp dụng biến đổi dữ liệu**, Padding mặc định chỉ chạy trên flow Attack; có
thể áp dụng cho một dòng hoặc một lô tối đa 200 flow Attack để demo phản hồi
nhanh. Kết quả được lưu trong
phiên làm việc để trang **Đánh giá độ bền vững của mô hình** sử dụng trực tiếp,
không cần chọn lại cấu hình.

## Chạy ứng dụng

```powershell
# Tạo môi trường ảo (chỉ cần chạy một lần):
python -m venv .venv

# Kích hoạt môi trường ảo trên Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Cập nhật pip và cài dependencies trong môi trường ảo:
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Kiểm tra Python đang chạy từ môi trường ảo:
python -c "import sys; print(sys.executable)"

# Khởi động Streamlit:
streamlit run app.py
```

## Chạy bằng Docker

Yêu cầu Docker Desktop đang hoạt động. Từ thư mục gốc của project:

```powershell
# Build image:
docker build -t dgt-nids:latest .

# Chạy container:
docker run --rm -p 8501:8501 dgt-nids:latest
```

Mở [http://localhost:8501](http://localhost:8501). Image chứa `src/`, dataset
demo, scaler và model bundles trong `artifacts/models/`; notebook và môi trường
ảo local không được đưa vào image.

Nếu PowerShell chặn script kích hoạt, chạy một lần trong PowerShell hiện tại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Sau khi kích hoạt `.venv`, mọi lệnh `python`, `pip` và `streamlit` trong tài liệu
này đều phải được chạy trong cùng cửa sổ PowerShell. Có thể kiểm tra nhanh bằng
`python -c "import streamlit; print(streamlit.__version__)"`.

Mặc định giao diện xử lý tối đa 5.000 dòng để demo phản hồi nhanh. Đặt giới
hạn bằng `0` nếu muốn xử lý toàn bộ tập test nhánh A; giao diện sẽ hiển thị
chính xác số dòng thực tế được sử dụng.

## Hợp đồng dữ liệu

- `data/100_Thursday_scaled.parquet`: bản scaled của bộ demo 100 dòng.
- `data/100_Thursday_non_scale.parquet`: nguồn mặc định để thực hiện biến đổi
  Padding; gồm 50 dòng Benign và 50 dòng Attack.
- Các file `.csv` tương ứng là fallback cho đúng bộ `100_Thursday_*` khi cần.
- `data/scaler_day_based_82.joblib`: scaler được fit trên tập train và được nạp
  trực tiếp khi khởi tạo mọi model bundle để scale dữ liệu sạch và dữ liệu sau
  Padding.
- Các model bundle trong `artifacts/models/` cần runtime `xgboost` và
  `lightgbm` để tải đủ cả ba model.
- Cần có đủ ba file model bundle trong `artifacts/models/` trước khi chạy các
  luồng dự đoán và đánh giá robustness.
- `Benign = 0`, `Attack = 1`.

Padding là biến đổi ở cấp feature/flow, không phải phát lại packet thực tế.
Validator hợp lệ chỉ có nghĩa là mẫu vượt qua các rule đã được triển khai,
không đồng nghĩa với việc mô hình dự đoán đúng hoặc dữ liệu chắc chắn hợp lệ
về mặt mạng thực tế.

Nhãn dự đoán trong giao diện dùng ngưỡng `fpr0.1%` đã lưu trong từng model
bundle, thay vì ngưỡng mặc định 0,5 của `estimator.predict()`. Các ngưỡng này
được chọn trên validation để giữ FPR ở mức mục tiêu của thí nghiệm.

## Kiểm thử

```powershell
python -m pytest -q
```

Các test bao phủ công thức Padding tương đương notebook, Random Padding có
thể tái lập, phát hiện vi phạm Validator, tính metric và lấy mẫu đúng schema.

## Lưu ý về tương thích phiên bản

Metadata của model bundle ghi nhận scikit-learn 1.8.0, vì vậy
`requirements.txt` ghim phiên bản này để tương thích với estimator. File
`scaler_day_based_82.joblib` được tạo bằng phiên bản scikit-learn cũ hơn nên
có thể vẫn xuất hiện cảnh báo tương thích; scaler được load nguyên trạng và
không được fit lại.
