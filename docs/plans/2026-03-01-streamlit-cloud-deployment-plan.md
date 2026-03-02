# Streamlit Cloud Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let users enter their own Deepgram API key in a sidebar so the app can be deployed on Streamlit Cloud.

**Architecture:** Move API key resolution from `os.environ` lookup inside `_transcribe_batch` to a sidebar `text_input` with `.env` fallback. Pass the key explicitly to transcription functions. Disable Transcribe buttons when no key is present.

**Tech Stack:** Streamlit, Deepgram SDK v5, python-dotenv, pytest

---

### Task 1: Update `_transcribe_batch` to accept `api_key` parameter

**Files:**
- Modify: `tests/test_streamlit_app.py` (TestProcessInputs, TestProcessUrls)
- Modify: `tests/conftest.py` (remove `env_with_api_key` fixture)
- Modify: `streamlit_app.py:25-32`

**Step 1: Update tests to pass `api_key` argument**

In `tests/test_streamlit_app.py`, update every test in `TestProcessInputs` and `TestProcessUrls` that currently uses the `env_with_api_key` fixture:

- Remove `env_with_api_key` from fixture parameters
- Pass `api_key="test-key"` as the first argument to `_process_inputs()` and `_process_urls()`

For example, change:

```python
def test_creates_single_client_for_batch(
    self, mock_deepgram_cls, env_with_api_key, mock_st
):
    streamlit_app._process_inputs([("a.wav", b"a"), ("b.wav", b"b")])
```

to:

```python
def test_creates_single_client_for_batch(
    self, mock_deepgram_cls, mock_st
):
    streamlit_app._process_inputs("test-key", [("a.wav", b"a"), ("b.wav", b"b")])
```

Apply this pattern to all tests in both classes that use `env_with_api_key`. The affected tests (7 in TestProcessInputs, 7 in TestProcessUrls):

- `test_creates_single_client_for_batch`
- `test_passes_correct_transcribe_options`
- `test_stores_responses_in_session_state`
- `test_continues_after_single_file_failure` / `test_continues_after_single_url_failure`
- `test_all_files_failing_does_not_set_session_state` / `test_all_urls_failing_does_not_set_session_state`
- `test_stores_all_successful_responses`
- `test_error_message_includes_filename_and_exception` / `test_error_message_includes_url_and_exception`

**Step 2: Remove `test_missing_api_key_shows_error` from both test classes**

Delete `TestProcessInputs::test_missing_api_key_shows_error` (lines 76-84) and `TestProcessUrls::test_missing_api_key_shows_error` (lines 175-183). The missing-key case is now handled by the UI (disabled buttons), not by the functions.

**Step 3: Remove the `env_with_api_key` fixture**

In `tests/conftest.py`, delete the `env_with_api_key` fixture (lines 33-35).

**Step 4: Run tests to verify they fail**

Run: `uv run pytest tests/test_streamlit_app.py -v`
Expected: tests fail because `_process_inputs` and `_process_urls` don't accept `api_key` yet.

**Step 5: Update `_transcribe_batch` signature and body**

In `streamlit_app.py`, change `_transcribe_batch` from:

```python
def _transcribe_batch(items: list[tuple[str, dict[str, object]]], method: str):
    """Transcribe a batch of audio sources and store results in session state."""
    try:
        api_key = os.environ["DEEPGRAM_API_KEY"]
    except KeyError:
        st.error("Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root.")
        return
    client = DeepgramClient(api_key=api_key)
```

to:

```python
def _transcribe_batch(
    api_key: str, items: list[tuple[str, dict[str, object]]], method: str
):
    """Transcribe a batch of audio sources and store results in session state."""
    client = DeepgramClient(api_key=api_key)
```

**Step 6: Update `_process_inputs` and `_process_urls` to accept and forward `api_key`**

Change:

```python
def _process_inputs(files: list[tuple[str, bytes]]):
    """Transcribe files with a shared client and store results in session state."""
    items = [(name, {"request": data}) for name, data in files]
    _transcribe_batch(items, "transcribe_file")


def _process_urls(urls: list[str]):
    """Transcribe remote audio URLs with a shared client and store results in session state."""
    items = [(url, {"url": url}) for url in urls]
    _transcribe_batch(items, "transcribe_url")
```

