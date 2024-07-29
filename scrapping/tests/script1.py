import os

print(len(os.environ))
print(os.environ['AWS_ACCESS_KEY_ID'])
print(os.environ['AWS_SECRET_ACCESS_KEY'])
print(os.environ['S3_BUCKET_NAME'])
