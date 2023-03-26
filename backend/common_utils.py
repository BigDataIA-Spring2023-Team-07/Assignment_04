import boto3
import os
import openai
from dotenv import load_dotenv

load_dotenv()



def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY1'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY1'))
    return s3client


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



def getdefaultquestion(question, selected_file, message_history):

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

        
        reply, message_history = chat(file_content + question + "?", message_history)
        return reply, message_history
    

def getfilenames():

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

    return file_list


def uploadfile(file_name, file_content):

    s3client = create_connection()
    s3client.put_object(Bucket='damg7245-team7', Key= 'Adhoc/' + file_name , Body= file_content)

