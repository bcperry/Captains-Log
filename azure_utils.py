from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import datetime

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


