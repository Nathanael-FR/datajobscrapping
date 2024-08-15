import boto3
import os
import pandas as pd
from datetime import datetime
from utils.logger import Logger

today = datetime.now().strftime("%Y-%m-%d")
logger = Logger(f"etl_test_{today}.log").get_logger()


 


def connect_to_s3():

    try:
        session = boto3.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    except Exception as e:
        logger.error(f'Error while connecting to S3: {e}')
        return None
    else:
        logger.info("Connected to S3")
        return session.client("s3")


def download_csv_files(s3) -> None:

    bucket_name = os.environ["S3_BUCKET"]
    local_folder = os.path.join(os.getcwd(), "tmp")
    s3_folder = "data//"

    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
        logger.info(f"Created folder {local_folder}")

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_folder)

    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.csv'):
            logger.info(f"Downloading {obj['Key']} to {local_folder}")
            local_path = os.path.join(
                local_folder, os.path.basename(obj['Key']))
            s3.download_file(bucket_name, obj['Key'], local_path)
            logger.info(f"Downloaded {obj['Key']} to {local_path}")
            break  # We only need one file


def create_df() -> pd.DataFrame:
    """ return a pandas dataframe from the csv files """
    dir = os.path.join(os.getcwd(), "tmp")
    # Get all the absolute paths of the csv files
    csv_files = [os.path.join(dir, f)
                 for f in os.listdir(dir) if f.endswith('.csv')]
    logger.info(f"Creating dataframe from csv files: {csv_files}")
    return pd.concat(map(pd.read_csv, csv_files))



def remove_tmp_folder() -> None:
    import shutil
    shutil.rmtree(os.path.join(os.getcwd(), "tmp"))
    logger.info("Removed tmp folder")


if __name__ == "__main__":
    s3: boto3.client = connect_to_s3()
    if s3:
        download_csv_files(s3)
        df = create_df()
        print(df.tail())
        remove_tmp_folder()
