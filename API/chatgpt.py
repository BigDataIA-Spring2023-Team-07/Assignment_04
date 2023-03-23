from fastapi import APIRouter, Response, status
import boto3
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import openai


load_dotenv()


router = APIRouter()

class Default_qn(BaseModel):
    question: str
    file_name: str

def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY1'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY1'))
    return s3client



@router.post("/getdefaultquestion")
async def getdefaultquestion(default_qn: Default_qn):


    file_list = []
    s3client = create_connection()
    bucket = 'damg7245-team7'
    prefix = 'Processed Text/'

    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix)

    for obj in response['Contents']:
        file_name = obj['Key'][len(prefix):]
        if file_name != '':
            file_list.append(file_name)

    file_list = [val.split(".")[0] for val in file_list]

    if default_qn.file_name in file_list:
        # Fetch transcript from S3
        bucket_name = 'damg7245-team7'
        file_path = 'Processed Text/' + default_qn.file_name + '.txt'

        # Fetch the file content from S3
        response = s3client.get_object(Bucket=bucket_name, Key=file_path)

        # Read the contents of the file
        file_content = response['Body'].read().decode('utf-8')

        # Provide the content to chatgpt api
        openai.api_key = os.environ.get('OPENAI_API_KEY')







