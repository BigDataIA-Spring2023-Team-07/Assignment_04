import base64
import requests
import streamlit as st
import boto3
import os
from dotenv import load_dotenv
import numpy as np

load_dotenv()


st.title("Model as a Service - Meeting Summary :page_with_curl:")

st.header("Please upload the audio file :mega:")

audio_file = st.file_uploader("Upload audio file", type=['mp4', 'mp3'])


if st.button("Submit"):
    if audio_file is None:
        st.error("Please upload the audio file")
    
    
    # check if the file is mp4
    elif (audio_file.name[-4:] != ".mp4") and (audio_file.name[-4:] != ".mp3"):
            st.error("Please upload the audio file in mp4 format")  
    else:
        st.write("File name: ", audio_file.name)
        st.write("File size: ", audio_file.size/1048576 , "MB")
        s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY1'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY1'))
        with st.spinner("Uploading file to S3"):
            s3client.put_object(Bucket='damg7245-team7', Key= 'Adhoc/' + audio_file.name , Body=audio_file.read())
            st.success("File uploaded to S3 successfully")




# Fetch files from S3 and store the filenames in a list
st.header("Select a file from the list")
FAST_API_URL = "http://localhost:8000/getfilenames"
response = requests.get(FAST_API_URL)
file_list = response.json()['filenames']

# Display the list of files in a dropdown
file_selected = st.selectbox("Select a file", np.unique(file_list))
st.write("You selected: ", file_selected)




# Select the qn from dropdown list
st.header("Select a question from the list")
qn_selected = st.selectbox("Select a question", ["Can you summarize the meeting?", "What is the meeting about?", "How was the tone of the meeting?", "Question4", "Custom"])

# if qn_selected == "Custom":
#     qn_selected = st.text_input("Enter your question")

st.write("Your Question: ", qn_selected)

if st.button("Process"):
     FASTAPI_URL = "http://localhost:8000/getdefaultquestion"
     response = requests.post(FASTAPI_URL, json={"question": qn_selected, "file_name": file_selected})

