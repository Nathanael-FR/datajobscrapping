import boto3
import os
from dotenv import load_dotenv

load_dotenv()

session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

client = session.client('s3')

# Load the csv file into the S3 bucket
client.upload_file('job_offers.csv', 'jobscrappingbucket', 'job_offers.csv')

