from fastapi import Response, status
from fastapi.responses import JSONResponse
import boto3
import os
from dotenv import load_dotenv
from fastapi import FastAPI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.common_utils import create_connection


load_dotenv()

from API.chatgpt import router as chatgpt_router

app = FastAPI()
app.include_router(chatgpt_router)



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
    




    