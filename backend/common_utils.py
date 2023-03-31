import boto3
import os
from dotenv import load_dotenv
import requests

load_dotenv()

AIRFLOW_API_ENDPOINT = 'http://localhost:8080/api/v1/dags/audio_processing_dag/dagRuns'
airflow_username = os.environ.get('AIRFLOW_USERNAME')
airflow_password = os.environ.get('AIRFLOW_PASSWORD')


def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
    return s3client



def uploadfile(file_name, file_content,folder):
    
    """Upload file to S3 bucket
    Args:
        file_name (str): Name of the file
        file_content (str): Content of the file
    """

    s3client = create_connection()
    s3client.put_object(Bucket=os.environ.get('bucket_name'), Key= folder +'/' + file_name , Body= file_content)


def trigger_dag(filename):

    """triggers the Adhoc DAG
    Args:
        filename (str): Name of the file
    """

    data = {
    "conf": {"filename": filename}
    }
    response = requests.post(AIRFLOW_API_ENDPOINT, json=data, auth=(airflow_username, airflow_password))
    return response

def dag_status():

    """checks DAG status
    Args:
        filename (str): Name of the file
    """
    response = requests.get(AIRFLOW_API_ENDPOINT, auth=(airflow_username, airflow_password))
    return response