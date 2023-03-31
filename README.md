<img src="logo.png" width=200>

# VaniVerse - Transcripting voice to a words

VaniVerse is a conversational AI platform that can be used to generate prompts for a given audio file. "Vani" is a Sanskrit word which means "speech" and 
"Verse" means world/collection. Currently hosted on GCP

## Resources

- [Application link](http://34.148.127.152:8501/) <br>
- [Codelab Documentation](https://codelabs-preview.appspot.com/?file_id=1hNtIBuVUguJAEm5IxnkI41rLJiBsVWwF6RFALK7FtU0#0)

## What is VaniVerse?

We developed an AI powered tool which leverages combination of OPENAI Whisper and ChatGPT API to process audio files and simultaneously generate prompts based on the transcript. This tool streamlines the process of generating summaries for long meetings and ask targeted questions for topics discussed. VaniVerse is able to process long transcripts (tested upto 16 mins) by uniquely processing text into smaller chunks for ChatGPT api to be able to process 

## Features
- Audio files transcribed to text (English and other languages) 
- Instant processing of single files and timed processing of bulk uploads (Processed later in night)
- User specifiend and default prompts on audio files
- Long transcript processing, only limit of file size

## Architecture Diagram
<img src="Architecture Diagram.png" alt="Architecture Diagram">

## Tech Deliverables

- The overall architecture involves storing data into AWS S3 buckets
- Processing Adhoc and Batch files through Airflow intantly and timed
- Using Whisper API to transcribe/translate audio based on Language
- Prompt generation based on questions using GPT3.5-turbo and GPT-davinci Models
- Maintaining storage of generated transcripts and prompt responses in AWS S3 buckets 

## Video 

<div align="center">
  <a href=""><img src="" alt="VaniVerse Demo"></a>
</div>

## Steps to reproduce
To run it locally please follow the steps below - 
- clone the repo 
- create a virtual environment and install requirements.txt
- create a .env file with following variables (Airflow credentials can be changed in docker-compose.yaml)
```
OPENAI_API_KEY=
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
bucket_name= <Enter AWS Bucket Name>
AIRFLOW_USERNAME= airflow2 
AIRFLOW_PASSWORD= airflow2
```
- Enter airflow folder and run docker compose command in following manner 
```
cd airflow
docker compose up airflow-init
docker compose up
```
- run streamlit frontend using the following command 
```
streamlit run Home.py
```
