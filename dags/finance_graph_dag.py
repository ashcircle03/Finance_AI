
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add src to path just in case, though PYTHONPATH should handle it
sys.path.append('/opt/airflow')

from src.etl_pipeline import run_stock_pipeline

default_args = {
    'owner': 'fingraph',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'finance_graph_etl',
    default_args=default_args,
    description='Fetches Stock and News data, extracts signals, and loads to Neo4j',
    schedule_interval='*/30 * * * *', # Run every 30 mins
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['finance', 'gemini', 'neo4j'],
) as dag:

    etl_task = PythonOperator(
        task_id='run_etl_pipeline',
        python_callable=run_stock_pipeline,
    )

    etl_task
