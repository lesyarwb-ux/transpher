# train: признаки и target по дням создания в заданном окне.
# predict: признаки на один prediction_day без target.

import numpy as np
import pandas as pd
from pyspark.sql import functions as F
from route2_core import TARGET

KEYS = ["prediction_day", "src_osm_id", "lm_osm_id"]
WINDOWS = (3, 5, 7, 14)
BASELINE_DAYS = 21
ROUTE1_DAYS = 14
PENDING_LOOKBACK_DAYS = 14
R2Q_LOOKBACK_DAYS = 21
SCALE_FLOOR_H = 1.0
HAZARD_MAX_AGE_DAY = 14
HAZARD_PRIOR_WEIGHT = 50.0
HAZARD_LOOKBACK_DAYS = 28
LAG_DAYS = 3

DAY = pd.Timedelta(days=1)
NODE_DAY = ["prediction_day", "lm_osm_id"]


def _hours(start, end):
    return (F.col(end).cast("long") - F.col(start).cast("long")) / 3600.0

def _median(col):
    return F.percentile_approx(col, 0.5)

def _trailing(daily, days):
    """размножаем дневной факт вперёд на нужное окно"""
    return (daily
            .withColumn("prediction_day", F.explode(F.sequence(F.date_add("available_day", 1), F.date_add("available_day", days))))
            .withColumn("age_days", F.datediff("prediction_day", "available_day")))


def build_edge_state(raw):
    """история Route2 по ребру A->B"""
    daily = (
        raw.filter(F.col("timestamp_src").isNotNull() & F.col("timestamp_lm").isNotNull())
        .groupBy(F.to_date("timestamp_lm").alias("available_day"), "src_osm_id", "lm_osm_id")
        .agg(F.count("srid").alias("n"), _median(_hours("timestamp_src", "timestamp_lm")).alias("t2_h"))
    )
    aggs = [
        _median("t2_h").alias("baseline21"),
        F.percentile_approx("t2_h", 0.25).alias("p25"),
        F.percentile_approx("t2_h", 0.75).alias("p75"),
        F.max("available_day").alias("last_fact_day"),
    ]
    for w in WINDOWS:
        in_w = F.col("age_days") <= w
        aggs += [
            _median(F.when(in_w, F.col("t2_h"))).alias(f"L{w}_h"),
            F.count(F.when(in_w, 1)).alias(f"L{w}_days"),
            F.sum(F.when(in_w, F.col("n"))).alias(f"L{w}_srids"),
        ]

    # совсем мёртвые рёбра не тащим
    state = _trailing(daily, BASELINE_DAYS).groupBy(*KEYS).agg(*aggs).filter(F.col("L3_h").isNotNull())

    return (state
            .withColumn("scale21", F.greatest((F.col("p75") - F.col("p25")) / 1.349, F.lit(SCALE_FLOOR_H)))
            .withColumns({f"shift_L{w}_z": (F.col(f"L{w}_h") - F.col("baseline21")) / F.col("scale21") for w in WINDOWS})
            .withColumns({f"d{a}_{b}": F.col(f"shift_L{a}_z") - F.col(f"shift_L{b}_z") for a, b in ((3, 14), (5, 14), (7, 14), (3, 7))})
            .withColumns({f"abs_d{a}_14": F.abs(f"d{a}_14") for a in (3, 5, 7)})
            .withColumns({f"volume_ratio_{w}_14": F.col(f"L{w}_srids") / F.col("L14_srids") for w in (3, 5, 7)})
            .withColumns({f"known_ratio_{w}_14": F.col(f"L{w}_days") / F.col("L14_days") for w in (3, 5, 7)})
            .withColumn("days_since_last_fact", F.datediff("prediction_day", "last_fact_day")))


def build_target(raw, target_from, target_to):
    """target = медиана T2 для созданных в день D объектов на A->B"""
    created = F.to_date("timestamp_created")
    return (
        raw.filter(created.between(target_from, target_to) & F.col("timestamp_src").isNotNull() & F.col("timestamp_lm").isNotNull())
        .groupBy(created.alias("prediction_day"), "src_osm_id", "lm_osm_id")
        .agg(_median(_hours("timestamp_src", "timestamp_lm")).alias(TARGET))
    )


