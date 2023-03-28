import os
import openai
from dotenv import load_dotenv
import tiktoken
from backend import common_utils

load_dotenv()



def getfilenames():

    """Get the list of files from S3 bucket
    Returns:
        file_list (list): List of files stored in S3 bucket
    """

    file_list = []
    s3client = common_utils.create_connection()
    bucket = os.environ.get('bucket_name')
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

def getdefaultquestion(question, selected_file, message_history):

    """Get the question from the user
    Args:
        question (str): Question from the user
        selected_file (str): Selected file from the user
        message_history (list): Message history
    Returns:
        reply (str): Reply from the chatgpt api
        
    """

    file_list = []
    s3client = common_utils.create_connection()
    bucket = os.environ.get('bucket_name')
    prefix = 'Processed Text/'


    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix)

    for obj in response['Contents']:
        file_name = obj['Key'][len(prefix):]
        if file_name != '':
            file_list.append(file_name)

    file_list = [val.split(".")[0] for val in file_list]

    if selected_file in file_list:
        # Fetch transcript from S3
        bucket_name = os.environ.get('bucket_name')
        file_path = 'Processed Text/' + selected_file + '.txt'
        # Fetch the file content from S3
        response = s3client.get_object(Bucket=bucket_name, Key=file_path)

        # Read the contents of the file
        file_content = response['Body'].read().decode('utf-8')


        # Provide the content to chatgpt api
        openai.api_key = os.environ.get('OPENAI_API_KEY')

        num_tokens = count_tokens(file_content)
        if num_tokens > 2000:
            reply, message_history = split_token_chat(file_content, question)
            return reply
        else:
            reply, message_history = chat(file_content + question + "?", message_history)
            return reply
    

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
    return reply_content

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
