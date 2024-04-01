# External packages
import streamlit as st
import whisper
from audiorecorder import audiorecorder
from streamlit.runtime.uploaded_file_manager import UploadedFile
from openai import OpenAI
import azure_utils as azure

# Python In-built packages
import os
from io import BytesIO
import datetime
import time
import tempfile
from pathlib import Path


@st.cache_data
def save_transcript(transcript : str):
    """
    save the transcript for later use.

    Args:
        transcript (str): The string of the transcript.
        
    Returns:
        None
    """
    if st.session_state.local_storage:
        # Get current date
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Create directory if it doesn't exist
        directory = f"data/{current_date}"
        os.makedirs(directory, exist_ok=True)
        
        # Count existing files
        existing_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        file_count = len(existing_files)
        
        # Construct filename
        filename = f"{current_date}_log_{file_count + 1}.txt"
        
        # Write text to file
        with open(os.path.join(directory, filename), 'w', encoding='utf-8')  as file:
            file.write(transcript)
        
        print(f"Text saved to {filename} in {directory}")
            
    else:
        azure.save_transcript(transcript, st.session_state.azure_client)
        print(f"Text saved to azure")

@st.cache_resource
def create_client():
    """
    Creates an instance of the OpenAI client using the provided API key stored in Streamlit secrets.

    Returns:
    - OpenAI: An instance of the OpenAI client.
    """
    client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)
    return client

@st.cache_resource
def authenticate_storage():
    st.secrets.AZURE_CONN_STRING
    return()

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
def generate_summary(transcripts:str):
    """
    Generates a summary of the transcripts using the OpenAI GPT-3.5 Turbo model.

    Parameters:
    - transcripts (str): The transcripts to generate the summary from.

    Returns:
    - str: The generated summary.
    """
    completion = st.session_state.openAI.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a service tailored to the army domain, aimed at generating concise, formal summaries for senior \
         leaders based on a mix of transcripts from meetings, interviews, and presentations. The summaries should focus on key items, anomalies,\
          and the number of events, with each summary limited to one page or less. Additionally, the service should include functionality for\
          keyword extraction."},
        {"role": "user", "content": transcripts}
    ]
    )

    summary = completion.choices[0].message.content
    return summary

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
    if st.session_state.local_model:
        transcription = model.transcribe(str(dest_path))
        
    else:
        audio_file= open(str(dest_path), "rb")
        transcription = st.session_state.openAI.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        response_format="verbose_json",
        )
    if isinstance(transcription, dict):
        text = transcription['text']
    else:
        text = transcription.text

    return text

# Setting page layout
st.set_page_config(
    page_title="Captain's Log",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="expanded"
)


# Create an OpenAI client if not already initialized in the Streamlit session state
if "openAI" not in st.session_state:
    st.session_state.openAI= create_client()

# Create an OpenAI client if not already initialized in the Streamlit session state
if "summary" not in st.session_state:
    st.session_state.summary= None

if "azure_client" not in st.session_state:
    st.session_state.azure_client= azure.get_container_client(container_name="blainecperry", connection_string=st.secrets.AZURE_CONN_STRING)


# Main page heading
st.title("Captain's Log 🖖📜")

# Sidebar
with st.sidebar:
    st.header("Log Recorder")
    st.session_state.local_model = st.toggle("Use Local Whisper", value=False)
    st.session_state.local_storage = st.toggle("Use Local Storage", value=False)


    if st.session_state.local_model:
        # load the whisper model
        model = create_whisper_model()

    audio_files = []

    st.header("Record your audio")
    recording = audiorecorder("Click to record", "Click to stop recording")
    if st.button("Clear Recording"):
        recording = None
    if recording is not None and len(recording)> 0:
        # its a pain in the ass to deal with this see if we can clean it later
        file = recording.export(TEMP_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}_Captains_Log.wav", format="wav")
        audio_stream = BytesIO()
        recording.export(audio_stream, format='wav')
        audio_stream.seek(0)
        file.file_id = 'recording'
        file.type = "audio/wav"
        file.data = audio_stream.getvalue()
        file = UploadedFile(record = file, file_urls=TEMP_DIR / f"audio.wav")
        
        # show the recording
        st.header("Your recording")
        recording

        #add to the list
        audio_files.append(file)
    st.header("Made with ❤️ on Vulcan")


if len(audio_files)>0:
    transcripts = ""
    for file in audio_files:
        # rename becase I am a hack
        file.name = file.name.split('\\')[-1]
        # load the audio file into memory
        dest_path = load_file(file)

        # transcribe the text
        transcription_text = transcribe(str(dest_path))

        # persist the transcripts
        save_transcript(transcript=transcription_text)

        # this will save the transcripts in a format ready to show the user
        transcripts = transcripts + f'{file.name}: \n\n {transcription_text}\n\n'

        with st.expander("Your log",expanded=True):
            st.markdown(transcripts)


    if st.sidebar.button("Rerun"):
        st.cache_data.clear()

else:
    st.warning("Please record a log.")


