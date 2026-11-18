from __future__ import annotations

import zlib

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_service import FEATURES, load_test_data, select_sample
from src.evaluation import metrics, metrics_table
from src.model_service import DEFAULT_THRESHOLD_KEY, MODEL_FILES, load_model, predict
from src.perturbation import PAD_LEVELS, PAD_MODES, SEED, apply_padding
from src.validator import RULE_VI, validate, violation_report


MODEL_LABELS = {
    "Random Forest": "Random Forest",
    "XGBoost": "XGBoost",
    "LightGBM": "LightGBM",
}
THRESHOLD_OPTIONS = {
    "fpr0.1%": "FPR mục tiêu 0,1% (thận trọng)",
    "fpr1%": "FPR mục tiêu 1% (bắt được nhiều Attack hơn)",
    "0.5": "Ngưỡng mặc định 0,5",
}
MODE_LABELS = {"static": "Padding tĩnh", "random": "Padding ngẫu nhiên"}
RULE_LABELS = {
    "non_finite_new": "Phát sinh NaN/Inf mới",
    "negative_value_new": "Phát sinh giá trị âm mới",
    "modifiable_decreased": "Feature được sửa bị giảm",
    "immutable_changed": "Feature bất biến bị thay đổi",
    "min_mean_max_new": "Vi phạm Min ≤ Mean ≤ Max",
}
CHANGED_COLUMNS = [
    "Fwd Packets Length Total",
    "Fwd Packet Length Mean",
    "Packet Length Mean",
    "Avg Packet Size",
    "Avg Fwd Segment Size",
    "Flow Bytes/s",
]
LIMITATION_NOTE = (
    "Lưu ý: Do đặc thù mất cân bằng dữ liệu NIDS, mô hình đang tiếp tục được "
    "tối ưu hóa khả năng phát hiện các cuộc tấn công hiếm gặp."
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --dgt-bg: #07111f;
            --dgt-panel: #0d1b2d;
            --dgt-panel-2: #11253b;
            --dgt-border: rgba(148, 163, 184, .18);
            --dgt-text: #e6edf7;
            --dgt-muted: #8ea4bd;
            --dgt-cyan: #35d7e8;
            --dgt-green: #59d499;
            --dgt-amber: #f7bd61;
            --dgt-red: #ff7b88;
        }
        .stApp {
            background:
                radial-gradient(circle at 85% 0%, rgba(35, 155, 190, .12), transparent 30rem),
                linear-gradient(135deg, #07111f 0%, #091625 55%, #07111f 100%);
            color: var(--dgt-text);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #081522 0%, #0b1a2b 100%);
            border-right: 1px solid var(--dgt-border);
        }
        [data-testid="stSidebar"] .stRadio label { color: var(--dgt-muted); }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
            gap: .35rem;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
            padding: .65rem .75rem;
            border: 1px solid transparent;
            border-radius: .65rem;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
            background: rgba(53, 215, 232, .08);
            border-color: rgba(53, 215, 232, .25);
        }
        h1, h2, h3 { letter-spacing: -.025em; }
        h1 { font-weight: 750; }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(17, 37, 59, .92), rgba(13, 27, 45, .92));
            border: 1px solid var(--dgt-border);
            border-radius: .85rem;
            padding: .8rem 1rem;
        }
        [data-testid="stMetricLabel"] { color: var(--dgt-muted); }
        [data-testid="stMetricValue"] { color: var(--dgt-text); }
        .dgt-kicker {
            color: var(--dgt-cyan);
            font-size: .73rem;
            font-weight: 700;
            letter-spacing: .13em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }
        .dgt-subtitle { color: var(--dgt-muted); font-size: 1rem; }
        .dgt-card {
            background: linear-gradient(145deg, rgba(17, 37, 59, .9), rgba(9, 24, 40, .9));
            border: 1px solid var(--dgt-border);
            border-radius: .9rem;
            padding: 1rem 1.1rem;
            min-height: 8rem;
            display: flex;
            flex-direction: column;
        }
        .dgt-card h4 { margin: 0 0 .45rem; color: var(--dgt-text); }
        .dgt-card p { margin: 0; color: var(--dgt-muted); line-height: 1.5; flex: 1; }
        .dgt-pill {
            display: inline-block;
            padding: .25rem .55rem;
            margin: .15rem .25rem .15rem 0;
            border: 1px solid rgba(53, 215, 232, .32);
            border-radius: 999px;
            color: #a9f3f8;
            background: rgba(53, 215, 232, .08);
            font-size: .78rem;
        }
        .dgt-pill.green {
            color: #b6f4d5;
            border-color: rgba(89, 212, 153, .3);
            background: rgba(89, 212, 153, .08);
        }
        .dgt-pill.amber {
            color: #ffe0a6;
            border-color: rgba(247, 189, 97, .3);
            background: rgba(247, 189, 97, .08);
        }
        .dgt-note {
            border-left: 3px solid var(--dgt-amber);
            background: rgba(247, 189, 97, .08);
            padding: .75rem .9rem;
            border-radius: 0 .6rem .6rem 0;
            color: #d8e2ef;
        }
        .overview-note { margin-top: 1.5rem; }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ui_pills(items: list[tuple[str, str]], container=st) -> None:
    html = "".join(f'<span class="dgt-pill {tone}">{label}</span>' for label, tone in items)
    container.markdown(html, unsafe_allow_html=True)


