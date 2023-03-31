import streamlit as st
import boto3
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend import common_utils

load_dotenv()


st.title("VaniVerse - Transcribing voice to words :page_with_curl:")

# Mutiple file upload
st.header("Select bulk files to upload")
st.info('Please note the bulk files will be processed later in the night, hence transcript will not be available for immediate use. Also, please upload files with same language together.')
uploaded_files = st.file_uploader("Upload audio files (Individual file Limit 25Mb):", type=['mp4', 'mp3', 'wav'], accept_multiple_files=True)

language = st.selectbox('Audio Language for files:', ['English', 'Otherss'])

if st.button("Submit"):
    if uploaded_files is None:
        st.error("Please upload the audio file")

    for uploaded_file in uploaded_files:
        # check if the file is mp4 or mp3
        if uploaded_file.name[-4:] != ".mp4" and uploaded_file.name[-4:] != ".mp3" and uploaded_file.name[-4:] != ".wav":
            st.error("Please upload the audio file in mp4 format")  
        elif uploaded_file.size/1048576 > 25:
            st.error("File size should be less than 25MB")

        else:
            st.write("File name: ", uploaded_file.name)
            st.write("File size: ", uploaded_file.size/1048576 , "MB")
            st.write("Audio Language: ", language)
            s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
            with st.spinner("Uploading file to S3"):
                audio_file_name= uploaded_file.name[:-4] + '_' + language + uploaded_file.name[-4:]
                common_utils.uploadfile(audio_file_name, uploaded_file.read(),'Batch')
                st.write("File name: ", audio_file_name)
                st.write("File size: ", uploaded_file.size/1048576 , "MB")
            st.success("File uploaded to S3 successfully")



