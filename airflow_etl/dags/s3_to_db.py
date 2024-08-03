import pandas as pd
from datetime import datetime, timedelta
from airflow.decorators import task
from airflow.operators.python import PythonOperator
from airflow import DAG
from scrapping.src.models import JobItemProcessed
from airflow_etl.src.utils import connect_to_s3, download_csv_files, create_df, remove_tmp_folder
from airflow_etl.src.postgres import get_conn, insert_job_offer
import sys
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'daily_etl_job_offers',
    default_args=default_args,
    description='A simple ETL pipeline for job offers',
    schedule_interval='0 8 * * *',  # This cron expression means every day at 8 AM
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['etl', 'job_offers'],
) as dag:

    @task()
    def extract_from_s3():
        s3 = connect_to_s3()
        if s3:
            download_csv_files(s3)
            return True
        return False

    @task()
    def transform_data():
        df = create_df()
        return df

    @task()
    def load_data(df):
        conn = get_conn()
        if conn:
            for _, row in df.iterrows():
                job_offer: dict = row.to_dict()
                try:
                    job = JobItemProcessed(**job_offer)
                    insert_job_offer(conn, job)
                except Exception as e:
                    print(e)
            return True
        return False

    # Defining the task dependencies
    extract_task = extract_from_s3()
    transform_task = transform_data()
    load_task = load_data(transform_task)

    extract_task >> transform_task >> load_task
