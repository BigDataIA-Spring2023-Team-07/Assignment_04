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

aws_access_key = Variable.get('AWS_ACCESS_KEY')
aws_secret_key = Variable.get('AWS_SECRET_KEY')
openai.api_key = Variable.get('OPENAI_API_KEY')
s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
bucket_name = 'damg7245-team7'


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 26),
    'retries': 1
}

# Task 1: reads an audio file from S3
def read_audio(**context):
    # s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    # bucket_name = 'damg7245-assignment-1'
    filename = context["dag_run"].conf["filename"]
    file_key = 'Adhoc/' + filename
    file = '/opt/airflow/working_dir/data/'+filename

    # Download audio file from S3
    s3.download_file(bucket_name, file_key, file)
    context['task_instance'].xcom_push(key='file_path', value = file)

# Task 2: sends the audio file to Whisper API for transcription
def transcribe_audio(**context):
    audio_file_path = context['task_instance'].xcom_pull(task_ids='read_audio', key='file_path')

    # print(audio_file_path)
    #print(input_data)
    input_data = open(audio_file_path,'rb')
    # Use the openai.Audio.transcribe() function to transcribe the audio file
    transcription = openai.Audio.transcribe(model="whisper-1", file=input_data, response_format='text')

    # Print the transcription to the console
    # print(transcription)

    context['task_instance'].xcom_push(key='transcription', value=transcription)

# Task 3: saves the transcript as a text file in S3
def save_transcript(**context):
    filename = context["dag_run"].conf["filename"]
    transcript = context['task_instance'].xcom_pull(task_ids='transcribe_audio', key='transcription')
    dot_pos = filename.rfind(".")
    outputFile = filename[:dot_pos] + "_transcript.txt"

    with open(outputFile, "w") as f:
        f.write(transcript)
        f.close()
   
    # Upload the string object to S3
    with open(outputFile, "rb") as f:
        s3.upload_fileobj(f, bucket_name, 'Processed_Folder/'+outputFile)

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
        reply, message_history = chat(file_content + question + "?", message_history)
        return reply, message_history


# Task 4: passes the transcript to GPT 3.5 Turbo model for processing
def process_transcript(**context):

    transcript = context['task_instance'].xcom_pull(task_ids='transcribe_audio', key='transcription')
    message_history = []

    question = "Can you summarize the meeting for me?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)

    question = "What was the main topic discussed in the meeting?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)

    question = "How was the tone of the meeting?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)

    question = "Are there any action items from the meeting that we need to follow up on?"
    # message_history.append({"role": "user", "content": f"{question}"})
    getdefaultquestion(question,transcript,message_history)



    # # Define the transcript and content of each question
    # message = [
    #     {"role": "user", "content": f"This is the meeting transcript.{transcript}"},
    #     {"role": "user", "content": "Can you summarize the meeting for me?"},
    #     {"role": "user", "content": "What was the main topic discussed in the meeting?"},
    #     {"role": "user", "content": "How was the tone of the meeting?"},
    #     {"role": "user", "content": "Are there any action items from the meeting that we need to follow up on?"},
    # ]

    # # Generate a chat response using the OpenAI API
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=message
    # )

    # # Grab just the text from the API completion response
    # reply_content = completion.choices[0].message.content


    # Push the generated response
    context['task_instance'].xcom_push(key='transcript', value=transcript)
    context['task_instance'].xcom_push(key='message_history', value=message_history)

    

# def send_to_streamlit(**context):
#     transcript = context['task_instance'].xcom_pull(task_ids='transcribe_audio', key='transcription')
#     context['task_instance'].xcom_push(key='transcript', value=transcript)
#     # requests.post('http://localhost:8501/transcript', data=transcript)
#     # url = 'http://34.148.127.152:8501/File_Upload'

#     # # url = "http://localhost:8501/get_transcript"
#     # data = {"transcript_id": "123"}

#     # response = requests.post(url, data=data)


# Defining the DAG
with DAG('audio_processing_dag', default_args=default_args, schedule_interval=None) as dag:

    read_audio = PythonOperator(
        task_id='read_audio',
        provide_context=True,
        python_callable=read_audio
    )

    transcribe_audio = PythonOperator(
        task_id='transcribe_audio',
        python_callable=transcribe_audio
    )

    save_transcript = PythonOperator(
        task_id='save_transcript',
        provide_context=True,
        python_callable=save_transcript
    )

    process_transcript = PythonOperator(
        task_id='process_transcript',
        python_callable=process_transcript
    )

    # Defining the task dependencies
    read_audio >> transcribe_audio >> save_transcript >> process_transcript
