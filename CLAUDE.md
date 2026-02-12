# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Medical dictation transcription app using Deepgram's speech-to-text API. Single-script prototype that transcribes a local audio file using Deepgram's Nova-3 model.

## Commands

```bash
# Install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Run
python main.py

# Lint and format
ruff check .
ruff format .

# Type check
ty check .

# Test
pytest
```

## Architecture

Single-file application (`main.py`) that:

1. Loads `DEEPGRAM_API_KEY` from `.env` via python-dotenv
2. Creates a `DeepgramClient` with the API key passed explicitly
3. Reads a local audio file from `tests/data/audio/` and calls `client.listen.v1.media.transcribe_file()` with Nova-3 model and smart formatting
4. Prints the transcription as JSON via Pydantic's `model_dump_json()`

## Testing

Tests live in `tests/test_main.py` and mock `DeepgramClient` so no real API calls are made.

- `conftest.py` (root) — Adds project root to pytest's `sys.path`
- `tests/conftest.py` — Shared fixtures (`mock_deepgram_cls`, `env_with_api_key`)
- `tests/test_main.py` — Tests for happy-path transcription, missing API key, and missing audio file

## Dependencies

- **deepgram-sdk** (v5) — Speech-to-text SDK. Options are keyword args (not `PrerecordedOptions`), API key is passed explicitly to `DeepgramClient`, responses are Pydantic models.
- **python-dotenv** — Loads environment variables from `.env`
- **ruff** — Linter and formatter
- **ty** — Type checker
- **pytest** — Testing framework

## Environment

- `DEEPGRAM_API_KEY` — Required. Set in `.env` at project root.