def build_route1_features(raw):
    daily = (
        raw.filter(F.col("timestamp_src").isNotNull())
        .groupBy(F.to_date("timestamp_src").alias("available_day"), "src_osm_id", "lm_osm_id")
        .agg(_median(_hours("timestamp_created", "timestamp_src")).alias("r1_h"), F.count("srid").alias("n"))
    )
    last7 = F.col("age_days") <= 7
    return (
        _trailing(daily, ROUTE1_DAYS).groupBy(*KEYS)
        .agg(
            _median(F.when(last7, F.col("r1_h"))).alias("r1_L7_h"),
            _median("r1_h").alias("r1_L14_h"),
            F.sum(F.when(last7, F.col("n")).otherwise(0)).alias("r1_L7_n"),
        )
        .withColumn("r1_fastslow_h", F.col("r1_L7_h") - F.col("r1_L14_h"))
        .withColumn("r1_expected_entry_days", F.least(F.greatest(F.col("r1_L7_h") / 24.0, F.lit(0.0)), F.lit(5.0)))
    )


def _cohorts(raw, start, end):
    """cohorts = сколько объектов вошло в процесс в каждый день
exits   = сколько из этих когорт вышло в каждый день
все объекты, которые начали процесс в один день и идут в один B, считаются одной когортой"""
    cohorts = (
        raw.filter(F.col(start).isNotNull())
        .groupBy(F.to_date(start).alias("cohort_day"), "lm_osm_id")
        .agg(F.count("srid").alias("size"))
        .toPandas().astype({"cohort_day": "datetime64[ns]"})
    )
    exits = (
        raw.filter(F.col(start).isNotNull() & F.col(end).isNotNull())
        .groupBy(F.to_date(start).alias("cohort_day"), F.to_date(end).alias("exit_day"), "lm_osm_id")
        .agg(F.count("srid").alias("n"))
        .toPandas().astype({"cohort_day": "datetime64[ns]", "exit_day": "datetime64[ns]"})
    )
    return cohorts, exits


def _snapshots(cohorts, exits, first_day, last_day, lookback):
    """разворачиваем когорту по дням: сколько ещё висит и сколько ей часов"""
    c = cohorts.assign(
        d0=(cohorts.cohort_day + DAY).clip(lower=first_day),
        d1=(cohorts.cohort_day + lookback * DAY).clip(upper=last_day),
    )
    c = c[c.d1 >= c.d0].reset_index(drop=True)
    snap = c.loc[c.index.repeat((c.d1 - c.d0).dt.days + 1)]
    snap["prediction_day"] = snap.d0 + pd.to_timedelta(snap.groupby(level=0).cumcount().to_numpy(), unit="D")

    done = exits.sort_values("exit_day")
    done["done"] = done.groupby(["lm_osm_id", "cohort_day"]).n.cumsum()
    snap = pd.merge_asof(
        snap.sort_values("prediction_day"), done[["lm_osm_id", "cohort_day", "exit_day", "done"]],
        left_on="prediction_day", right_on="exit_day", by=["lm_osm_id", "cohort_day"],
        allow_exact_matches=False,  # события дня D ещё не знаем
    )
    snap["pending"] = snap["size"] - snap.done.fillna(0)
    snap["age_h"] = ((snap.prediction_day - snap.cohort_day).dt.days - 1) * 24.0
    return snap


def _queue_stats(snap, prefix, quantiles, share_hours):
    """размер очереди, возраст и доля старых объектов по B и дню"""
    by_node_day = [snap.prediction_day, snap.lm_osm_id]
    out = pd.DataFrame({f"{prefix}_count": snap.groupby(by_node_day).pending.sum()})
    for h in share_hours:
        old = snap.pending.where(snap.age_h >= h, 0.0).groupby(by_node_day).sum()
        out[f"{prefix}_share_gt{h}"] = (old / out[f"{prefix}_count"]).fillna(0.0)

    live = snap[snap.pending > 0].sort_values(NODE_DAY + ["age_h"], kind="mergesort")
    g = live.groupby(NODE_DAY).pending
    cum, total = g.cumsum(), g.transform("sum")
    for q in quantiles:
        out[f"{prefix}_p{round(q * 100)}_age_h"] = live.age_h[cum >= q * total].groupby([live.prediction_day, live.lm_osm_id]).first()
    return out


