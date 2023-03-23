from fastapi import Response, status
from fastapi.responses import JSONResponse
import boto3
import os
from dotenv import load_dotenv
from fastapi import FastAPI


load_dotenv()

from API.chatgpt import router as chatgpt_router

app = FastAPI()
app.include_router(chatgpt_router)

def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY1'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY1'))
    return s3client



@app.get("/getfilenames")
async def getfilenames():

    file_list = []
    s3client = create_connection()
    bucket = 'damg7245-team7'
    prefix1 = 'Adhoc/'
    prefix2 = 'Batch/'


    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix1)

    for obj in response['Contents']:
        file_name = obj['Key'][len(prefix1):]
        if file_name != '':
            file_list.append(file_name)

    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix2)

    for obj in response['Contents']:
        file_name = obj['Key'][len(prefix2):]
        if file_name != '':
            file_list.append(file_name)

    file_list = [val.split(".")[0] for val in file_list]
    # file_list.remove('Adhoc/')
    # file_list.remove('Batch/')

    return {"filenames": file_list}
    




    