# Remote URL Transcription Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Remote URL" tab that transcribes audio files hosted at public URLs via Deepgram's `transcribe_url` API.

**Architecture:** New `_process_urls()` function mirrors `_process_inputs()` but calls `transcribe_url` instead of `transcribe_file`. Third tab with a text area for multiple URLs (one per line). Same display logic for results.

**Tech Stack:** Deepgram SDK v5 (`client.listen.v1.media.transcribe_url`), Streamlit

---

### Task 1: Add `transcribe_url` mock to conftest

**Files:**
- Modify: `tests/conftest.py:24`

**Step 1: Update the mock fixture to also mock `transcribe_url`**

In `tests/conftest.py`, add a line after line 24 so that `transcribe_url` returns the same mock response as `transcribe_file`:

```python
        mock_cls.return_value.listen.v1.media.transcribe_file.return_value = (
            mock_response
        )
        mock_cls.return_value.listen.v1.media.transcribe_url.return_value = (
            mock_response
        )
```

**Step 2: Run existing tests to verify nothing broke**

Run: `uv run pytest -v`
Expected: All existing tests PASS

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add transcribe_url mock to conftest"
```

---

### Task 2: Test and implement `_process_urls` — client reuse

**Files:**
- Test: `tests/test_streamlit_app.py`
- Modify: `streamlit_app.py`

**Step 1: Write the failing test**

Add a new test class in `tests/test_streamlit_app.py`:

```python
class TestProcessUrls:
    def test_creates_single_client_for_batch(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(
            ["https://example.com/a.wav", "https://example.com/b.wav"]
        )

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        assert mock_client.listen.v1.media.transcribe_url.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_streamlit_app.py::TestProcessUrls::test_creates_single_client_for_batch -v`
Expected: FAIL with `AttributeError: module 'streamlit_app' has no attribute '_process_urls'`

**Step 3: Write minimal implementation**

Add to `streamlit_app.py` after `_process_inputs`:

```python
def _process_urls(urls: list[str]):
    """Transcribe remote audio URLs with a shared client and store results in session state."""
    try:
        api_key = os.environ["DEEPGRAM_API_KEY"]
    except KeyError:
        st.error("Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root.")
        return
    client = DeepgramClient(api_key=api_key)
    responses = []
    for url in urls:
        try:
            with st.spinner(f"Transcribing {url}..."):
                resp = client.listen.v1.media.transcribe_url(
                    url=url, **_TRANSCRIBE_OPTS
                )
                responses.append((url, resp))
        except Exception as e:
            st.error(f"Transcription failed for {url}: {e}")
    if responses:
        st.session_state["responses"] = responses
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_streamlit_app.py::TestProcessUrls::test_creates_single_client_for_batch -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_streamlit_app.py streamlit_app.py
git commit -m "feat: add _process_urls with client reuse"
```

---

### Task 3: Test `_process_urls` — transcribe options, session state, missing key

**Files:**
- Test: `tests/test_streamlit_app.py`

**Step 1: Add three more tests to `TestProcessUrls`**

```python
    def test_passes_correct_transcribe_options(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(["https://example.com/test.wav"])

        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.assert_called_once_with(
            url="https://example.com/test.wav",
            model="nova-3-medical",
            smart_format=True,
            numerals=True,
            profanity_filter=True,
        )

    def test_stores_responses_in_session_state(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(["https://example.com/test.wav"])

        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0][0] == "https://example.com/test.wav"

    def test_missing_api_key_shows_error(self, mock_deepgram_cls, monkeypatch, mock_st):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

        streamlit_app._process_urls(["https://example.com/test.wav"])

        mock_st.error.assert_called_once_with(
            "Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root."
        )
        assert "responses" not in mock_st.session_state
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_streamlit_app.py::TestProcessUrls -v`
Expected: All 4 tests PASS

**Step 3: Commit**

```bash
git add tests/test_streamlit_app.py
git commit -m "test: add option, session state, and missing key tests for _process_urls"
```

---

### Task 4: Test `_process_urls` — error handling

**Files:**
- Test: `tests/test_streamlit_app.py`

**Step 1: Add error handling tests to `TestProcessUrls`**

```python
    def test_continues_after_single_url_failure(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        good_response = MagicMock()
        mock_client.listen.v1.media.transcribe_url.side_effect = [
            Exception("API error"),
            good_response,
        ]

        streamlit_app._process_urls(
            ["https://example.com/bad.wav", "https://example.com/good.wav"]
        )

        mock_st.error.assert_called_once_with(
            "Transcription failed for https://example.com/bad.wav: API error"
        )
        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0] == ("https://example.com/good.wav", good_response)

    def test_all_urls_failing_does_not_set_session_state(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.side_effect = Exception("fail")

        streamlit_app._process_urls(
            ["https://example.com/a.wav", "https://example.com/b.wav"]
        )

        assert mock_st.error.call_count == 2
        assert "responses" not in mock_st.session_state

    def test_stores_all_successful_responses(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(
            [
                "https://example.com/a.wav",
                "https://example.com/b.wav",
                "https://example.com/c.wav",
            ]
        )

        responses = mock_st.session_state["responses"]
        assert len(responses) == 3
        assert [name for name, _ in responses] == [
            "https://example.com/a.wav",
            "https://example.com/b.wav",
            "https://example.com/c.wav",
        ]

    def test_error_message_includes_url_and_exception(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.side_effect = Exception("timeout")

        streamlit_app._process_urls(["https://example.com/bad.wav"])

        mock_st.error.assert_called_once_with(
            "Transcription failed for https://example.com/bad.wav: timeout"
        )
```

Note: `MagicMock` is already imported at the top of `test_streamlit_app.py`.

**Step 2: Run all tests to verify they pass**

Run: `uv run pytest tests/test_streamlit_app.py::TestProcessUrls -v`
Expected: All 8 tests PASS

**Step 3: Commit**

```bash
git add tests/test_streamlit_app.py
git commit -m "test: add error handling tests for _process_urls"
```

---

### Task 5: Add Remote URL tab to the UI

**Files:**
- Modify: `streamlit_app.py:47`

**Step 1: Update tab creation to include three tabs**

Change line 47 from:

```python
tab_upload, tab_record = st.tabs(["Upload File", "Record Audio"])
```

to:

```python
tab_record, tab_url, tab_upload = st.tabs(["Record Audio", "Remote URL", "Upload File"])
```

**Step 2: Add the Remote URL tab block after the `with tab_record:` block**

```python
with tab_url:
    url_text = st.text_area(
        "Enter audio file URLs (one per line)",
        placeholder="https://example.com/audio.wav",
    )
    if st.button("Transcribe", disabled=not url_text.strip(), key="transcribe_url"):
        raw_urls = [line.strip() for line in url_text.splitlines()]
        urls = [u for u in raw_urls if u]
        invalid = [u for u in urls if not u.startswith(("http://", "https://"))]
        if invalid:
            st.error(f"Invalid URL(s): {', '.join(invalid)}")
        elif len(urls) > MAX_UPLOADS:
            st.error(f"Too many URLs. Maximum is {MAX_UPLOADS} per batch.")
        else:
            _process_urls(urls)
```

**Step 3: Run full test suite and linter**

Run: `uv run pytest -v && uv run ruff check . && uv run ruff format --check .`
Expected: All pass

**Step 4: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add Remote URL tab for transcribing audio from URLs"
```

---

### Task 6: Final verification

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 2: Run linter and formatter**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: Clean

**Step 3: Run type checker**

Run: `uv run ty check .`
Expected: No errors (warnings are acceptable)

**Step 4: Manual smoke test**

Run: `uv run streamlit run streamlit_app.py`
Verify: Three tabs visible — "Record Audio", "Remote URL", "Upload File". The URL tab has a text area and a Transcribe button.
