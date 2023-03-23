import boto3
import os
from dotenv import load_dotenv

load_dotenv()



def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY1'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY1'))
    return s3client