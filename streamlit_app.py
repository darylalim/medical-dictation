import io
import os
import wave

import streamlit as st
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
MAX_RECORDING_SECONDS = 10 * 60  # 10 minutes
MAX_UPLOADS = 100


def transcribe(audio_bytes: bytes):
    client = DeepgramClient(api_key=os.environ["DEEPGRAM_API_KEY"])
    return client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-3-medical",
        smart_format=True,
        numerals=True,
        profanity_filter=True,
    )


st.title("Medical Dictation Transcriber")

tab_upload, tab_record = st.tabs(["Upload File", "Record Audio"])

with tab_upload:
    uploaded_files = st.file_uploader(
        "Upload audio files", type=["wav", "mp3", "m4a", "flac", "ogg"], accept_multiple_files=True
    )
    if st.button("Transcribe", disabled=not uploaded_files, key="transcribe_upload"):
        if len(uploaded_files) > MAX_UPLOADS:
            st.error(f"Too many files. Maximum is {MAX_UPLOADS} per batch.")
        else:
            responses = []
            oversized = []
            for f in uploaded_files:
                if f.size > MAX_FILE_SIZE:
                    oversized.append(f.name)
                    continue
                try:
                    with st.spinner(f"Transcribing {f.name}..."):
                        responses.append((f.name, transcribe(f.getvalue())))
                except KeyError:
                    st.error(
                        "Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root."
                    )
                    break
                except Exception as e:
                    st.error(f"Transcription failed for {f.name}: {e}")
            if oversized:
                st.error(f"Skipped (exceeds 2 GB): {', '.join(oversized)}")
            if responses:
                st.session_state["responses"] = responses

with tab_record:
    recording = st.audio_input("Record a dictation")
    if st.button("Transcribe", disabled=recording is None, key="transcribe_record"):
        audio_bytes = recording.getvalue()
        with wave.open(io.BytesIO(audio_bytes)) as wf:
            duration = wf.getnframes() / wf.getframerate()
        if duration > MAX_RECORDING_SECONDS:
            st.error("Recording exceeds the 10-minute limit.")
        else:
            try:
                with st.spinner("Transcribing..."):
                    response = transcribe(audio_bytes)
                st.session_state["responses"] = [("Recording", response)]
            except KeyError:
                st.error(
                    "Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root."
                )
            except Exception as e:
                st.error(f"Transcription failed: {e}")

if "responses" in st.session_state:
    for name, response in st.session_state["responses"]:
        json_str = response.model_dump_json(indent=4)
        result = response.results.channels[0].alternatives[0]

        st.subheader(name)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Confidence", f"{result.confidence:.1%}")
        col2.metric("Duration", f"{response.metadata.duration:.1f}s")
        col3.metric("Words", len(result.words))
        col4.metric("Language", response.results.channels[0].detected_language or "N/A")

        st.text_area(
            name, value=result.transcript, height=300, disabled=True, label_visibility="collapsed"
        )

        st.download_button(
            "Download JSON",
            data=json_str,
            file_name=f"{name}.json",
            mime="application/json",
            key=f"download_{name}",
        )
