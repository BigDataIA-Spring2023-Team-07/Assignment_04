import boto3
import os
import openai
from dotenv import load_dotenv
import tiktoken
from backend import common_utils

load_dotenv()

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

    # Return the generated response
    return reply_content



def getdefaultquestion(question, selected_file, message_history):

    file_list = []
    s3client = common_utils.create_connection()
    bucket = 'damg7245-team7'
    prefix = 'Processed Text/'


    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix)

    for obj in response['Contents']:
        file_name = obj['Key'][len(prefix):]
        if file_name != '':
            file_list.append(file_name)

    file_list = [val.split(".")[0] for val in file_list]




    if selected_file in file_list:
        # Fetch transcript from S3
        bucket_name = 'damg7245-team7'
        file_path = 'Processed Text/' + selected_file + '.txt'
        # Fetch the file content from S3
        response = s3client.get_object(Bucket=bucket_name, Key=file_path)

        # Read the contents of the file
        file_content = response['Body'].read().decode('utf-8')


        # Provide the content to chatgpt api
        openai.api_key = os.environ.get('OPENAI_API_KEY')

       

    

        reply = chat(file_content + question + "?", message_history)
        return reply, message_history
    

def getfilenames():

    file_list = []
    s3client = common_utils.create_connection()
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

    return file_list

def count_tokens(text):
    encoding = tiktoken.get_encoding("gpt2")
    input_ids = encoding.encode(text)
    num_tokens = len(input_ids)
    return num_tokens

def break_up_file_to_chunks(filename, chunk_size=2000, overlap=100):

    encoding = tiktoken.get_encoding("gpt2")
    with open(filename, 'r') as f:
        text = f.read()

    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    
    chunks = []
    for i in range(0, num_tokens, chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks
