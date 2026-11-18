from __future__ import annotations

import numpy as np
import pandas as pd

MUTABLE_COLS = ["Fwd Packets Length Total"]
DERIVED_COLS = ["Fwd Packet Length Mean", "Packet Length Mean", "Avg Packet Size",
                "Avg Fwd Segment Size", "Flow Bytes/s"]
MODIFIABLE_COLS = MUTABLE_COLS + DERIVED_COLS
# Các cột phụ thuộc vào kích thước gói nhưng không thể tái tạo chính xác từ dữ liệu flow -> giữ nguyên.
PRESERVED_UNIDENTIFIABLE_COLS = [
    "Fwd Packet Length Min", "Fwd Packet Length Max", "Fwd Packet Length Std",
    "Packet Length Min", "Packet Length Max", "Packet Length Std", "Packet Length Variance",
    "Subflow Fwd Bytes", "Subflow Bwd Bytes", "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk",
    "Fwd Avg Bulk Rate", "Bwd Avg Bytes/Bulk", "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate",
]
REQUIRED_COLS = ["Fwd Act Data Packets", "Total Fwd Packets", "Total Backward Packets",
                 "Fwd Packets Length Total", "Bwd Packets Length Total", "Flow Duration",
                 "Fwd Packet Length Mean", "Packet Length Mean", "Avg Packet Size",
                 "Avg Fwd Segment Size", "Flow Bytes/s"]
PAD_LEVELS = [16, 64, 256]
PAD_MODES = ["static", "random"]
SEED = 42


def arr(df, col):
    return pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=np.float64)


def apply_padding(df, pad_bytes, mode, rng):
    """Trả (perturbed_df, applicable_mask, bytes_added)."""
    req = REQUIRED_COLS
    miss = [c for c in req if c not in df.columns]
    if miss: raise KeyError(f"Thiếu feature cần cho Padding: {miss}")
    n = len(df); out = df.copy()
    active = np.clip(arr(df, "Fwd Act Data Packets"), 0, None)
    fn = np.clip(arr(df, "Total Fwd Packets"), 0, None)
    bn = np.clip(arr(df, "Total Backward Packets"), 0, None)
    tn = fn + bn
    ft, bt = arr(df, "Fwd Packets Length Total"), arr(df, "Bwd Packets Length Total")
    fm, pm = arr(df, "Fwd Packet Length Mean"), arr(df, "Packet Length Mean")
    fmax = arr(df, "Fwd Packet Length Max") if "Fwd Packet Length Max" in df else np.full(n, np.inf)
    pmax = arr(df, "Packet Length Max") if "Packet Length Max" in df else np.full(n, np.inf)
    dur = arr(df, "Flow Duration")
    selected = np.floor(active) if mode == "static" else rng.binomial(np.floor(active).astype(np.int64), .5)
    requested = selected * float(pad_bytes)
    cap_fwd = np.maximum(0, (fmax - fm) * fn)
    # (new forward bytes + backward bytes) / total packets <= packet max.
    cap_all = np.maximum(0, pmax * tn - ft - bt)
    add = np.minimum(requested, np.minimum(cap_fwd, cap_all))
    add = np.where((active >= 1) & (fn > 0) & (tn > 0), add, 0.0)
    applicable = add > 0
    new_fwd_total = ft + add
    new_total_bytes = new_fwd_total + bt
    def assign(c, v):
        if c in out.columns: out[c] = np.where(applicable, v, arr(df,c))
    assign("Fwd Packets Length Total", new_fwd_total)
    nfm = np.divide(new_fwd_total, fn, out=fm.copy(), where=fn>0)
    npm = np.divide(new_total_bytes, tn, out=pm.copy(), where=tn>0)
    assign("Fwd Packet Length Mean", nfm)
    assign("Avg Fwd Segment Size", nfm)
    assign("Packet Length Mean", npm)
    assign("Avg Packet Size", npm)
    old_rate = arr(df, "Flow Bytes/s")
    rate = np.divide(new_total_bytes, dur / 1e6, out=old_rate.copy(), where=dur > 0)
    assign("Flow Bytes/s", rate)
    return out, applicable, add
