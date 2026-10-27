"""Один Spark job на DAG: чтение -> признаки -> обучение или прогноз."""

import argparse
import io
import subprocess
from datetime import date, datetime, timedelta, timezone

import joblib
from pyspark.sql import SparkSession, functions as F

from collect_route2_data import collect_events
from route2_core import FEATURE_HISTORY_DAYS, predict_models, target_window, train_models
from route2_features import build_feature_panel


def hdfs(*args, data=None):
    return subprocess.run(["hdfs", "dfs", *args], input=data, capture_output=True, check=True).stdout


def save_model(model_dir, day, artifact):
    buffer = io.BytesIO()
    joblib.dump(artifact, buffer)
    hdfs("-mkdir", "-p", model_dir)
    path = f"{model_dir.rstrip('/')}/{day}.joblib"
    hdfs("-put", "-f", "-", path, data=buffer.getvalue())
    return path


def load_model(model_dir, day):
    files = hdfs("-ls", "-C", model_dir).decode().splitlines()
    candidates = [path for path in files if path.endswith(".joblib")]
    candidates = [path for path in candidates if path.rsplit("/", 1)[-1][:10] <= day.isoformat()]
    if not candidates:
        raise FileNotFoundError(f"В HDFS нет модели на дату {day} или раньше: {model_dir}")
    path = max(candidates)
    return joblib.load(io.BytesIO(hdfs("-cat", path))), path


def write_predictions(spark, office_map, counts, preds, name, day, namespace):
    """Прогноз OSM -> офисы; полная замена текущих таблиц Iceberg."""
    model_df = spark.createDataFrame(preds)
    result = (
        model_df.join(office_map, ["src_osm_id", "lm_osm_id"], "inner")
        .join(counts, ["src_office_id", "lm_office_id"], "left")
        .select(
            F.xxhash64(F.lit(day), "src_office_id", "lm_office_id").alias("id"),
            F.col("src_office_id").cast("int").alias("src_office_id"),
            F.col("lm_office_id").cast("int").alias("lm_office_id"),
            F.coalesce(F.col("count"), F.lit(0)).cast("bigint").alias("count"),
            F.col("duration").cast("double"),
        )
    )
    table = f"{namespace}.t2_{name}"
    spark.sql(f"""CREATE TABLE IF NOT EXISTS {table} (
        id BIGINT, src_office_id INT, lm_office_id INT, `count` BIGINT, duration DOUBLE
    ) USING iceberg""")
    # Iceberg атомарно заменяет содержимое таблицы на прогноз только за день D.
    result.writeTo(table).option("snapshot-property.route2_day", day.isoformat()).overwrite(F.lit(True))


def predict(spark, raw, df, model_dir, namespace, day):
    today = datetime.now(timezone.utc).date()
    if day != today:
        raise ValueError(f"Прогноз за {day} не записан: сегодня UTC {today}")

    artifact, model_path = load_model(model_dir, day)
    print(f"Route2: используем модель {model_path}")

    office_map = (
        raw.filter((F.col("src_office_id") > 0) & (F.col("lm_office_id") > 0))
        .select("src_osm_id", "lm_osm_id", "src_office_id", "lm_office_id")
        .distinct()
    )
    if office_map.groupBy("src_office_id", "lm_office_id").count().filter("count > 1").limit(1).count():
        raise ValueError("Несколько OSM-пар соответствуют одной офисной паре")

    counts = (
        raw.filter(
            (F.col("timestamp_src").isNotNull())
            & (F.col("timestamp_lm") >= F.lit(day - timedelta(days=14)).cast("timestamp"))
            & (F.col("timestamp_lm") < F.lit(day).cast("timestamp"))
        )
        .groupBy("src_office_id", "lm_office_id")
        .agg(F.count("srid").alias("count"))
        .cache()
    )
    for name, preds in predict_models(df, artifact):
        write_predictions(spark, office_map, counts, preds, name, day, namespace)
        print(f"Route2: записана {namespace}.t2_{name}")


def run(mode, day, model_dir, namespace):
    spark = SparkSession.builder.appName(f"route2_{mode}_{day}").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    try:
        day_from, day_to = target_window(day) if mode == "train" else (day, day)
        raw = collect_events(spark, day_from - timedelta(days=FEATURE_HISTORY_DAYS), day).cache()
        df = build_feature_panel(raw, day_from, day_to, with_target=(mode == "train"))
        if mode == "train":
            print("Route2: модель сохранена", save_model(model_dir, day, train_models(df)))
        else:
            predict(spark, raw, df, model_dir, namespace, day)
    finally:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "predict"], required=True)
    parser.add_argument("--run-day", type=date.fromisoformat, required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--iceberg-namespace", required=True)
    args = parser.parse_args()
    run(args.mode, args.run_day, args.model_dir, args.iceberg_namespace)
