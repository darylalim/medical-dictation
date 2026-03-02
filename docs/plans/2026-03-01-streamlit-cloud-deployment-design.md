# Streamlit Cloud Deployment

## Summary

Deploy the app on Streamlit Cloud so users can test it with their own Deepgram API keys. Each visitor enters their key in a sidebar input; local development continues to work via `.env`.

## Approach

Sidebar text input with `.env` fallback. Keep `load_dotenv()` so the key auto-populates locally. On Streamlit Cloud (no `.env`), users paste their own key.

Rejected alternatives:
- Sidebar only (no `.env`): breaks local dev workflow, requires typing the key every run.
- Secrets only (`secrets.toml`): all visitors share one key, no per-user isolation.

## API Key Handling

- `load_dotenv()` remains at app startup
- Add `st.sidebar.text_input("Deepgram API Key", type="password", value=os.environ.get("DEEPGRAM_API_KEY", ""))` at top of UI
- Store resolved key in a local variable `api_key`
- Pass `api_key` as a parameter to `_transcribe_batch` instead of reading `os.environ` inside it
- `_process_inputs` and `_process_urls` also accept and forward `api_key`
- Remove the `KeyError` try/except from `_transcribe_batch`

## Button Disabling

- All three Transcribe buttons add `not api_key` to their `disabled` condition
- Example: `disabled=not uploaded_files or not api_key`
- No separate error message — button is simply not clickable without a key

## Transcript Display

- Already changed from `st.text_area(disabled=True)` to `st.code(language=None, wrap_lines=True)` for easy copy-paste via built-in copy button

## Deployment

- Streamlit Cloud deploys directly from the GitHub repo pointing at `streamlit_app.py`
- `pyproject.toml` declares dependencies; Streamlit Cloud resolves via `uv`
- No `requirements.txt`, `Dockerfile`, or secrets configuration needed

## Test Updates

- Update `_transcribe_batch`, `_process_inputs`, `_process_urls` tests to pass `api_key` as an argument
- Remove or simplify the "missing API key" test (UI disabling handles this now)
- Update `mock_deepgram_cls` usage if the function signature changes
