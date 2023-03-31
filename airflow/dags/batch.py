from airflow import DAG
from airflow.operators.python_operator import PythonOperator
# from airflow.providers.amazon.aws.operators.s3 import S3GetObjectOperator, S3CreateBucketOperator, S3DeleteObjectsOperator
from airflow.models import XCom, Variable
from datetime import datetime
import requests
import tiktoken
import openai
import boto3
import io
from pydub import AudioSegment
import json
from pathlib import Path
import os
import re
import logging


# create a logger object
logger = logging.getLogger()

# set the log level to INFO
logger.setLevel(logging.INFO)

aws_access_key = Variable.get('AWS_ACCESS_KEY')
aws_secret_key = Variable.get('AWS_SECRET_KEY')
openai.api_key = Variable.get('OPENAI_API_KEY')
bucket_name = Variable.get('bucket_name')


def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3: S3 client object
    """
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    return s3

def get_file_list():
    s3 = create_connection()
    prefix = 'Batch/'
    file_list = []

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    for obj in response['Contents']:
        file_name = obj['Key'][len(prefix):]
        if file_name != '':
            file_list.append(file_name)

    return file_list


def read_audio(filename,**context):
    s3 = create_connection()
    # filename = context["dag_run"].conf["filename"]
    file_key = 'Batch/' + filename
    file = '/opt/airflow/working_dir/data/'+filename

    # Download audio file from S3
    s3.download_file(bucket_name, file_key, file)
    context['task_instance'].xcom_push(key='file_path', value = file)

# Task 2: sends the audio file to Whisper API for transcription
def transcribe_audio(task_filename,**context):
    audio_file_path = context['task_instance'].xcom_pull(task_ids=f'read_audio_{task_filename}', key='file_path')
    input_data = open(audio_file_path,'rb')
    
    # Use the openai.Audio.transcribe() function to transcribe the audio file
    # transcription = openai.Audio.transcribe(model="whisper-1", file=input_data, response_format='text')
    filename=Path(audio_file_path).name
    if filename[-11:-4]=='English':
        transcription = openai.Audio.transcribe(model="whisper-1", file=input_data, response_format='text')
    elif filename[-11:-4]=='Otherss':
        transcription = openai.Audio.translate(model="whisper-1", file=input_data, response_format='text')

    # Print the transcription to the console
    # print(transcription)

    context['task_instance'].xcom_push(key='transcription', value=transcription)

# Task 3: saves the transcript as a text file in S3
def save_transcript(filename,task_filename,**context):
    s3 = create_connection()
    transcript = context['task_instance'].xcom_pull(task_ids=f'transcript_{task_filename}', key='transcription')
    dot_pos = filename.rfind(".")
    outputFile = filename[:dot_pos] + ".txt"

    with open(outputFile, "w") as f:
        f.write(transcript)
        f.close()
   
    # Upload the string object to S3
    with open(outputFile, "rb") as f:
        s3.upload_fileobj(f, bucket_name, 'Processed Text/'+outputFile)

def count_tokens(text):

    """Count the number of tokens in a text
    Args:
        text (str): Text to count tokens for
    Returns:
        num_tokens (int): Number of tokens in the text
    """
    encoding = tiktoken.get_encoding("gpt2")
    input_ids = encoding.encode(text)
    num_tokens = len(input_ids)
    return num_tokens

def break_up_file_to_chunks(text, chunk_size=2000, overlap=100):

    """Break up a text into chunks of a given size
    Args:
        text (str): Text to break up into chunks
        chunk_size (int): Size of each chunk defaults to 2000
        overlap (int): Number of tokens to overlap between chunks defaults to 100
    Returns:
        chunks (list): List of chunks
    """

    encoding = tiktoken.get_encoding("gpt2")


    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    
    chunks = []
    for i in range(0, num_tokens, chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks

def split_token_chat(text, question):

    """Split the text into chunks and call the chatgpt api
    Args:
        text (str): Text to be split into chunks
        question (str): Question to be asked to the chatgpt api
    Returns:
        reply (str): Reply from the chatgpt api
    """
    encoding = tiktoken.get_encoding("gpt2")
    chunks = break_up_file_to_chunks(text)

    prompt_response = []
    messages = [] 

    for i, chunk in enumerate(chunks):
        prompt_request = question + "?" + encoding.decode(chunks[i])
        messages.append({"role": "user", "content": prompt_request})

        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=.5,
                max_tokens=500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
        )
        
        prompt_response.append(response["choices"][0]["message"]['content'].strip())

    prompt_request = "Can you consoloidate this text ?" + str(prompt_response)

    response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt_request,
            temperature=.5,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0)

    meeting_summary = response["choices"][0]["text"].strip()
    return meeting_summary, messages

def chat(inp, message_history, role="user"):

    """Question to be asked to the chatgpt api
    Args:
        inp (str): Input from the user
        message_history (list): Message history
        role (str): Role of the user
    Returns:
        reply (str): Reply from the chatgpt api
    """

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
    return reply_content, message_history

def save_message_history(message_history,filename):
    final_json = {}
    my_json = {}
    my_list=[]
    
    for message_id, message in enumerate(message_history):
        if message['role']=='user':
            my_json["Question"] = str(message['content'].split('\n')[1])
            my_json["Answer"] = message_history[message_id+1]['content']
            my_json["Type"] = 'Default'
            my_list.append(my_json)
            my_json={}

    final_json['message_history'] = my_list
    json_string = json.dumps(final_json)

    json_file_name = filename.split('.')[0] + '.json'

    s3 = create_connection()
    folder_name = 'Message_History'
    s3.put_object(Bucket=bucket_name, Key=f'{folder_name}/{json_file_name}', Body=json_string)

def getdefaultquestion(question, transcript, message_history):

    """
    Args:
        question (str): Default Question
        selected_file (str): Selected file from the user
        message_history (list): Message history
    Returns:
        reply (str): Reply from the chatgpt api
        
    """

    file_content = transcript

    num_tokens = count_tokens(file_content)
    if num_tokens > 2000:
        reply, message_history = split_token_chat(file_content, question)
        return reply, message_history
    else:
        reply, message_history = chat(file_content + question, message_history)
        return reply, message_history


# Task 4: passes the transcript to GPT 3.5 Turbo model for processing
def process_transcript(filename,task_filename,**context):

    transcript = context['task_instance'].xcom_pull(task_ids=f'transcript_{task_filename}', key='transcription')
    message_history = []

    question = "Can you summarize?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)

    question = "What is the main topic?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)

    question = "How is the tone?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)

    #Save message history to S3
    
    save_message_history(message_history,filename)



default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 3, 28, 3, 0, 0),
}

dag = DAG('audio_processing_batch_dag', default_args=default_args, schedule_interval='0 3 * * *')

file_list = get_file_list()

for filename in file_list:

    task_filename = re.sub(r'[^\w.-]', '_', filename)

    read_audio_task = PythonOperator(
        task_id='read_audio_{}'.format(task_filename),
        python_callable=read_audio,
        op_kwargs={'filename': filename},
        dag=dag
    )

    transcript_task = PythonOperator(
        task_id='transcript_{}'.format(task_filename),
        python_callable=transcribe_audio,
        op_kwargs={'task_filename': task_filename},
        dag=dag
    )

    save_task = PythonOperator(
        task_id='save_{}'.format(task_filename),
        python_callable=save_transcript,
        op_kwargs={'filename': filename,'task_filename': task_filename},
        dag=dag
    )
    
    process_transcript_task = PythonOperator(
        task_id='process_transcript_{}'.format(task_filename),
        python_callable=process_transcript,
        op_kwargs={'filename': filename,'task_filename': task_filename},
        dag=dag
    )

    read_audio_task >> transcript_task >> save_task >> process_transcript_task