to:

```python
def _process_inputs(api_key: str, files: list[tuple[str, bytes]]):
    """Transcribe files with a shared client and store results in session state."""
    items = [(name, {"request": data}) for name, data in files]
    _transcribe_batch(api_key, items, "transcribe_file")


def _process_urls(api_key: str, urls: list[str]):
    """Transcribe remote audio URLs with a shared client and store results in session state."""
    items = [(url, {"url": url}) for url in urls]
    _transcribe_batch(api_key, items, "transcribe_url")
```

**Step 7: Remove `import os`**

`os` is no longer used anywhere in the file (the sidebar will use `os` — but that's added in Task 2). For now, keep `import os` since Task 2 adds it back. Actually, leave `import os` in place since Task 2 needs it.

**Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_streamlit_app.py -v`
Expected: all tests pass.

**Step 9: Lint and format**

Run: `uv run ruff check . && uv run ruff format .`

**Step 10: Commit**

```bash
git add streamlit_app.py tests/conftest.py tests/test_streamlit_app.py
git commit -m "refactor: accept api_key as parameter instead of reading os.environ"
```

---

### Task 2: Add sidebar API key input and disable buttons

**Files:**
- Modify: `streamlit_app.py:67-127` (UI section)

**Step 1: Add sidebar API key input after `st.title`**

After line `st.title("Medical Dictation Transcriber")`, add:

```python
api_key = st.sidebar.text_input(
    "Deepgram API Key",
    type="password",
    value=os.environ.get("DEEPGRAM_API_KEY", ""),
)
```

**Step 2: Update all three Transcribe button `disabled` conditions**

Upload tab — change:
```python
if st.button("Transcribe", disabled=not uploaded_files, key="transcribe_upload"):
```
to:
```python
if st.button("Transcribe", disabled=not uploaded_files or not api_key, key="transcribe_upload"):
```

Record tab — change:
```python
st.button("Transcribe", disabled=recording is None, key="transcribe_record")
```
to:
```python
st.button("Transcribe", disabled=recording is None or not api_key, key="transcribe_record")
```

URL tab — change:
```python
if st.button("Transcribe", disabled=not url_text.strip(), key="transcribe_url"):
```
to:
```python
if st.button("Transcribe", disabled=not url_text.strip() or not api_key, key="transcribe_url"):
```

**Step 3: Pass `api_key` to all call sites**

Change the three call sites:

- `_process_inputs(valid)` → `_process_inputs(api_key, valid)`
- `_process_inputs([("Recording", audio_bytes)])` → `_process_inputs(api_key, [("Recording", audio_bytes)])`
- `_process_urls(valid)` → `_process_urls(api_key, valid)`

**Step 4: Run tests**

Run: `uv run pytest tests/test_streamlit_app.py -v`
Expected: all tests pass (UI code isn't exercised by unit tests, but ensures nothing broke).

**Step 5: Lint and format**

Run: `uv run ruff check . && uv run ruff format .`

**Step 6: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add sidebar API key input with .env fallback, disable buttons when empty"
```

---

### Task 3: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update the architecture section**

In the `## Architecture` section, update point 1 to reflect the new API key handling:

Change:
```
1. Loads `DEEPGRAM_API_KEY` from `.env` via python-dotenv
```

to:
```
1. Loads `DEEPGRAM_API_KEY` from sidebar input (falls back to `.env` via python-dotenv)
```

Update point 3 and 4 to note the `api_key` parameter:

Change:
```
3. `_process_inputs(files)` — creates one shared `DeepgramClient` for a batch, transcribes each file, handles errors via `st.error`, stores results in `st.session_state["responses"]`
4. `_process_urls(urls)` — same pattern as `_process_inputs` but calls `transcribe_url` for remote audio URLs
```

to:
```
3. `_process_inputs(api_key, files)` — creates one shared `DeepgramClient` for a batch, transcribes each file, handles errors via `st.error`, stores results in `st.session_state["responses"]`
4. `_process_urls(api_key, urls)` — same pattern as `_process_inputs` but calls `transcribe_url` for remote audio URLs
```

**Step 2: Update testing section**

Remove "Missing API key error" from the test list since that test was deleted.

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for sidebar API key input"
```
