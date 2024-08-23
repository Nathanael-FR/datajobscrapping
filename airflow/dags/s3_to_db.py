import os
from utils.postgres import get_conn, insert_job_offer
from utils.s3 import connect_to_s3, download_csv_files, create_df, remove_tmp_folder
from utils.models import JobItemProcessed
from datetime import datetime, timedelta
from airflow.decorators import task
from airflow.operators.python import PythonOperator
from airflow import DAG
from airflow.exceptions import AirflowFailException

# Import internal modules

# Importing required modules

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
    schedule='0 6 * * *',  # This cron expression means every day at midnight
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['etl', 'job_offers'],
) as dag:

    @task()
    def extract_from_s3():
        try:
            s3 = connect_to_s3()
            if s3:
                download_csv_files(s3)
                print("task (1/3) completed - Extracted data from S3")
            else:
                print("task (1/3) failed - Could not connect to S3")
                raise AirflowFailException("Could not connect to S3")
        except Exception as e:
            print(f"task (1/3) failed - {e}")
            raise AirflowFailException(e)

    @task()
    def transform_data():
        try:
            df = create_df()
            print("task (2/3) completed - Transformed data")
            return df
        except Exception as e:
            print(f"task (2/3) failed - Exception: {str(e)}")
            raise AirflowFailException(f"Error in transform_data: {str(e)}")

    @task()
    def load_data(df):
        try:
            conn = get_conn()
            if conn:
                for _, row in df.iterrows():
                    try:
                        job_offer = row.to_dict()
                        job = JobItemProcessed(**job_offer)
                        insert_job_offer(conn, job)
                    except Exception as e:
                        raise AirflowFailException(
                            f"Error inserting job offer: {job.__str__()} : {str(e)}")
                conn.close()
                print("task (3/3) completed - Loaded data into the database")
            else:
                raise AirflowFailException("Could not connect to the database")
        except Exception as e:
            raise AirflowFailException(f"Error in load_data: {str(e)}")

    # Defining the task dependencies
    extract_task = extract_from_s3()
    transform_task = transform_data()
    load_task = load_data(transform_task)

    extract_task >> transform_task >> load_task


if __name__ == "__main__":
    dag.test()
