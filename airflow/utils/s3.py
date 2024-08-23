import boto3
import os
import pandas as pd
from datetime import datetime


def connect_to_s3() -> boto3.client:

    try:
        session = boto3.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name="us-east-1"
        )
    except Exception as e:
        raise e
    else:
        print("Connected to S3")
        return session.client("s3")


def download_csv_files(s3) -> None:

    bucket_name = os.environ["S3_BUCKET"]
    local_folder = os.path.join(os.getcwd(), "tmp")
    s3_folder = "data/"

    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
        print(f"Created {local_folder}")

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_folder)
    print(f"Downloading csv files from {bucket_name}/{s3_folder}")

    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.csv'):
            print(f"Downloading {obj['Key']} to {local_folder}")
            local_path = os.path.join(
                local_folder, os.path.basename(obj['Key']))
            s3.download_file(bucket_name, obj['Key'], local_path)
            print(f"Downloaded {obj['Key']} to {local_path}")


def create_df() -> pd.DataFrame:
    """ return a pandas dataframe from the csv files """
    dir = os.path.join(os.getcwd(), "tmp")
    # Get all the absolute paths of the csv files
    csv_files = [os.path.join(dir, f)
                 for f in os.listdir(dir) if f.endswith('.csv')]
    print(f"Creating dataframe from csv files: {csv_files}")
    return pd.concat(map(pd.read_csv, csv_files))


def remove_tmp_folder() -> None:
    import shutil
    shutil.rmtree(os.path.join(os.getcwd(), "tmp"))
    print("Removed tmp folder")


if __name__ == "__main__":
    s3: boto3.client = connect_to_s3()
    if s3:
        download_csv_files(s3)
        df = create_df()
        print(df.tail())
        remove_tmp_folder()
