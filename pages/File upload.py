import time
import streamlit as st
import boto3
import os
from dotenv import load_dotenv
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend import common_utils, chatgpt
import json

load_dotenv()


st.title("VaniVerse - Transcribing voice to words :page_with_curl:")

st.header("Select audio file to upload")

audio_file = st.file_uploader("Upload audio file (Limit 25Mb)", type=['mp4', 'mp3', 'wav'])

language = st.selectbox('Audio Language:', ['English', 'Otherss'])

if st.button("Submit"):
    if audio_file is None:
        st.error("Please upload the audio file")
    
    # check if the file is mp4
    elif (audio_file.name[-4:] != ".mp4") and (audio_file.name[-4:] != ".mp3") and (audio_file.name[-4:] != ".wav"):
            st.error("Please upload the audio file in mp4 format")  
    else:
        st.write("File name: ", audio_file.name)
        st.write("File size: ", audio_file.size/1048576 , "MB")
        st.write("Audio Language: ", language)
        if audio_file.size/1048576 > 25:
            st.error("File size should be less than 25MB")
        s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
        with st.spinner("Uploading file to S3"):
            # s3client.put_object(Bucket='damg7245-team7', Key= 'Adhoc/' + audio_file.name , Body=audio_file.read())
            audio_file_name= audio_file.name[:-4] + '_' + language + audio_file.name[-4:]
            common_utils.uploadfile(audio_file_name, audio_file.read(),'Adhoc')
            st.success("File uploaded to S3 successfully")

            # triggering the DAG
            response = common_utils.trigger_dag(audio_file_name)
            if response.status_code == 200:
                st.success('DAG triggered successfully')
            else:
                st.error(f'Error triggering DAG: {response.text}')




# Fetch files from S3 and store the filenames in a list
st.header("Which file do you want to generate prompts for? :three_button_mouse:")

file_list = chatgpt.getfilenames()
custom_qn = ""
# Display the list of files in a dropdown
file_selected = st.selectbox("Select a File :",np.unique(file_list))
st.write("You selected: ", file_selected)
            
st.header("Select a question from the list :grey_question:")
qn_selected = st.selectbox("Select a question", ["Can you summarize?", "What is the main topic?", "How is the tone?", "Custom"])

st.write("You selected: ", qn_selected)
if qn_selected == "Custom":
    custom_qn = st.text_input("Enter your question")

message_history = []
message_history.append({"role": "user", "content": f"{custom_qn}"})

def check_file_exists(file_name):
    s3client = common_utils.create_connection()
    bucket = os.environ.get('bucket_name')
    prefix = 'Message_History/'
    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix+file_name+'.json')
    if 'Contents' in response:
        return True
    else:
        return False

if st.button("Ask"):
    
    with st.spinner("Processing your request"):
        timeout=120
        start_time = time.time()
        while not(check_file_exists(file_selected)):
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                st.error("File not processed yet. Please try again later")
                break                
            time.sleep(5)
            
        # st.write('file processed')
    
    if qn_selected == "Custom":
        if len(custom_qn) == 0:
            st.error("Please enter a question")
        else:
            with st.spinner("Processing your request"):
                reply = chatgpt.getdefaultquestion(custom_qn, file_selected, message_history)
                if len(reply) == 0:
                    st.write("No response from the model. Please try again")
            
                else:
                    st.write("Answer:", reply)
                    s3client = common_utils.create_connection()
                    bucket = os.environ.get('bucket_name')
                    prefix = 'Message_History/'
                    response = s3client.list_objects_v2(Bucket=bucket, Prefix=prefix+file_selected+'.json')
                    
                    for obj in response['Contents']:
                        file_obj = s3client.get_object(Bucket=bucket, Key=obj['Key'])
                        file_content = file_obj['Body'].read().decode('utf-8')

                        # Decode the JSON content
                        data = json.loads(file_content)

                        # Add a new item to the 'message_history' list
                        new_item = {
                            "Question": custom_qn,
                            "Answer": reply,
                            "Type": "Custom"
                        }
                        data['message_history'].append(new_item)
                        new_content = json.dumps(data)

                        # Upload the modified file back to S3
                    s3client.delete_object(Bucket=bucket, Key=prefix+file_selected+'.json')    
                    s3client.put_object(Bucket=bucket, Key= obj['Key'], Body=new_content)
    else:
        s3client = common_utils.create_connection()        
        response = s3client.get_object(Bucket=os.environ.get('bucket_name'), Key= 'Message_History/' + file_selected+'.json')
        file_content = response['Body'].read().decode('utf-8')
        message_hist = json.loads(file_content)

        with st.spinner("Processing your request"):
            reply=""
            for message in message_hist['message_history']:
                if message['Question'] == qn_selected:
                    reply = message['Answer']
                    break
            if len(reply) == 0:
                st.write("No response from the model. Please try again")
            else:
                st.write("Answer:", reply)
