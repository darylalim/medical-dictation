# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Medical dictation transcription app using Deepgram's speech-to-text API. Streamlit web app that transcribes uploaded or recorded audio using Deepgram's Nova-3 Medical model.

## Commands

```bash
# Install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Run
streamlit run streamlit_app.py

# Lint and format
ruff check .
ruff format .

# Type check
ty check .

# Test
pytest
```

## Architecture

Single-file Streamlit application (`streamlit_app.py`) that:

1. Loads `DEEPGRAM_API_KEY` from `.env` via python-dotenv
2. Provides a `transcribe(audio_bytes)` helper that creates a `DeepgramClient` and calls `client.listen.v1.media.transcribe_file()` with Nova-3 Medical model, smart formatting, numerals conversion, and profanity filtering
3. Offers a Streamlit UI with two input tabs:
   - **Upload File** — batch upload up to 100 audio files (max 2 GB each), formats: wav, mp3, m4a, flac, ogg
   - **Record Audio** — record from microphone via `st.audio_input` (max 10 minutes)
4. Displays per-file metrics (confidence, duration, word count, language), transcript viewer, and JSON download

## Testing

Tests live in `tests/test_streamlit_app.py` and mock `DeepgramClient` so no real API calls are made.

- `conftest.py` (root) — Adds project root to pytest's `sys.path`
- `tests/conftest.py` — Shared fixtures (`mock_deepgram_cls`, `env_with_api_key`)
- `tests/test_streamlit_app.py` — Tests for `transcribe()` helper: correct API args, response structure, and missing API key

## Dependencies

- **deepgram-sdk** (v5) — Speech-to-text SDK. Options are keyword args (not `PrerecordedOptions`), API key is passed explicitly to `DeepgramClient`, responses are Pydantic models.
- **streamlit** — Web UI framework
- **python-dotenv** — Loads environment variables from `.env`
- **ruff** — Linter and formatter
- **ty** — Type checker
- **pytest** — Testing framework

## Environment

- `DEEPGRAM_API_KEY` — Required. Set in `.env` at project root.
