from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

HISTORY_DAYS = 180         # 180 дней для train
LABEL_DELAY_DAYS = 22      # ждём до 15 дней Route1 + до 7 дней Route2
FEATURE_HISTORY_DAYS = 52  # 28 hazard + D-3 + очередь до 21 дня

TARGET = "target_t2_median_h"

EDGE_FEATURES = [
    "shift_L7_z", "baseline21", "scale21", "days_since_last_fact",
    "shift_L3_z", "shift_L5_z", "shift_L14_z",  # shift_L7_z указан выше
    "d3_14", "d5_14", "d7_14", "d3_7", "abs_d3_14", "abs_d5_14", "abs_d7_14",
    "L3_days", "L5_days", "L7_days", "L14_days",
    "L3_srids", "L5_srids", "L7_srids", "L14_srids",
    "volume_ratio_3_14", "volume_ratio_5_14", "volume_ratio_7_14",
    "known_ratio_3_14", "known_ratio_5_14", "known_ratio_7_14",
]
PENDING_FEATURES = [
    "pending_count_14d", "pending_p50_age_h", "pending_p90_age_h",
    "pending_share_gt24", "pending_share_gt48", "pending_share_gt72",
    "backlog_days", "flow_imbalance",
]
ALIGN_STATE = [
    "r2q_count", "r2q_p90_age_h", "r2q_share_gt48",
    "r2_pressure_ratio", "r2_deficit", "capacity_drop_ratio", "hazard_next1",
]
ALIGN3_FEATURES = [
    "r1_L7_h", "r1_L14_h", "r1_fastslow_h", "r1_L7_n", "r1_expected_entry_days",
    *[f"aligned3_{c}" for c in ALIGN_STATE], "alignment3_any_clipped",
]
LM_PEER_FEATURES = [
    "lm_peer_z", "lm_peer_fastgap_z", "lm_peer_degree",
    "lm_peer_breadth_abs1", "lm_peer_volume", "lm_group_iqr_z",
]
BASE = EDGE_FEATURES + PENDING_FEATURES
MODEL_FEATURES = {
    "edge_pending": BASE,
    "align3": BASE + ALIGN3_FEATURES,
    "lm_peers": BASE + LM_PEER_FEATURES,
    "align3_lm_peers": BASE + ALIGN3_FEATURES + LM_PEER_FEATURES,
}


def target_window(interval_end_day):
    """Задержка меток 22 дня; окно обучения 180 дней."""
    target_to = interval_end_day - timedelta(days=LABEL_DELAY_DAYS)
    return target_to - timedelta(days=HISTORY_DAYS - 1), target_to


def _fit_align_bounds(df):
    bounds = {c: (0.0, df[c].quantile(0.99)) for c in ALIGN_STATE}
    bounds["r2_deficit"] = tuple(df["r2_deficit"].quantile([0.01, 0.99]))
    bounds["r2q_share_gt48"] = bounds["hazard_next1"] = (0.0, 1.0)
    return bounds


def add_align3(df, bounds):
    """протягиваем состояние B от D до ожидаемого входа в Route2. всё ещё хотим
каким будет состояние узла B не сегодня, а к моменту, 
когда сегодняшний SRID войдёт в Route2"""
    clipped = pd.Series(False, index=df.index)
    for c in ALIGN_STATE:
        low, high = bounds[c]
        x = df[c] + df["r1_expected_entry_days"] * (df[c] - df[f"{c}_lag3"]) / 3.0
        df[f"aligned3_{c}"] = x.clip(low, high)
        clipped |= (x < low) | (x > high)
    df["alignment3_any_clipped"] = clipped.astype(np.int8)


def _new_model():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("model", HistGradientBoostingRegressor(
            loss="absolute_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=31,
            min_samples_leaf=30, l2_regularization=1.0, random_state=42,
        )),
    ])


def train_models(df):
    if df.empty:
        raise ValueError("Пустая обучающая таблица")
    bounds = _fit_align_bounds(df)
    add_align3(df, bounds)
    y = (df[TARGET] - df["baseline21"]) / df["scale21"]
    models = {name: _new_model().fit(df[cols], y) for name, cols in MODEL_FEATURES.items()}
    return {"models": models, "align_bounds": bounds}


def predict_models(df, artifact):
    if df.empty:
        raise ValueError("Пустая таблица для прогноза")
    add_align3(df, artifact["align_bounds"])
    for name, model in artifact["models"].items():
        z = model.predict(df[MODEL_FEATURES[name]])
        yield name, df[["src_osm_id", "lm_osm_id"]].assign(
            duration=df["baseline21"] + df["scale21"] * z
        )
