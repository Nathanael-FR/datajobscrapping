from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
from datetime import datetime
from datetime import timedelta
import pandas as pd


from src.utils import connect_to_s3, download_csv_files, create_df, remove_tmp_folder

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}


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
    ...
