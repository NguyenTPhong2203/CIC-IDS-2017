from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd


MODEL_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "models"
SCALER_FILE = Path(__file__).resolve().parent.parent / "data" / "scaler_day_based_82.joblib"
DEFAULT_THRESHOLD_KEY = "fpr0.1%"
MODEL_FILES = {
    "Random Forest": MODEL_DIR / "random_forest.joblib",
    "XGBoost": MODEL_DIR / "xgboost.joblib",
    "LightGBM": MODEL_DIR / "lightgbm.joblib",
}


def load_model(name: str) -> dict:
    if name not in MODEL_FILES:
        raise ValueError(f"Model không được hỗ trợ: {name}")
    artifact = joblib.load(MODEL_FILES[name])
    if not isinstance(artifact, dict) or not {"model", "features"}.issubset(artifact):
        raise ValueError(f"Artifact {name} không có đủ model và features.")
    scaler = joblib.load(SCALER_FILE)
    expected_features = len(artifact["features"])
    if not hasattr(scaler, "transform") or getattr(
        scaler, "n_features_in_", expected_features
    ) != expected_features:
        raise ValueError(
            f"Scaler {SCALER_FILE.name} không tương thích với model {name}: "
            f"cần {expected_features} feature."
        )
    artifact["scaler"] = scaler
    artifact["scaler_file"] = str(SCALER_FILE)
    return artifact


def feature_matrix(df: pd.DataFrame, artifact: dict) -> np.ndarray:
    features = list(artifact["features"])
    missing = [c for c in features if c not in df.columns]
    if missing:
        raise ValueError(f"Dữ liệu thiếu {len(missing)} feature: {missing[:10]}")
    values = df[features].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError("Feature đầu vào có NaN hoặc Inf.")
    return values.astype(np.float32)


def predict(
    df: pd.DataFrame,
    artifact: dict,
    threshold_key: str = DEFAULT_THRESHOLD_KEY,
) -> tuple[np.ndarray, np.ndarray | None]:
    estimator = artifact["model"]
    values = feature_matrix(df, artifact)
    scores = None
    if hasattr(estimator, "predict_proba"):
        scores = np.asarray(estimator.predict_proba(values))[:, 1]
    if scores is not None:
        thresholds = artifact.get("thresholds", {})
        threshold = thresholds.get(threshold_key, 0.5)
        labels = (scores >= float(threshold)).astype(int)
    else:
        labels = np.asarray(estimator.predict(values)).astype(int)
    return labels, scores
