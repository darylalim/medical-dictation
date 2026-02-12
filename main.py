import os

import streamlit as st
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()


def transcribe(audio_bytes: bytes):
    client = DeepgramClient(api_key=os.environ["DEEPGRAM_API_KEY"])
    return client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-3",
        smart_format=True,
    )


st.title("Medical Dictation Transcriber")

uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a", "flac", "ogg"])

if st.button("Transcribe", disabled=uploaded_file is None):
    try:
        with st.spinner("Transcribing..."):
            response = transcribe(uploaded_file.getvalue())
        st.session_state["response"] = response
    except KeyError:
        st.error("Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root.")
    except Exception as e:
        st.error(f"Transcription failed: {e}")

if "response" in st.session_state:
    response = st.session_state["response"]
    json_str = response.model_dump_json(indent=4)
    result = response.results.channels[0].alternatives[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Confidence", f"{result.confidence:.1%}")
    col2.metric("Duration", f"{response.metadata.duration:.1f}s")
    col3.metric("Words", len(result.words))
    col4.metric("Language", response.results.channels[0].detected_language or "N/A")

    st.subheader("Transcript")
    st.text_area("", value=result.transcript, height=300, disabled=True)

    st.download_button("Download JSON", data=json_str, file_name="transcript.json", mime="application/json")
