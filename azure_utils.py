from azure.storage.blob import BlobServiceClient, ContainerClient
import datetime
import streamlit as st

def get_container_client(container_name: str, connection_string: str):

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    if not container_client.exists():
        container_client.create_container()

    return container_client

def save_transcript(transcript: str, container_client: ContainerClient):
    """
    save the transcript for later use.

    Args:
        transcript (str): The string of the transcript.
        
    Returns:
        None
    """
    # Get current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Count existing files
    # List blobs within the current date "directory"
    blobs_in_folder = container_client.list_blobs(name_starts_with=current_date)
    file_count = len(list(blobs_in_folder))
    
    # Construct filename
    filename = f"{current_date}/log_{file_count + 1}.txt"
    
    # Write text to file
    container_client.upload_blob(name=filename, data=transcript)

        
    return (f"Text saved to {filename} in {current_date}")

@st.cache_data
def get_subfolders(_container_client: ContainerClient, folder_prefix: str = '', ):
    
    blobs_in_folder = _container_client.list_blobs()

    # Extract unique subfolder names
    subfolders = set()

    for blob in blobs_in_folder:
        # Get the blob name relative to the folder prefix
        relative_blob_name = blob.name[len(folder_prefix):]

        # Extract the subfolder name (if any)
        subfolder = relative_blob_name.split("/", 1)[0]
        
        # Add the subfolder to the set
        subfolders.add(subfolder)
    
    return subfolders

@st.cache_data
def get_data(_container_client: ContainerClient, subfolder_prefix: str = ''):

    # List "logs" within a date subfolder
    all_logs = _container_client.list_blobs(name_starts_with=subfolder_prefix)

    log_list = [log.name for log in all_logs]

    entries = []

    for log in log_list:
        # Get a reference to the blob
        blob_client = _container_client.get_blob_client(log)
        
        # Download the blob content
        blob_data = blob_client.download_blob()

        # Read the content of the blob as text
        content = blob_data.readall()

        entries.append(content.decode("utf-8"))
    
    return entries