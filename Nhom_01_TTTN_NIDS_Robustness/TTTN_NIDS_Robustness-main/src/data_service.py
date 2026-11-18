from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_DATA_FILES = {
    False: (
        "100_Thursday_non_scale.parquet",
        "100_Thursday_non_scale.csv",
    ),
    True: (
        "100_Thursday_scaled.parquet",
        "100_Thursday_scaled.csv",
    ),
}
FEATURES = [
    "Protocol", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Fwd Packets Length Total", "Bwd Packets Length Total", "Fwd Packet Length Max",
    "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean",
    "Bwd Packet Length Std", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean",
    "Flow IAT Std", "Flow IAT Max", "Flow IAT Min", "Fwd IAT Total", "Fwd IAT Mean",
    "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Total", "Bwd IAT Mean",
    "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Fwd PSH Flags", "Bwd PSH Flags",
    "Fwd URG Flags", "Bwd URG Flags", "Fwd RST Flags", "Bwd RST Flags",
    "Fwd Header Length", "Bwd Header Length", "Fwd Packets/s", "Bwd Packets/s",
    "Packet Length Min", "Packet Length Max", "Packet Length Mean",
    "Packet Length Std", "Packet Length Variance", "FIN Flag Count", "SYN Flag Count",
    "RST Flag Count", "PSH Flag Count", "ACK Flag Count", "URG Flag Count",
    "CWR Flag Count", "ECE Flag Count", "Down/Up Ratio", "Avg Packet Size",
    "Avg Fwd Segment Size", "Avg Bwd Segment Size", "Fwd Avg Bytes/Bulk",
    "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate", "Bwd Avg Bytes/Bulk",
    "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate", "Subflow Fwd Packets",
    "Subflow Fwd Bytes", "Subflow Bwd Packets", "Subflow Bwd Bytes",
    "Init Fwd Win Bytes", "Init Bwd Win Bytes", "Fwd Act Data Packets",
    "Fwd Seg Size Min", "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min", "ICMP Code", "ICMP Type",
    "Total TCP Flow Time",
]


def _validate_frame(df: pd.DataFrame, name: str) -> pd.DataFrame:
    required = set(FEATURES) | {"Label", "Label_binary"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name} thiếu feature bắt buộc: {missing[:10]}")
    result = df.reset_index(drop=True).copy()
    result["Label_binary"] = pd.to_numeric(result["Label_binary"], errors="raise").astype(int)
    if not result["Label_binary"].isin([0, 1]).all():
        raise ValueError(f"{name}: Label_binary phải chỉ gồm 0 và 1.")
    numeric = result[FEATURES].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError(f"{name}: feature chứa NaN, Inf hoặc kiểu không phải số.")
    result[FEATURES] = numeric
    return result


def load_test_data(scaled: bool) -> pd.DataFrame:
    candidates = DEFAULT_DATA_FILES[scaled]
    for filename in candidates:
        path = DATA_DIR / filename
        if not path.exists():
            continue
        if path.suffix.lower() == ".csv":
            frame = pd.read_csv(path)
        else:
            frame = pd.read_parquet(path)
        return _validate_frame(frame, filename)
    raise FileNotFoundError(
        f"Không tìm thấy dữ liệu thử nghiệm. Đã kiểm tra: "
        f"{', '.join(candidates)}"
    )


def select_sample(df: pd.DataFrame, limit: int | None, seed: int = 42) -> pd.DataFrame:
    if limit is None or limit >= len(df):
        return df.reset_index(drop=True)
    if limit < 1:
        raise ValueError("Giới hạn số dòng phải lớn hơn 0.")
    if "Label_binary" not in df:
        return df.sample(limit, random_state=seed).reset_index(drop=True)
    groups = list(df.groupby("Label_binary", sort=True))
    counts = [min(len(group), max(1, round(limit * len(group) / len(df))))
              for _, group in groups]
    while sum(counts) > limit:
        candidates = [i for i, count in enumerate(counts) if count > 1]
        if not candidates:
            break
        index = max(candidates, key=lambda i: counts[i])
        counts[index] -= 1
    while sum(counts) < limit:
        candidates = [i for i, (_, group) in enumerate(groups)
                      if counts[i] < len(group)]
        if not candidates:
            break
        index = max(
            candidates,
            key=lambda i: len(groups[i][1]) / max(counts[i], 1),
        )
        counts[index] += 1
    parts = [
        group.sample(counts[i], random_state=seed + int(label))
        for i, (label, group) in enumerate(groups)
        if counts[i] > 0
    ]
    result = pd.concat(parts).sample(frac=1, random_state=seed)
    if len(result) > limit:
        result = result.iloc[:limit]
    return result.reset_index(drop=True)
