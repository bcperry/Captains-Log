import streamlit as st
from azure_utils import get_subfolders, get_data


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
        {"role": "system", "content": "Given a series of journal entries covering various aspects of life such as work, food, family, \
         and personal reflections, summarize each entry by extracting keywords, identifying sentiment, and highlighting significant \
         points. Prioritize information relevant to your day, including major events, key tasks, and other important details. Present\
          keywords as a comma-separated list, key events as bullet points (limited to a maximum of 10 bullets), and provide sentiment \
         analysis covering a broad range of emotions, categorized into positive, negative, and neutral, while also identifying specific \
         emotions when applicable."},
        {"role": "user", "content": transcripts}
    ]
    )

    summary = completion.choices[0].message.content
    return summary


# Setting page layout
st.set_page_config(
    page_title="Captain's Summary",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="auto",

)

if "azure_client" not in st.session_state:
    st.warning("Log in on App tab before use")

else:
    
    dates = get_subfolders(st.session_state.azure_client, folder_prefix="")

    # Create a dropdown menu
    log_day = st.selectbox(
        placeholder = "Choose an option",
        label = 'Select an option',
        options= dates
    )

    if st.button("Get Logs"):
        logs = get_data(st.session_state.azure_client, subfolder_prefix=log_day)
        logs