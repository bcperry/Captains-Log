# External packages
import streamlit as st
import whisper
from audiorecorder import audiorecorder

from streamlit.runtime.uploaded_file_manager import UploadedFile
from openai import OpenAI
import azure_utils as azure
import utilities as util

# Python In-built packages
import os
from io import BytesIO
import datetime
import time
import tempfile
from pathlib import Path


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
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
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
def load_file(file: str):
    # Streamlit file uploader returns a BytesIO object
    # bytes will be saved to a temporary directory

    dest_path = TEMP_DIR / file.name
    # Save file to destination path
    with open(dest_path, "wb") as f:
        f.write(file.getvalue())
    return dest_path

@st.cache_data
def transcribe(dest_path: str):
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
    initial_sidebar_state="auto"
)



if "user" not in st.session_state:
    st.session_state.user= None


# Main page heading
st.title("Captain's Log 🖖📜")

# use login info
# Create an empty container
placeholder = st.empty()

user_email = st.secrets.USER
actual_password = st.secrets.PASSWORD 

if st.session_state.user is None:
    # Insert a form in the container
    with placeholder.form("login"):
        st.markdown("#### Enter your credentials")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit and email == user_email and password == actual_password:
        # If the form is submitted and the email and password are correct,
        # clear the form/container and display a success message
        placeholder.empty()
        user, email = util.get_user(email)
        st.session_state.user=user
        st.success("Login successful")
    elif submit and email != user_email and password != actual_password:
        st.error("Login failed")
    else:
        pass

# Sidebar
with st.sidebar:
    st.header("Log Recorder")
    st.session_state.local_model = st.toggle("Use Local Whisper", value=False)
    st.session_state.local_storage = st.toggle("Use Local Storage", value=False)
    st.header("Made with ❤️ on Vulcan")


if st.session_state.local_model:
    # load the whisper model
    model = create_whisper_model()


if st.session_state.user:

    # Create an OpenAI client if not already initialized in the Streamlit session state
    if "openAI" not in st.session_state:
        st.session_state.openAI= create_client()

    # Create an OpenAI client if not already initialized in the Streamlit session state
    if "summary" not in st.session_state:
        st.session_state.summary= None

    if "azure_client" not in st.session_state:
        st.session_state.azure_client= azure.get_container_client(container_name=st.session_state.user, connection_string=st.secrets.AZURE_CONN_STRING)


    file = None

    st.subheader("Record your audio")
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

    if file is not None:
        transcripts = ""
        # rename becase I am a hack
        file.name = file.name.split('\\')[-1]
        # load the audio file into memory
        dest_path = load_file(file)

        # transcribe the text
        transcription_text = transcribe(str(dest_path))

        with st.expander("Your log",expanded=True):
            st.markdown(transcription_text)

        # persist the transcripts
        result = save_transcript(transcript=transcription_text)

        st.toast(result)
        
    else:
        st.warning("Please record a log.")
