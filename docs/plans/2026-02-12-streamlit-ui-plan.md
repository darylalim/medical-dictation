# Streamlit UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the CLI `main.py` with a Streamlit app that lets users upload audio, transcribe it via Deepgram, view transcript and metrics, and download JSON.

**Architecture:** Single-file `main.py` with a `transcribe(audio_bytes: bytes) -> response` helper (pure function, testable without Streamlit) and Streamlit UI code guarded by `if __name__ ...` or equivalent. Session state persists the response across Streamlit reruns.

**Tech Stack:** Streamlit, deepgram-sdk v5, python-dotenv, pytest

---

### Task 1: Rewrite `main.py` with `transcribe()` helper and Streamlit UI

**Files:**
- Modify: `main.py`

**Step 1: Rewrite `main.py`**

Replace the entire contents of `main.py` with:

```python
import os

import streamlit as st
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

ACCEPTED_TYPES = ["audio/wav", "audio/mpeg", "audio/mp4", "audio/flac", "audio/ogg"]


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
```

**Step 2: Verify the app starts**

Run: `streamlit run main.py --server.headless true &` then stop it.
Expected: App starts without import errors.

**Step 3: Commit**

```bash
git add main.py
git commit -m "feat: rewrite main.py as Streamlit app with transcribe() helper"
```

---

### Task 2: Update tests for `transcribe()` helper

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/test_main.py`

**Step 1: Update `tests/conftest.py`**

Replace the entire contents with:

```python
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_deepgram_cls():
    with patch("main.DeepgramClient") as mock_cls:
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = '{"results": "transcribed"}'

        alt = MagicMock()
        alt.transcript = "Life moves pretty fast."
        alt.confidence = 0.98
        alt.words = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        channel = MagicMock()
        channel.alternatives = [alt]
        channel.detected_language = "en"

        mock_response.results.channels = [channel]
        mock_response.metadata.duration = 3.5

        mock_cls.return_value.listen.v1.media.transcribe_file.return_value = (
            mock_response
        )
        yield mock_cls


@pytest.fixture
def env_with_api_key(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
```

**Step 2: Rewrite `tests/test_main.py`**

Replace the entire contents with:

```python
import pytest

import main

FAKE_AUDIO = b"fake-audio-data"


class TestTranscribe:
    def test_calls_deepgram_with_correct_args(
        self, mock_deepgram_cls, env_with_api_key
    ):
        main.transcribe(FAKE_AUDIO)

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.assert_called_once_with(
            request=FAKE_AUDIO,
            model="nova-3",
            smart_format=True,
        )

    def test_returns_response_object(self, mock_deepgram_cls, env_with_api_key):
        response = main.transcribe(FAKE_AUDIO)

        assert response.results.channels[0].alternatives[0].transcript == "Life moves pretty fast."
        assert response.results.channels[0].alternatives[0].confidence == 0.98
        assert response.metadata.duration == 3.5

    def test_missing_api_key_raises_key_error(self, mock_deepgram_cls, monkeypatch):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

        with pytest.raises(KeyError, match="DEEPGRAM_API_KEY"):
            main.transcribe(FAKE_AUDIO)
```

**Step 3: Run tests**

Run: `pytest tests/test_main.py -v`
Expected: All 3 tests PASS.

**Step 4: Commit**

```bash
git add tests/conftest.py tests/test_main.py
git commit -m "test: update tests for transcribe() helper"
```

---

### Task 3: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md**

In the Commands section, change `python main.py` to `streamlit run main.py`.

In the Architecture section, replace the description to reflect the Streamlit app with `transcribe()` helper.

In the Dependencies section, add `streamlit`.

In the Testing section, update to reflect testing the `transcribe()` function.

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for Streamlit UI"
```

---

### Task 4: Lint, format, and verify

**Step 1: Run ruff**

Run: `ruff check . && ruff format .`
Expected: No errors. Fix any issues found.

**Step 2: Run tests one final time**

Run: `pytest -v`
Expected: All tests pass.

**Step 3: Commit any formatting fixes**

```bash
git add -A
git commit -m "style: apply ruff formatting"
```
(Only if ruff made changes.)
