# External packages
import streamlit as st
import whisper

# Python In-built packages
import pandas as pd
import tempfile
from pathlib import Path

TEMP_DIR = Path(tempfile.gettempdir())

@st.cache_resource()
def create_whisper_model(
    model_path : str = "model/medium.en.pt",
):
    """
    Create a Whisper model for text transcription.

    Args:
        model_path (str): The path to the Llama model.
        
    Returns:
        Whisper: The created whisper model.
    """
        
    return whisper.load_model(model_path)

@st.cache_data
def load_file(file):
    # Streamlit file uploader returns a BytesIO object
    # bytes will be saved to a temporary directory

    dest_path = TEMP_DIR / file.name
    # Save file to destination path
    with open(dest_path, "wb") as f:
        f.write(file.getvalue())
    return dest_path

@st.cache_data
def transcribe(dest_path):
    transcription = model.transcribe(str(dest_path))
    transcript_df = pd.DataFrame(transcription['segments'])
    transcript_df = transcript_df[['start', 'end', 'text']]
    return transcript_df

# Setting page layout
st.set_page_config(
    page_title="Transcription Service",
    page_icon="👂",
    layout="centered",
    initial_sidebar_state="expanded"
)

# load the whisper model
model = create_whisper_model()



# Main page heading
st.title("Speech to Text Transcription")

# Sidebar
st.sidebar.header("Data Upload")

transcription_file = st.sidebar.file_uploader(
    "Select Audio or Video File", type=["mp4", "avi", "mov", "mkv", "mp3", "wav"])  # TODO: Expand this list

st.sidebar.header("Made with ❤️ by the Data Science Team")


if transcription_file:

    dest_path = load_file(transcription_file)

    transcription = transcribe(str(dest_path))

    st.video(str(dest_path))
    transcription






else:
    st.warning("Please upload a file.")

if st.button("Rerun"):
    st.cache_data.clear()
