from fastapi import APIRouter, Response, status
import boto3
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import openai
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.common_utils import create_connection


load_dotenv()


router = APIRouter()

class Default_qn(BaseModel):
    question: str
    file_name: str
    message_history: list



def chat(inp, message_history, role="user"):

    # Append the input message to the message history
    message_history.append({"role": role, "content": f"{inp}"})

    # Generate a chat response using the OpenAI API
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_history
    )

    # Grab just the text from the API completion response
    reply_content = completion.choices[0].message.content

    # Append the generated response to the message history
    message_history.append({"role": "assistant", "content": f"{reply_content}"})

    # Return the generated response and the updated message history
    return reply_content, message_history



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
        
        reply, default_qn.message_history = chat(file_content + default_qn.question + "?", default_qn.message_history)
        return {"reply": reply, "message_history": default_qn.message_history}






