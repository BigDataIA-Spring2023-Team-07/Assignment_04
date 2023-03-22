import streamlit as st

st.title("Model as a Service - Meeting Summary")

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
            st.success("File uploaded successfully")
            st.write("File name: ", uploaded_file.name)
            st.write("File size: ", uploaded_file.size/1048576 , "MB")

