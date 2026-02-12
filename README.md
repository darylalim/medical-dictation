# Medical Dictation

Transcribe medical dictation with Deepgram.

## Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
DEEPGRAM_API_KEY=your-key-here
```

## Usage

```bash
python main.py
```

Reads an audio file from `tests/data/audio/`, sends it to Deepgram's Nova-3 model, and prints the transcription as JSON.

## Testing

```bash
pytest
```

Tests mock the Deepgram API — no real API calls are made.
