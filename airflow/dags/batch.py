from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import XCom, Variable
from datetime import datetime
from pathlib import Path
import requests
import openai
import boto3
import io
import re
import logging


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
    elif filename[-11:-4]=='Others':
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

    read_audio_task >> transcript_task >> save_task
