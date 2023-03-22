import streamlit as st


st.title("Model as a Service - Meeting Summary")

st.header("Please upload the audio file ")

audio_file = st.file_uploader("Upload audio file", type=['mp4', 'mp3'])


if st.button("Submit"):
    if audio_file is None:
        st.error("Please upload the audio file")
    
    
    # check if the file is mp4
    elif (audio_file.name[-4:] != ".mp4") and (audio_file.name[-4:] != ".mp3"):
            st.error("Please upload the audio file in mp4 format")  
    else:
        st.success("File uploaded successfully")
        st.write("File name: ", audio_file.name)
        st.write("File size: ", audio_file.size/1048576 , "MB")


# Fetch files from S3 and store the filenames in a list
file_selected = st.selectbox("Select a file", ["File1", "File2", "File3", "File4", "File5"])
qn_selected = st.selectbox("Select a question", ["Question1", "Question2", "Question3", "Question4", "Custom"])

if qn_selected == "Custom":
    custom_qn = st.text_input("Enter your question")

if st.button("Process"):
     pass