st.set_page_config(
    page_title="DGT NIDS Robustness - Đánh giá độ bền vững của hệ thống phát hiện xâm nhập",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def cached_data(scaled: bool) -> pd.DataFrame:
    return load_test_data(scaled)


@st.cache_resource(show_spinner=False)
def cached_model(name: str) -> dict:
    return load_model(name)


def mode_label(mode: str) -> str:
    return MODE_LABELS[mode]


def scenario_label(mode: str, level: int) -> str:
    return f"{mode_label(mode)} {level} B"


def metric_value(value: float | int, percent: bool = False) -> str:
    if percent:
        return f"{float(value) * 100:.2f}%"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    return f"{float(value):.4f}"


def csv_download(df: pd.DataFrame, filename: str) -> None:
    st.download_button(
        "⬇️ Tải CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        filename,
        "text/csv",
    )


def validate_input_frame(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    required = set(FEATURES)
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(
            f"{source_name} thiếu {len(missing)} feature bắt buộc. "
            f"Ví dụ: {', '.join(missing[:5])}"
        )
    if len(df) == 0:
        raise ValueError(f"{source_name} không có dòng dữ liệu.")
    if len(df) > 10_000:
        raise ValueError("File CSV tối đa 10.000 dòng cho luồng demo.")
    result = df.reset_index(drop=True).copy()
    result[FEATURES] = result[FEATURES].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(result[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("CSV có feature không phải số, NaN hoặc Inf.")
    if "Label_binary" in result:
        result["Label_binary"] = pd.to_numeric(
            result["Label_binary"], errors="coerce"
        )
    if "Label" not in result:
        result["Label"] = "Chưa có nhãn"
    return result


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.size > 10 * 1024 * 1024:
        raise ValueError("File CSV/Parquet tối đa 10 MB cho luồng demo.")
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        frame = pd.read_csv(uploaded_file)
    elif filename.endswith(".parquet"):
        frame = pd.read_parquet(uploaded_file)
    else:
        raise ValueError("Chỉ hỗ trợ file .csv hoặc .parquet.")
    return validate_input_frame(
        frame,
        f"File tải lên ({uploaded_file.name})",
    )


def prepare_model_input(
    df: pd.DataFrame, artifact: dict, already_scaled: bool = False
) -> pd.DataFrame:
    result = df.copy()
    scaler = artifact.get("scaler")
    if scaler is not None and not already_scaled:
        result[artifact["features"]] = scaler.transform(result[artifact["features"]])
    return result


def predict_probabilities(
    df: pd.DataFrame, threshold_key: str = DEFAULT_THRESHOLD_KEY
) -> pd.DataFrame:
    rows = []
    for model_name in MODEL_FILES:
        artifact = cached_model(model_name)
        model_input = prepare_model_input(df, artifact)
        labels, scores = predict(model_input, artifact, threshold_key)
        score = float(scores[0]) if scores is not None else float(labels[0])
        rows.append(
            {
                "Model": MODEL_LABELS[model_name],
                "Nhãn": "Bị tấn công" if int(labels[0]) == 1 else "Bình thường",
                "Xác suất Attack": score,
                "Độ tin cậy": max(score, 1 - score),
            }
        )
    return pd.DataFrame(rows)


def show_metrics(result: dict) -> None:
    items = [
        ("Số dòng", metric_value(result["n_rows"])),
        ("Attack", metric_value(result["n_attack"])),
        ("Precision Attack", metric_value(result["precision_attack"], True)),
        ("Recall Attack", metric_value(result["recall_attack"], True)),
        ("F1 Attack", metric_value(result["f1_attack"], True)),
        ("FPR", metric_value(result["fpr"], True)),
    ]
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


def metrics_frame(result: dict) -> pd.DataFrame:
    labels = {
        "n_rows": "Số dòng",
        "n_attack": "Số Attack",
        "accuracy": "Accuracy",
        "balanced_accuracy": "Balanced Accuracy",
        "precision_attack": "Precision Attack",
        "recall_attack": "Recall Attack",
        "f1_attack": "F1 Attack",
        "fpr": "FPR",
        "specificity": "Specificity",
        "roc_auc": "ROC-AUC",
        "pr_auc": "PR-AUC",
        "tn": "True Negative",
        "fp": "False Positive",
        "fn": "False Negative",
        "tp": "True Positive",
    }
    rows = []
    for key, label in labels.items():
        if key not in result:
            continue
        is_percent = key in {
            "accuracy",
            "balanced_accuracy",
            "precision_attack",
            "recall_attack",
            "f1_attack",
            "fpr",
            "specificity",
        }
        rows.append({"Chỉ số": label, "Giá trị": metric_value(result[key], is_percent)})
    return pd.DataFrame(rows)


def page_header(title: str, description: str) -> None:
    st.markdown('<div class="dgt-kicker">DGT NIDS / ĐÁNH GIÁ ĐỘ BỀN VỮNG</div>', unsafe_allow_html=True)
    st.title(title)
    if description:
        st.markdown(f'<div class="dgt-subtitle">{description}</div>', unsafe_allow_html=True)


def show_terms() -> None:
    with st.expander("Giải thích thuật ngữ"):
        st.markdown(
            "- **Benign (0):** lưu lượng bình thường.\n"
            "- **Attack (1):** lưu lượng bị gắn nhãn tấn công.\n"
            "- **Padding:** tăng feature ở cấp flow, không phải phát lại packet.\n"
            "- **Validator:** kiểm tra các ràng buộc đã được triển khai.\n"
            "- **DR/Recall:** tỷ lệ flow Attack được phát hiện.\n"
            "- **Accuracy:** tỷ lệ dự đoán đúng trên toàn bộ flow.\n"
            "- **Balanced Accuracy:** trung bình Recall của Benign và Attack.\n"
            "- **Specificity:** tỷ lệ Benign được nhận diện đúng.\n"
            "- **FPR:** tỷ lệ flow Benign bị cảnh báo nhầm.\n"
            "- **ROC-AUC/PR-AUC:** chất lượng xếp hạng xác suất của model."
        )


def run_perturbation(
    df: pd.DataFrame,
    level: int,
    mode: str,
    tag: str,
    seed: int = SEED,
):
    attacks = df["Label_binary"].to_numpy(int) == 1
    positions = np.flatnonzero(attacks)
    attack_df = df.iloc[positions].reset_index(drop=True)
    rng = np.random.default_rng(seed + zlib.crc32(tag.encode()))
    perturbed, applicable, added = apply_padding(attack_df, level, mode, rng)
    violations = validate(attack_df[FEATURES], perturbed[FEATURES])
    failed = violations.any(axis=1).to_numpy()
    applied = applicable & ~failed
    output = df.copy().reset_index(drop=True)
    for col in perturbed.columns:
        values = output[col].to_numpy(copy=True)
        values[positions[applied]] = perturbed[col].to_numpy()[applied]
        output[col] = values
    output["__padding_applicable"] = False
    output["__padding_applied"] = False
    output["__validation_failed"] = False
    output["__fwd_bytes_added"] = 0.0
    output.loc[positions, "__padding_applicable"] = applicable
    output.loc[positions, "__padding_applied"] = applied
    output.loc[positions, "__validation_failed"] = failed
    output.loc[positions, "__fwd_bytes_added"] = np.where(applied, added, 0.0)
    return output, violation_report(violations), violations


def run_single_padding(
    row: pd.DataFrame,
    level: int,
    mode: str,
    seed: int,
):
    if int(row["Label_binary"].iloc[0]) != 1:
        return row.copy(), row.copy(), "Padding chỉ áp cho flow tấn công", 0.0, None
    rng = np.random.default_rng(seed)
    perturbed, applicable, added = apply_padding(row[FEATURES], level, mode, rng)
    violations = validate(row[FEATURES], perturbed[FEATURES])
    if not bool(applicable[0]):
        if float(row["Fwd Act Data Packets"].iloc[0]) < 1:
            status = "không áp dụng được (không có Fwd Act Data Packets)"
        else:
            status = "không áp dụng được (không đủ biên Min/Max)"
        return row.copy(), row.copy(), status, 0.0, violations
    if bool(violations.any(axis=1).iloc[0]):
        return row.copy(), row.copy(), "vi phạm validator → hoàn nguyên", 0.0, violations
    result = row.copy()
    result[FEATURES] = result[FEATURES].astype(float)
    result.loc[:, FEATURES] = perturbed[FEATURES].to_numpy()
    return row.copy(), result, "áp dụng được", float(added[0]), violations


def validator_table(report: pd.DataFrame) -> pd.DataFrame:
    return report.assign(
        Rule=report["rule"].map(RULE_LABELS).fillna(report["rule"]),
        Mô_tả=report["rule"].map(RULE_VI).fillna(""),
    )[["Rule", "Mô_tả", "n_violations", "pct_of_rows"]].rename(
        columns={"n_violations": "Số vi phạm", "pct_of_rows": "Tỷ lệ (%)"}
    )


def show_validator_table(report: pd.DataFrame) -> None:
    table = validator_table(report)
    styled = table.style.apply(
        lambda row: [
            "background-color: #dcfce7; color: #166534;"
            if column == "Số vi phạm" and row[column] == 0
            else ""
            for column in table.columns
        ],
        axis=1,
    )
    st.dataframe(styled, hide_index=True, use_container_width=True)


def sidebar() -> str:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { width: 285px !important; }
        section[data-testid="stSidebar"] > div { padding-top: 1rem; }
        [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("## 🛡️ DGT NIDS ROBUSTNESS")
    page = st.sidebar.radio(
        "Mục lục",
        [
            "⌂  Tổng quan",
            "Phát hiện xâm nhập",
            "Áp dụng biến đổi dữ liệu",
            "Đánh giá độ bền vững của mô hình",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")
    ui_pills(
        [("3 mô hình", "green"), ("82 đặc trưng", ""), ("Chia theo ngày", "amber")],
        st.sidebar,
    )
    st.sidebar.caption("Padding là biến đổi ở cấp đặc trưng, không phải phát lại PCAP.")
    return page


def overview() -> None:
    page_header(
        "DGT NIDS Robustness - Đánh giá độ bền vững của hệ thống phát hiện xâm nhập",
        "",
    )
    st.markdown(
        '<div class="dgt-note">Mục tiêu demo: quan sát một luồng tấn công đi qua '
        'bộ phát hiện, kiểm tra tác động của Padding và đo sự thay đổi về độ bền vững. '
        'Kết quả chỉ áp dụng cho biến đổi ở cấp đặc trưng và dữ liệu được chia theo ngày.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Các tính năng chính")
    cols = st.columns(3)
    cards = [
        ("01 · Phát hiện xâm nhập", "Dự đoán luồng dữ liệu sạch bằng Random Forest, XGBoost và LightGBM."),
        ("02 · Biến đổi dữ liệu", "Áp dụng Padding có kiểm soát và kiểm tra tính hợp lệ bằng Validator."),
        ("03 · Đánh giá độ bền vững", "So sánh dữ liệu sạch và sau Padding qua Recall, F1 và FPR."),
    ]
    for col, (title, body) in zip(cols, cards):
        col.markdown(f'<div class="dgt-card"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dgt-note overview-note">{LIMITATION_NOTE}</div>',
        unsafe_allow_html=True,
    )


def batch_prediction_view(
    source: pd.DataFrame,
    threshold_key: str,
    scope: str,
    batch_size: int,
) -> None:
    selected = source if scope == "Toàn bộ dữ liệu" else source.head(batch_size)
    rows = []
    for model_name in MODEL_FILES:
        artifact = cached_model(model_name)
        labels, scores = predict(
            prepare_model_input(selected, artifact),
            artifact,
            threshold_key,
        )
        for position, (index, label) in enumerate(zip(selected.index, labels)):
            score = float(scores[position]) if scores is not None else float(label)
            item = {
                "Dòng": int(index),
                "Model": MODEL_LABELS[model_name],
                "Dự đoán": "Bị tấn công" if int(label) == 1 else "Bình thường",
                "Xác suất Attack": score,
                "Độ tin cậy": max(score, 1 - score),
            }
            if "Label" in selected:
                item["Nhãn thật"] = selected.loc[index, "Label"]
            rows.append(item)
    result = pd.DataFrame(rows)
    summary = (
        result.assign(Attack=result["Dự đoán"].eq("Bị tấn công"))
        .groupby("Model", as_index=False)
        .agg(
            **{
                "Số dòng": ("Dòng", "count"),
                "Số Attack": ("Attack", "sum"),
                "Tỷ lệ Attack": ("Attack", "mean"),
                "Xác suất Attack TB": ("Xác suất Attack", "mean"),
            }
        )
    )
    summary["Tỷ lệ Attack"] = summary["Tỷ lệ Attack"].map(lambda value: metric_value(value, True))
    summary["Xác suất Attack TB"] = summary["Xác suất Attack TB"].map(
        lambda value: metric_value(value, True)
    )
    st.success(f"Đã dự đoán {len(selected):,} dòng trên cả ba mô hình.")
    metric_cols = st.columns(3)
    metric_cols[0].metric("Số dòng xử lý", f"{len(selected):,}")
    metric_cols[1].metric("Số model", "3")
    metric_cols[2].metric("Threshold", threshold_key)
    st.subheader("Tổng hợp theo model")
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.subheader("Preview kết quả")
    st.caption("Hiển thị tối đa 300 dòng đầu; file tải xuống chứa toàn bộ kết quả.")
    st.dataframe(result.head(300), hide_index=True, use_container_width=True)
    scope_slug = "batch" if scope == "Theo lô" else "all"
    csv_download(result, f"branch_a_{scope_slug}_prediction.csv")


def intrusion_detection() -> None:
    page_header(
        "Phát hiện xâm nhập",
        "Dự đoán dữ liệu sạch",
    )
    threshold_key = st.selectbox(
        "Ngưỡng quyết định Attack",
        list(THRESHOLD_OPTIONS),
        index=list(THRESHOLD_OPTIONS).index(DEFAULT_THRESHOLD_KEY),
        format_func=lambda key: THRESHOLD_OPTIONS[key],
        key="detection_threshold",
        help="FPR thấp giúp giảm cảnh báo nhầm nhưng có thể bỏ sót nhiều Attack.",
    )
    st.caption(f"Đang dùng threshold `{threshold_key}` được lưu riêng cho từng model.")
    uploaded = st.file_uploader(
        "Tải CSV hoặc Parquet nhỏ (không bắt buộc)",
        type=["csv", "parquet"],
        help="File cần có đủ 82 feature theo đúng tên; có thể có thêm Label/Label_binary.",
    )
    try:
        if uploaded is not None:
            source = load_uploaded_file(uploaded)
            source_name = f"{uploaded.name} tải lên"
        else:
            source = cached_data(False)
            source_name = "Bộ 100_Thursday (50 Benign + 50 Attack)"
            st.info(
                "Chưa có file CSV tải lên. Hệ thống mặc định thử nghiệm trên "
                "bộ 100_Thursday gồm 50 dòng Benign và 50 dòng Attack."
            )
        st.caption(f"Nguồn dữ liệu hiện tại: {source_name}.")
        prediction_scope = st.radio(
            "Phạm vi dự đoán",
            ["Một flow", "Theo lô", "Toàn bộ dữ liệu"],
            horizontal=True,
            key="detection_scope",
        )
        row_number = 0
        batch_size = len(source)
        if prediction_scope == "Một flow":
            row_number = st.number_input(
                "Chọn dòng dữ liệu",
                min_value=0,
                max_value=max(0, len(source) - 1),
                value=0,
                step=1,
            )
            input_frame = source.iloc[[int(row_number)]].copy()
            action_label = "flow"
        elif prediction_scope == "Theo lô":
            batch_size = st.number_input(
                "Số dòng trong lô",
                min_value=1,
                max_value=len(source),
                value=min(200, len(source)),
                step=1,
            )
            input_frame = source.head(int(batch_size)).copy()
            action_label = f"{int(batch_size):,} dòng"
        else:
            input_frame = source
            action_label = f"{len(source):,} dòng"
        if not st.button("▶ Chạy dự đoán sạch", type="primary"):
            st.info(f"Chọn phạm vi ({action_label}) rồi bấm “Chạy dự đoán sạch”.")
            return
        if prediction_scope != "Một flow":
            batch_prediction_view(source, threshold_key, prediction_scope, int(batch_size))
            return
        row = input_frame
        model_results = []
        for model_name in MODEL_FILES:
            artifact = cached_model(model_name)
            model_input = prepare_model_input(row, artifact)
            labels, scores = predict(model_input, artifact, threshold_key)
            score = float(scores[0]) if scores is not None else float(labels[0])
            prediction = "Bị tấn công" if int(labels[0]) == 1 else "Bình thường"
            model_results.append(
                {
                    "Model": MODEL_LABELS[model_name],
                    "Dự đoán": prediction,
                    "Xác suất Attack": score,
                    "Độ tin cậy": max(score, 1 - score),
                }
            )
        st.success("Đã chạy dự đoán trên cả ba mô hình.")
        attack_votes = sum(item["Dự đoán"] == "Bị tấn công" for item in model_results)
        mean_score = float(np.mean([item["Xác suất Attack"] for item in model_results]))
        metric_cols = st.columns(3)
        metric_cols[0].metric("Model đồng thuận Attack", f"{attack_votes}/3")
        metric_cols[1].metric("Xác suất Attack TB", metric_value(mean_score, True))
        metric_cols[2].metric("Threshold", threshold_key)
        ui_pills([
            ("CLEAN FLOW", "green"),
            ("3 MODEL ENSEMBLE", ""),
            (f"ROW {int(row_number)}", "amber"),
        ])
        st.subheader("Thông số gốc của flow")
        st.dataframe(
            row[FEATURES].T.rename(columns={row.index[0]: "Giá trị"}),
            use_container_width=True,
        )
        st.subheader("Kết quả phân loại ban đầu")
        result = pd.DataFrame(model_results)
        st.dataframe(result, hide_index=True, use_container_width=True)
        if "Label_binary" in row and pd.notna(row["Label_binary"].iloc[0]):
            st.warning(
                "Metric không được hiển thị trên một flow đơn lẻ vì không đủ mẫu "
                "để đánh giá có ý nghĩa thống kê."
            )
        else:
            st.caption("CSV không có Label_binary nên chỉ hiển thị dự đoán và độ tin cậy.")
        csv_download(result, "branch_a_clean_prediction.csv")
    except Exception as exc:
        st.error(f"Không thể đọc hoặc dự đoán dữ liệu: {exc}")


def show_probability_comparison(before: pd.DataFrame, after: pd.DataFrame) -> None:
    threshold_key = st.session_state.get("padding_threshold", DEFAULT_THRESHOLD_KEY)
    before_prob = predict_probabilities(before, threshold_key).set_index("Model")
    after_prob = predict_probabilities(after, threshold_key).set_index("Model")
    comparison = before_prob[["Nhãn", "Xác suất Attack"]].rename(
        columns={"Nhãn": "Nhãn trước", "Xác suất Attack": "Xác suất trước"}
    ).join(
        after_prob[["Nhãn", "Xác suất Attack"]].rename(
            columns={"Nhãn": "Nhãn sau", "Xác suất Attack": "Xác suất sau"}
        )
    )
    comparison["Delta"] = comparison["Xác suất sau"] - comparison["Xác suất trước"]
    comparison["Thay đổi nhãn"] = np.where(
        (comparison["Nhãn trước"] == "Bị tấn công")
        & (comparison["Nhãn sau"] == "Bình thường"),
        "⚠️ đổi nhãn Attack → Benign",
        "",
    )
    st.dataframe(comparison.reset_index(), hide_index=True, use_container_width=True)


def single_perturbation_view(
    sample: pd.DataFrame,
    level: int,
    mode: str,
    seed: int,
) -> None:
    attack_row = sample.iloc[[0]].copy()
    before, after, status, added, violations = run_single_padding(
        attack_row, level, mode, seed
    )
    st.session_state["padding_clean"] = before.copy()
    st.session_state["padding_result"] = after.copy()
    st.session_state["padding_config"] = {
        "mode": mode,
        "level": level,
        "seed": seed,
        "scope": "Một flow",
    }
    if status == "Padding chỉ áp cho flow tấn công":
        st.info(status)
        return
    st.info(f"Trạng thái: **{status}** | Số byte cộng thêm: **{added:.0f} B**")
    if violations is not None and violations.any(axis=1).iloc[0]:
        st.warning("Dữ liệu vi phạm Validator nên đã được hoàn nguyên về giá trị ban đầu.")
    before_values = attack_row[CHANGED_COLUMNS].iloc[0]
    after_values = after[CHANGED_COLUMNS].iloc[0]
    comparison = pd.DataFrame(
        {
            "Feature": CHANGED_COLUMNS,
            "Trước": before_values.to_numpy(float),
            "Sau": after_values.to_numpy(float),
        }
    )
    comparison["% thay đổi"] = np.where(
        comparison["Trước"] != 0,
        (comparison["Sau"] - comparison["Trước"]) / comparison["Trước"] * 100,
        0.0,
    )
    st.subheader("So sánh trước / sau")
    st.dataframe(comparison, hide_index=True, use_container_width=True)
    st.caption(
        "Fwd Packet Length Min/Max/Std, Packet Length Min/Max/Std/Variance, "
        "Subflow và Bulk được giữ nguyên vì không thể tái tạo chính xác từ flow."
    )
    with st.expander("Chi tiết vi phạm ràng buộc theo luật"):
        if violations is None:
            st.info("Không có dữ liệu vi phạm để hiển thị.")
        else:
            report = violation_report(violations)
            show_validator_table(report)


def batch_perturbation_view(
    sample: pd.DataFrame,
    level: int,
    mode: str,
    seed: int,
    threshold_key: str,
) -> None:
    sample = sample.reset_index(drop=True)
    st.caption(
        "Chế độ lô mặc định xử lý tối đa 200 flow Attack để demo phản hồi nhanh."
    )
    output, report, _ = run_perturbation(
        sample,
        level,
        mode,
        f"batch_{mode}_{level}B",
        seed,
    )
    st.session_state["padding_clean"] = sample.copy()
    st.session_state["padding_result"] = output.copy()
    st.session_state["padding_config"] = {
        "mode": mode,
        "level": level,
        "seed": seed,
        "scope": "Lô trên mẫu",
    }
    valid = ~output["__validation_failed"]
    rows = []
    for model_name in MODEL_FILES:
        artifact = cached_model(model_name)
        clean_input = prepare_model_input(sample.loc[valid], artifact)
        pert_input = prepare_model_input(output.loc[valid], artifact)
        clean_pred, _ = predict(clean_input, artifact, threshold_key)
        pert_pred, _ = predict(pert_input, artifact, threshold_key)
        attacks = sample.loc[valid, "Label_binary"].to_numpy(int) == 1
        rows.append(
            {
                "Model": MODEL_LABELS[model_name],
                "DR trước": float(clean_pred[attacks].mean()) if attacks.any() else 0.0,
                "DR sau": float(pert_pred[attacks].mean()) if attacks.any() else 0.0,
                "Delta DR": float(pert_pred[attacks].mean() - clean_pred[attacks].mean()) if attacks.any() else 0.0,
                "Số flow flip": int(((clean_pred == 1) & (pert_pred == 0)).sum()),
            }
        )
    st.dataframe(
        pd.DataFrame(rows).assign(
            **{
                "DR trước": lambda frame: frame["DR trước"].map(lambda value: metric_value(value, True)),
                "DR sau": lambda frame: frame["DR sau"].map(lambda value: metric_value(value, True)),
                "Delta DR": lambda frame: frame["Delta DR"].map(lambda value: metric_value(value, True)),
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    cols = st.columns(3)
    cols[0].metric("Flow mẫu", f"{len(sample):,}")
    cols[1].metric("Flow áp dụng", f"{int(output['__padding_applied'].sum()):,}")
    cols[2].metric("Flow bị Validator từ chối", f"{int(output['__validation_failed'].sum()):,}")
    with st.expander("Chi tiết vi phạm ràng buộc theo luật"):
        show_validator_table(report)


def perturbation_lab() -> None:
    page_header(
        "Áp dụng biến đổi dữ liệu",
        "Thực hiện Padding cho một dòng dữ liệu tấn công hoặc một lô.",
    )
    ui_pills([("ATTACK FLOWS ONLY", "green"), ("VALIDATOR ON", ""), ("REPRODUCIBLE SEED", "amber")])
    st.markdown("### Experiment controls")
    sample = select_sample(cached_data(False), 5000)
    candidates = sample[sample["Label_binary"] == 1]
    if candidates.empty:
        st.warning("Không có flow Attack phù hợp trong mẫu hiện tại.")
        return
    flow_position = st.number_input(
        f"Chọn flow (0 - {len(candidates) - 1})",
        min_value=0,
        max_value=max(0, len(candidates) - 1),
        value=0,
        step=1,
    )
    mode = st.selectbox("Mode", PAD_MODES, format_func=mode_label, key="single_mode")
    level = st.selectbox("pad_bytes", PAD_LEVELS, format_func=lambda value: f"{value} B", key="single_level")
    if mode == "random":
        seed = st.number_input("Seed", min_value=0, value=SEED, step=1, key="single_seed")
    else:
        seed = SEED
    threshold_key = st.selectbox(
        "Ngưỡng đánh giá model",
        list(THRESHOLD_OPTIONS),
        index=list(THRESHOLD_OPTIONS).index(DEFAULT_THRESHOLD_KEY),
        format_func=lambda key: THRESHOLD_OPTIONS[key],
        key="padding_threshold",
        help="Ngưỡng này áp dụng cho so sánh model trong chế độ lô và robustness.",
    )
    run_mode = st.radio("Phạm vi", ["Một flow", "Lô trên mẫu"], horizontal=True)
    if not st.button("▶ Áp dụng", type="primary"):
        st.info("Chọn flow, mode và pad_bytes rồi bấm “Áp dụng”.")
        return
    selected = candidates.iloc[[int(flow_position)]].copy()
    try:
        with st.spinner("Đang áp dụng Padding và chạy Validator..."):
            if run_mode == "Một flow":
                single_perturbation_view(selected, level, mode, int(seed))
            else:
                batch_perturbation_view(
                    candidates.head(200), level, mode, int(seed), threshold_key
                )
    except Exception as exc:
        st.error(f"Không thể áp dụng Padding: {exc}")


def robustness_evaluation() -> None:
    page_header(
        "Đánh giá độ bền vững của mô hình",
        "Sử dụng trực tiếp kết quả Padding đã áp dụng ở trang “Áp dụng biến đổi dữ liệu”.",
    )
    padding_result = st.session_state.get("padding_result")
    padding_clean = st.session_state.get("padding_clean")
    padding_config = st.session_state.get("padding_config")
    if padding_result is None or padding_clean is None:
        st.markdown(
            '<div class="dgt-card"><h4>Chưa có scenario để đánh giá</h4>'
            '<p>Hãy chạy một experiment ở trang Áp dụng biến đổi dữ liệu. '
            'Kết quả sẽ được giữ trong phiên làm việc hiện tại.</p></div>',
            unsafe_allow_html=True,
        )
        return
    mode = padding_config["mode"]
    level = padding_config["level"]
    seed = padding_config["seed"]
    threshold_key = st.selectbox(
        "Ngưỡng đánh giá model",
        list(THRESHOLD_OPTIONS),
        index=list(THRESHOLD_OPTIONS).index(
            st.session_state.get("padding_threshold", DEFAULT_THRESHOLD_KEY)
        ),
        format_func=lambda key: THRESHOLD_OPTIONS[key],
        key="robustness_threshold",
        help="Chọn threshold để xem trade-off giữa bỏ sót Attack và cảnh báo nhầm.",
    )
    st.info(
        f"Đang dùng cấu hình đã áp dụng: {scenario_label(mode, level)}, "
        f"seed {seed}, phạm vi {padding_config['scope']}."
    )
    ui_pills([
        (scenario_label(mode, level).upper(), ""),
        (padding_config["scope"].upper(), "amber"),
        ("READY TO EVALUATE", "green"),
    ])
    if not st.button("▶ Đánh giá cả ba model", type="primary"):
        st.info("Bấm nút để đánh giá cả ba model trên cùng dữ liệu.")
        return
    try:
        if len(padding_clean) != len(padding_result):
            raise ValueError(
                "Dữ liệu sạch và dữ liệu sau Padding không cùng số dòng; "
                "vui lòng áp dụng lại biến đổi."
            )
        nonscale = padding_clean.reset_index(drop=True)
        perturbed = padding_result.reset_index(drop=True)
        failed = perturbed.get(
            "__validation_failed",
            pd.Series(False, index=perturbed.index, dtype=bool),
        ).reset_index(drop=True)
        valid = ~failed
        if "Label_binary" not in nonscale.columns:
            raise ValueError("Dữ liệu đánh giá thiếu cột Label_binary.")
        y_true = nonscale.loc[valid, "Label_binary"].astype(int)
        rows = []
        for model_name in MODEL_FILES:
            artifact = cached_model(model_name)
            clean_pred, clean_score = predict(
                prepare_model_input(nonscale.loc[valid], artifact),
                artifact,
                threshold_key,
            )
            pert_pred, pert_score = predict(
                prepare_model_input(perturbed.loc[valid], artifact),
                artifact,
                threshold_key,
            )
            for dataset, pred, scores in [
                ("Dữ liệu sạch", clean_pred, clean_score),
                ("Sau Padding", pert_pred, pert_score),
            ]:
                rows.append(
                    {
                        "Model": MODEL_LABELS[model_name],
                        "Dữ liệu": dataset,
                        **metrics(y_true, pred, scores),
                    }
                )
        table = metrics_table(rows)
        st.success(f"Đã đánh giá {mode_label(mode)} {level} B.")
        st.caption(f"Dùng {int(valid.sum()):,}/{len(valid):,} dòng hợp lệ.")
        metric_columns = [
            "accuracy",
            "balanced_accuracy",
            "precision_attack",
            "recall_attack",
            "f1_attack",
            "specificity",
            "fpr",
        ]
        view = table[["Model", "Dữ liệu"] + metric_columns].copy()
        view.columns = [
            "Model",
            "Dữ liệu",
            "Accuracy",
            "Balanced Accuracy",
            "Precision Attack",
            "DR / Recall",
            "F1 Attack",
            "Specificity",
            "FPR",
        ]
        for column in view.columns[2:]:
            view[column] = view[column].map(lambda value: metric_value(value, True))
        st.dataframe(view, hide_index=True, use_container_width=True)
        chart_data = table.melt(
            id_vars=["Model", "Dữ liệu"],
            value_vars=["accuracy", "balanced_accuracy", "recall_attack", "f1_attack", "fpr"],
            var_name="Chỉ số",
            value_name="Giá trị",
        )
        chart_data["Chỉ số"] = chart_data["Chỉ số"].map(
            {
                "accuracy": "Accuracy",
                "balanced_accuracy": "Balanced Accuracy",
                "recall_attack": "DR / Recall",
                "f1_attack": "F1 Attack",
                "fpr": "FPR",
            }
        )
        st.plotly_chart(
            px.bar(
                chart_data,
                x="Model",
                y="Giá trị",
                color="Dữ liệu",
                facet_col="Chỉ số",
                barmode="group",
                title="So sánh dữ liệu sạch và sau Padding",
                labels={"Giá trị": "Giá trị"},
                template="plotly_dark",
            ).update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,27,45,.55)",
                font={"color": "#dbeafe"},
                legend={"orientation": "h", "y": 1.12},
                margin={"t": 70, "l": 20, "r": 20, "b": 20},
            ),
            use_container_width=True,
        )
        csv_download(table, f"branch_a_robustness_{mode}_{level}B.csv")
        show_terms()
    except Exception as exc:
        st.error(f"Không thể đánh giá robustness: {exc}")


def main() -> None:
    inject_styles()
    page = sidebar()
    if page.startswith("⌂"):
        overview()
    elif page == "Phát hiện xâm nhập":
        intrusion_detection()
    elif page == "Áp dụng biến đổi dữ liệu":
        perturbation_lab()
    elif page == "Đánh giá độ bền vững của mô hình":
        robustness_evaluation()


if __name__ == "__main__":
    main()
