# Выгрузка событий посылок из ClickHouse
# Интервал date_from, date_to (включительно)
# Выход: Spark DataFrame, одна строка на SRID, OSM/офисы и времена событий
# Берём объект, если хотя бы одно событие попало в окно; из дублей выбираем
# наиболее продвинутую запись по timestamp_lm -> timestamp_src -> timestamp_created, затем проверяем порядок событий

import os
from datetime import date, timedelta

from pyspark.sql import Window, functions as F

TIMESTAMPS = ("timestamp_created", "timestamp_src", "timestamp_lm")


def canonicalize(events):
    t0, t1, t2 = (F.col(name) for name in TIMESTAMPS)
    latest = Window.partitionBy("srid").orderBy(
        t2.desc_nulls_last(), t1.desc_nulls_last(), t0.desc_nulls_last()
    )
    in_order = (
        F.coalesce(t0 <= t1, F.lit(True))
        & F.coalesce(t1 <= t2, F.lit(True))
        & F.coalesce(t0 <= t2, F.lit(True))
    )
    return (
        events
        .withColumn("version", F.row_number().over(latest))
        .filter("version = 1")
        .drop("version")
        .filter(t0.isNotNull() & in_order)
    )


def collect_events(spark, date_from: date, date_to: date):
    """Возвращает Spark DataFrame; вычисление ленивое, промежуточных файлов нет."""
    lo, hi = date_from, date_to + timedelta(days=1)
    query = f"""
        SELECT srid, src_osm_id, lm_osm_id, src_office_id, lm_office_id,
               toUnixTimestamp(timestamp_created) AS timestamp_created,
               toUnixTimestamp(timestamp_src) AS timestamp_src,
               toUnixTimestamp(timestamp_lm) AS timestamp_lm
        FROM wbx_data_mart.srids_dist
        WHERE (
             (timestamp_created >= toDateTime('{lo}', 'UTC') AND timestamp_created < toDateTime('{hi}', 'UTC'))
          OR (timestamp_src >= toDateTime('{lo}', 'UTC') AND timestamp_src < toDateTime('{hi}', 'UTC'))
          OR (timestamp_lm >= toDateTime('{lo}', 'UTC') AND timestamp_lm < toDateTime('{hi}', 'UTC'))
        )
          AND delivery_type IN ('FBS', 'WH') AND src_osm_id != 0 AND lm_osm_id != 0
    """

    raw = (
        spark.read.format("jdbc")
        .option("driver", "com.clickhouse.jdbc.ClickHouseDriver")
        .option("url", os.environ["CLICKHOUSE_JDBC_URL"])
        .option("user", os.environ["CLICKHOUSE_USER"])
        .option("password", os.environ["CLICKHOUSE_PASSWORD"])
        .option("query", query)
        .load()
    )
    events = raw.select(
        "srid", "src_osm_id", "lm_osm_id", "src_office_id", "lm_office_id",
        *[F.when(F.col(name) > 0, F.timestamp_seconds(name)).alias(name) for name in TIMESTAMPS],
    )
    return canonicalize(events)
