import streamlit as st
import boto3
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend import common_utils

load_dotenv()


st.title("Model as a Service - Meeting Summary :page_with_curl:")

# Mutiple file upload
uploaded_files = st.file_uploader("Upload audio files", type=['mp4', 'mp3'], accept_multiple_files=True)

if st.button("Submit"):
    if uploaded_files is None:
        st.error("Please upload the audio file")

    for uploaded_file in uploaded_files:
        # check if the file is mp4 or mp3
        if uploaded_file.name[-4:] != ".mp4" and uploaded_file.name[-4:] != ".mp3":
            st.error("Please upload the audio file in mp4 format")  

        else:
            st.write("File name: ", uploaded_file.name)
            st.write("File size: ", uploaded_file.size/1048576 , "MB")
            s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY1'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY1'))
            with st.spinner("Uploading file to S3"):
                for audio_file in uploaded_files:
                    # s3client.put_object(Bucket='damg7245-team7', Key= 'Batch/' + audio_file.name , Body=audio_file.read())
                    common_utils.uploadfile(audio_file.name, audio_file.read())
            st.success("File uploaded to S3 successfully")



