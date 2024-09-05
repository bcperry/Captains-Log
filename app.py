# External packages
import streamlit as st
import whisper
from audiorecorder import audiorecorder
from pydub import AudioSegment

# from openai import OpenAI
import azure_utils as azure

# Python In-built packages
import os
import datetime
import tempfile
import pytz
import pandas as pd

@st.cache_data
def save_transcript(transcript: str):
    """
    save the transcript for later use.

    Args:
        transcript (str): The string of the transcript.
        
    Returns:
        None
    """

    if st.session_state.local_storage:
        # Get current date
        current_date = datetime.datetime.now(tz=pytz.timezone("US/Central")).strftime('%Y-%m-%d')
        
        # Create directory if it doesn't exist
        directory = f"data/{current_date}"
        os.makedirs(directory, exist_ok=True)
        
        # Count existing files
        existing_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        file_count = len(existing_files)
        
        # Construct filename
        filename = f"log_{file_count + 1}.txt"
        
        # Write text to file
        with open(os.path.join(directory, filename), 'w', encoding='utf-8')  as file:
            file.write(transcript)
        return f"Text saved to local storage"

    else:
        azure.save_transcript(transcript, st.session_state.azure_client)
        return f"Text saved to azure"

@st.cache_resource
def create_client():
    """
    Creates an instance of the OpenAI client using the provided API key stored in Streamlit secrets.

    Returns:
    - OpenAI: An instance of the OpenAI client.
    """
    # client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)
    return "LLM NOT IMPLEMENTED"


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
def transcribe(filename: str):
    # Split audio file into chunks
    audio_chunks = split_audio(filename)

    full_transcription = ""

    # Transcribe each chunk
    for chunk in audio_chunks:

        # Create a temporary file to store the audio chunk
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            chunk.export(temp_audio_file.name, format="mp3")


            transcription = model.transcribe(temp_audio_file.name, initial_prompt=full_transcription)

            if isinstance(transcription, dict):
                text = transcription['text']
                transcript_df = pd.DataFrame(transcription['segments'])
            else:
                text = transcription.text
                transcript_df = pd.DataFrame(transcription.segments)
            transcript_df = transcript_df[['start', 'end', 'text']]
            
            full_transcription = full_transcription + text
            
        # Close and Delete the temporary audio file
        temp_audio_file.close()
        os.unlink(temp_audio_file.name)

    return transcript_df, full_transcription

# Function to split the audio file into chunks
@st.cache_data
def split_audio(input_file):
    audio = AudioSegment.from_file(input_file)

    # Define the chunk length (e.g., 120 seconds)
    chunk_duration_ms = 120 * 1000 # in milliseconds

    # Calculate number of chunks
    num_chunks = (len(audio) // chunk_duration_ms)+1

    # Split the audio file into chunks
    chunks = []
    for i in range(num_chunks):
        start = i * chunk_duration_ms
        end = (i + 1) * chunk_duration_ms
        chunk = audio[start:end]
        chunks.append(chunk)
    return chunks

# Setting page layout
st.set_page_config(
    page_title="Captain's Log",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="auto",

)


if "user" not in st.session_state:
    st.session_state.user= None

# Main page heading
st.title("Captain's Log 🖖📜")

# Sidebar
with st.sidebar:
    st.header("Log Recorder")
    audio_files = st.sidebar.file_uploader(
                                    "Select Audio or Video File", 
                                    accept_multiple_files=True,
                                    type=["mp4", "avi", "mov", "mkv", "mp3", "wav", "m4a"])  # TODO: Expand this list
    st.subheader("Record your audio")
    recording = audiorecorder("Click to record", "Click to stop recording")
    if st.button("Clear Recording"):
        recording = None
    st.header("Made with ❤️ on Vulcan")


model = create_whisper_model()



file = None


if recording is not None and len(recording)> 0:
    # Create a temporary file to store the audio
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
        recording.export(temp_audio_file.name, format="mp3")
    
    # Read audio data from the temporary file
    with open(temp_audio_file.name, "rb") as file:
        audio_data = file.read()
    
    # show the recording
    st.header("Your recording")
    st.audio(temp_audio_file.name)
    
    # transcribe the text 
    transcription_df, transcription_text = transcribe(temp_audio_file.name)

    with st.expander("Your log",expanded=True):
        st.markdown(transcription_text)
        st.write(transcription_df)

    # Delete the temporary audio file
    temp_audio_file.close()
    os.unlink(temp_audio_file.name)

if len(audio_files) > 0:
    for audio_file in audio_files:
        transcription_df, transcription_text = transcribe(audio_file.name)
        with st.expander(audio_file.name):
            st.video(audio_file)
            st.markdown(transcription_text)
            st.write(transcription_df)
            
else:
    st.warning("Please record a log.")
