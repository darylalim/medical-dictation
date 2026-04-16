from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_deepgram_cls():
    with patch("streamlit_app.DeepgramClient") as mock_cls:
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = '{"results": "transcribed"}'

        def _word(text: str, confidence: float):
            w = MagicMock()
            w.punctuated_word = text
            w.confidence = confidence
            return w

        alt = MagicMock()
        alt.transcript = "Life moves pretty fast really."
        alt.confidence = 0.98
        alt.words = [
            _word("Life", 0.99),
            _word("moves", 0.85),  # low — should be highlighted
            _word("pretty", 0.97),
            _word("fast", 0.80),  # low — should be highlighted
            _word("really.", 0.96),
        ]

        channel = MagicMock()
        channel.alternatives = [alt]
        channel.detected_language = "en"

        mock_response.results.channels = [channel]
        mock_response.metadata.duration = 3.5

        mock_cls.return_value.listen.v1.media.transcribe_file.return_value = (
            mock_response
        )
        mock_cls.return_value.listen.v1.media.transcribe_url.return_value = (
            mock_response
        )
        yield mock_cls


@pytest.fixture
def mock_st():
    session_state = {}
    with patch("streamlit_app.st") as mock:
        mock.session_state = session_state
        yield mock
