"""Ежедневный прогноз Route2 по офисам."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow_utils.v2 import SparkConfig, SparkSubmitOperator

spark_conf = (
    SparkConfig(image=Variable.get("route2_spark_image"))
    .set_resources(executor_memory="12g", executor_cores=4, max_executors=10, driver_memory="16g")
    .add_jars([Variable.get("route2_clickhouse_jar")])
)

files_envs = {
    "CLICKHOUSE_JDBC_URL": "jdbc:clickhouse:https://{{ conn.route2_clickhouse.host }}:{{ conn.route2_clickhouse.port }}/{{ conn.route2_clickhouse.schema }}?ssl=true&sslmode=none",
    "CLICKHOUSE_USER": "{{ conn.route2_clickhouse.login }}",
    "CLICKHOUSE_PASSWORD": "{{ conn.route2_clickhouse.password }}",
}

with DAG(
    dag_id="route2_predict",
    start_date=datetime(2026, 9, 1),
    schedule_interval="0 4 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["spark", "route2"],
) as dag:
    predict = SparkSubmitOperator(
        name="route2_predict",
        application="jobs/route2_job.py",
        conf=spark_conf,
        application_args=[
            "--mode", "predict", "--run-day", "{{ data_interval_end | ds }}",
            "--model-dir", "{{ var.value.route2_model_hdfs_dir }}",
            "--iceberg-namespace", "{{ var.value.route2_iceberg_namespace }}",
        ],
        files_envs=files_envs,
    )
