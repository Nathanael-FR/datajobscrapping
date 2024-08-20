import sys
import os


# Import internal modules
from utils.postgres import get_conn, insert_job_offer
from utils.s3 import connect_to_s3, download_csv_files, create_df, remove_tmp_folder
from utils.models import JobItemProcessed
from utils.logger import Logger

# Importing required modules
from datetime import datetime, timedelta
from airflow.decorators import task
from airflow.operators.python import PythonOperator
from airflow import DAG

log_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime("%Y-%m-%d")
logger = Logger(f"etl_test_{today}.log").get_logger()

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
    schedule='0 8 * * *',  # This cron expression means every day at 8 AM
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['etl', 'job_offers'],
) as dag:

    @task()
    def extract_from_s3():
        s3 = connect_to_s3()
        if s3:
            download_csv_files(s3)
            logger.info("task (1/3) completed - Extracted data from S3")

    @task()
    def transform_data():
        df = create_df()
        df["publication_date"].apply(
            lambda x: datetime.strptime(x, '%d/%m/%Y').strftime('%Y-%m-%d'))

        logger.info("task (2/3) completed - Transformed data")
        return df

    @task()
    def load_data(df):
        conn = get_conn()
        if conn:
            for _, row in df.iterrows():
                job_offer: dict = row.to_dict()
                job = JobItemProcessed(**job_offer)
                insert_job_offer(conn, job)
            conn.close()
            logger.info("task (3/3) completed - Loaded data into the database")

    # Defining the task dependencies
    extract_task = extract_from_s3()
    transform_task = transform_data()
    load_task = load_data(transform_task)

    extract_task >> transform_task >> load_task


if __name__ == "__main__":
    dag.test()
