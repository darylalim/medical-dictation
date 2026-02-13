# Medical Dictation

Transcribe medical dictation with Deepgram's Nova-3 Medical model.

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
streamlit run streamlit_app.py
```

The app provides two ways to transcribe audio:

- **Upload File** — upload up to 100 audio files at once (wav, mp3, m4a, flac, ogg; max 2 GB each)
- **Record Audio** — record from your microphone (max 10 minutes)

Transcriptions use smart formatting, numerals conversion, and profanity filtering. Each transcription displays confidence, duration, word count, and detected language metrics, along with the full transcript and a JSON download button.

## Testing

```bash
pytest
```

Tests mock the Deepgram API — no real API calls are made.
