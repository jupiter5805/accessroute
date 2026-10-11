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

    data_quality = BashOperator(
        task_id="data_quality",
        bash_command=(
            f"cd {PROJECT} && "
            f"{PYTHON} -m src.accessroute.quality"
        ),
        env=ENV,
        append_env=True,
    )

    setup_database >> ingest_openstreetmap >> enrich_elevation >> data_quality
