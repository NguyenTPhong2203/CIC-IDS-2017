"""validator_lib.py — Kiểm tra ràng buộc sau Padding.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .perturbation import MODIFIABLE_COLS as MODIFIABLE

RULE_VI = {
    "non_finite_new": "Sinh giá trị NaN/Inf mới",
    "negative_value_new": "Sinh giá trị âm mới ở cột được sửa",
    "modifiable_decreased": "Cột được sửa bị giảm (Padding chỉ được tăng)",
    "immutable_changed": "Cột bất biến bị thay đổi",
    "min_mean_max_new": "Vi phạm thứ tự Min ≤ Mean ≤ Max",
}


def _check_order_violation(
    frame: pd.DataFrame, lo: str, mid: str, hi: str
) -> np.ndarray:
    """Return rows that violate the Min <= Mean <= Max relationship."""
    lower = frame[lo].to_numpy(float)
    mean = frame[mid].to_numpy(float)
    upper = frame[hi].to_numpy(float)
    tolerance = 1e-6 * np.abs(mean) + 1e-9
    return (lower > mean + tolerance) | (mean > upper + tolerance)


def validate(original, perturbed):
    O, P = original.to_numpy(float), perturbed.to_numpy(float)
    v = {"non_finite_new": (~np.isfinite(P).all(1)) & np.isfinite(O).all(1)}
    mut = [c for c in MODIFIABLE if c in original.columns]
    imm = [c for c in original.columns if c not in MODIFIABLE]
    if mut:
        om, pm = original[mut].to_numpy(float), perturbed[mut].to_numpy(float)
        v["negative_value_new"] = ((pm<0)&(om>=0)).any(1)
        v["modifiable_decreased"] = (pm < om-(1e-6*np.abs(om)+1e-9)).any(1)
    else:
        v["negative_value_new"] = np.zeros(len(O), bool); v["modifiable_decreased"] = np.zeros(len(O), bool)
    if imm:
        oi, pi = original[imm].to_numpy(float), perturbed[imm].to_numpy(float)
        v["immutable_changed"] = (np.abs(pi-oi) > 1e-6*np.abs(oi)+1e-9).any(1)
    else: v["immutable_changed"] = np.zeros(len(O), bool)
    order_bad = np.zeros(len(O), bool)
    for lo, mid, hi in [("Fwd Packet Length Min","Fwd Packet Length Mean","Fwd Packet Length Max"),
                        ("Packet Length Min","Packet Length Mean","Packet Length Max")]:
        if all(c in original.columns for c in (lo,mid,hi)):
            order_bad |= _check_order_violation(
                perturbed, lo, mid, hi
            ) & ~_check_order_violation(original, lo, mid, hi)
    v["min_mean_max_new"] = order_bad
    return pd.DataFrame(v)


def violation_report(violations: pd.DataFrame) -> pd.DataFrame:
    """Bảng đếm vi phạm theo rule + dòng ANY (cùng định dạng validation_report.csv của notebook)."""
    rows = [{"rule": c, "n_violations": int(violations[c].sum()),
             "pct_of_rows": round(100 * float(violations[c].mean()), 3) if len(violations) else 0.0}
            for c in violations]
    anyv = violations.any(axis=1)
    rows.append({"rule": "ANY", "n_violations": int(anyv.sum()),
                 "pct_of_rows": round(100 * float(anyv.mean()), 3) if len(violations) else 0.0})
    return pd.DataFrame(rows)