def _flows(cohorts, exits, nodes, first_day, last_day):
    """входы/выходы B за вчера + средние за 7 дней"""
    ins = cohorts.groupby(["lm_osm_id", cohorts.cohort_day + DAY])["size"].sum().rename_axis(["lm_osm_id", "prediction_day"])
    outs = exits.groupby(["lm_osm_id", exits.exit_day + DAY]).n.sum().rename_axis(["lm_osm_id", "prediction_day"])
    calendar = pd.MultiIndex.from_product([nodes, pd.date_range(first_day - 6 * DAY, last_day)], names=["lm_osm_id", "prediction_day"])
    f = pd.concat({"ins": ins, "outs": outs}, axis=1).reindex(calendar).fillna(0.0)
    g = f.groupby(level="lm_osm_id")
    f["ins7"] = g.ins.transform(lambda x: x.rolling(7).mean())
    f["outs7"] = g.outs.transform(lambda x: x.rolling(7).mean())
    return f.reset_index().set_index(NODE_DAY)


def build_pending_features(raw, nodes, days):
    """created -> B: кто за 14 дней ещё не дошёл до timestamp_lm"""
    cohorts, exits = _cohorts(raw, "timestamp_created", "timestamp_lm")
    snap = _snapshots(cohorts, exits, days.min(), days.max(), PENDING_LOOKBACK_DAYS)
    out = _queue_stats(snap, "pending", (0.5, 0.9), (24, 48, 72)).rename(columns={"pending_count": "pending_count_14d"})
    out[["pending_p50_age_h", "pending_p90_age_h"]] = out[["pending_p50_age_h", "pending_p90_age_h"]].fillna(0.0)

    f = out.join(_flows(cohorts, exits, nodes, days.min(), days.max()))
    out["backlog_days"] = f.pending_count_14d / f.ins7.where(f.ins7 > 0)
    out["flow_imbalance"] = ((f.ins - f.outs) / (f.ins + f.outs)).fillna(0.0)
    return out.reset_index()


def _past_sum(frame, keys, cols):
    f = frame.sort_values("prediction_day", kind="mergesort")
    past = f.groupby(keys).rolling(f"{HAZARD_LOOKBACK_DAYS}D", on="prediction_day", closed="left")[cols].sum() #про лефт: данные текущего дня не используются, только прошлое
    rows = pd.MultiIndex.from_frame(frame[keys + ["prediction_day"]])
    return past.reindex(rows).fillna(0.0).set_axis(frame.index)


