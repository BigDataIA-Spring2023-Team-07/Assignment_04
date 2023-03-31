import streamlit as st
from PIL import Image

image=Image.open('cover.png')
st.title("VaniVerse - Transcribing voice to words :page_with_curl:")
st.write('VaniVerse is a conversational AI platform that can be used to generate prompts for a given audio file.')
st.image('cover.png',caption='VaniVerse Bot in a meeting (Image created in DALL-E)',width=700)