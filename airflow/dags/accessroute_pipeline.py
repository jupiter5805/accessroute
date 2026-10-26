from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT = "/opt/accessroute"
PYTHON = "/home/airflow/accessroute-venv/bin/python"

ENV = {
    "DATABASE_URL": (
        "postgresql+psycopg://"
        "accessroute:accessroute_dev@"
        "postgres:5432/accessroute"
    )
}


with DAG(
    dag_id="accessroute_pipeline",
    description="Build and validate the AccessRoute geospatial routing dataset",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["accessroute", "geospatial", "data-engineering"],
) as dag:

    setup_database = BashOperator(
        task_id="setup_database",
        bash_command=(
            f"cd {PROJECT} && "
            f"{PYTHON} -m src.accessroute.database.setup"
        ),
        env=ENV,
        append_env=True,
    )

    ingest_openstreetmap = BashOperator(
        task_id="ingest_openstreetmap",
        bash_command=(
            f"cd {PROJECT} && "
            f"{PYTHON} -m src.accessroute.ingestion.osm"
        ),
        env=ENV,
        append_env=True,
    )

    enrich_elevation = BashOperator(
        task_id="enrich_elevation",
        bash_command=(
            f"cd {PROJECT} && "
            f"{PYTHON} -m src.accessroute.ingestion.elevation"
        ),
        env=ENV,
        append_env=True,
    )

    train_ml_model = BashOperator(
    task_id="train_ml_model",
    bash_command=f"{PYTHON} -m src.accessroute.ml.train",
    cwd=PROJECT,
    env=ENV,
)


score_network_ml = BashOperator(
    task_id="score_network_ml",
    bash_command=(
        f"{PYTHON} "
        "-m src.accessroute.ml.score_network"
    ),
    cwd=PROJECT,
    env=ENV,
)

data_quality = BashOperator(
        task_id="data_quality",
        bash_command=(
            f"cd {PROJECT} && "
            f"{PYTHON} -m src.accessroute.quality"
        ),
        env=ENV,
        append_env=True,
    )

    setup_database >> ingest_openstreetmap >> enrich_elevation >> data_quality >> train_ml_model >> score_network_ml