def _hazard(snap, exits):
    """примерно какая доля текущей очереди B выйдет за следующий день"""
    today = exits.rename(columns={"exit_day": "prediction_day", "n": "exits"})
    s = snap.merge(today, on=["lm_osm_id", "cohort_day", "prediction_day"], how="left")
    s["age"] = (s.age_h // 24).clip(upper=HAZARD_MAX_AGE_DAY)
    s["exits"] = s.exits.fillna(0.0).clip(upper=s.pending)

    cols = ["pending", "exits"]
    a = s.groupby(["prediction_day", "lm_osm_id", "age"], as_index=False)[cols].sum()
    glob = a.groupby(["prediction_day", "age"], as_index=False)[cols].sum()
    glob_past = _past_sum(glob, ["age"], cols)
    glob["h_global"] = (glob_past.exits / glob_past.pending).fillna(0.0)
    a = a.merge(glob[["prediction_day", "age", "h_global"]], on=["prediction_day", "age"])

    node_past = _past_sum(a, ["lm_osm_id", "age"], cols)
    h_node = (node_past.exits + HAZARD_PRIOR_WEIGHT * a.h_global) / (node_past.pending + HAZARD_PRIOR_WEIGHT)
    a["expected"] = a.pending * h_node
    g = a.groupby(NODE_DAY)
    return (g.expected.sum() / g.pending.sum()).fillna(0.0).rename("hazard_next1")


def build_queue_state(raw, nodes, days):
    """описать, насколько сейчас загружен узел B и как его состояние изменилось за последние 3 дня.
      плюс D-3 для align3, где
      D3 -- состояние того же узла B три дня назад относительно текущего дня D"""
    cohorts, exits = _cohorts(raw, "timestamp_src", "timestamp_lm")
    first_day = days.min() - (HAZARD_LOOKBACK_DAYS + LAG_DAYS) * DAY  # hazard нужен и на D−3
    snap = _snapshots(cohorts, exits, first_day, days.max(), R2Q_LOOKBACK_DAYS)

    f = _flows(cohorts, exits, nodes, first_day, days.max())
    base = f.outs7.clip(lower=1.0)
    f["r2_pressure_ratio"] = f.ins / base
    f["r2_deficit"] = f.ins - f.outs
    f["capacity_drop_ratio"] = f.outs / base

    q = (
        _queue_stats(snap, "r2q", (0.9,), (48,))
        .join(f[["r2_pressure_ratio", "r2_deficit", "capacity_drop_ratio"]])
        .join(_hazard(snap, exits))
        .reset_index()
    )
    lag = q.assign(prediction_day=q.prediction_day + LAG_DAYS * DAY)
    q = q.merge(lag, on=NODE_DAY, how="left", suffixes=("", "_lag3"))
    return q[q.prediction_day >= days.min()]


# соседи по B


def _loo_median(x):
    if len(x) < 2:
        return np.full(len(x), np.nan)
    return np.array([np.median(np.delete(x, i)) for i in range(len(x))])


def _peer_block(g):
    z, gap, vol = (g[c].to_numpy(float) for c in ("shift_L7_z", "d3_14", "L14_srids"))
    degree = len(g) - 1
    high = np.abs(z) >= 1.0
    return pd.DataFrame({
        "lm_peer_z": _loo_median(z),
        "lm_peer_fastgap_z": _loo_median(gap),
        "lm_peer_degree": degree,
        "lm_peer_breadth_abs1": (high.sum() - high) / degree if degree else np.nan,
        "lm_peer_volume": vol.sum() - vol,
        "lm_group_iqr_z": np.subtract(*np.percentile(z, [75, 25])),
    }, index=g.index)


def build_peer_features(state):
    """Остальные A'->B в тот же день, без собственного ребра.

    Если остальные рёбра в тот же B тоже тормозят, проблема, вероятно, в B.
    """
    src = state.select(*KEYS, "shift_L7_z", "d3_14", "L14_srids").toPandas()
    src["prediction_day"] = pd.to_datetime(src["prediction_day"])
    peers = pd.concat([_peer_block(g) for _, g in src.groupby(NODE_DAY)])
    return src[KEYS].join(peers)

# собираем всё вместе
def build_feature_panel(raw, day_from, day_to, with_target):
    """Считаем агрегаты в Spark и собираем финальную таблицу в pandas."""
    state = build_edge_state(raw).filter(F.col("prediction_day").between(day_from, day_to)).cache()
    if with_target:
        panel = build_target(raw, day_from, day_to).join(state, KEYS)
    else:
        panel = state

    panel = panel.join(build_route1_features(raw), KEYS, "left").toPandas()
    if panel.empty:
        raise ValueError("Нет активных рёбер/размеченных записей за выбранные даты")
    panel["prediction_day"] = pd.to_datetime(panel["prediction_day"])
    days = panel["prediction_day"]
    nodes = panel["lm_osm_id"].unique()
    raw_b = raw.filter(F.col("lm_osm_id").isin(nodes.tolist()))

    return (
        panel
        .merge(build_pending_features(raw_b, nodes, days), on=NODE_DAY, how="left")
        .merge(build_peer_features(state), on=KEYS, how="left")
        .merge(build_queue_state(raw_b, nodes, days), on=NODE_DAY, how="left")
        .drop(columns=["p25", "p75", "last_fact_day", *[f"L{w}_h" for w in WINDOWS]])
        .sort_values(KEYS, ignore_index=True)
    )
