from unittest.mock import MagicMock


def mock_word(text: str, confidence: float):
    w = MagicMock()
    w.punctuated_word = text
    w.confidence = confidence
    return w
