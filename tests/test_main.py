from unittest.mock import MagicMock

import pytest

import main

FAKE_AUDIO = b"fake-audio-data"


class TestMainTranscribesAudio:
    def test_calls_transcribe_with_correct_args(
        self, mock_deepgram_cls, env_with_api_key, monkeypatch
    ):
        monkeypatch.setattr(
            main, "AUDIO_FILE", MagicMock(read_bytes=MagicMock(return_value=FAKE_AUDIO))
        )

        main.main()

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.assert_called_once_with(
            request=FAKE_AUDIO,
            model="nova-3",
            smart_format=True,
        )

    def test_prints_json_response(self, mock_deepgram_cls, env_with_api_key, capsys):
        main.main()

        captured = capsys.readouterr()
        assert captured.out.strip() == '{"results": "transcribed"}'


class TestMainMissingApiKey:
    def test_raises_key_error(self, mock_deepgram_cls, monkeypatch):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

        with pytest.raises(KeyError, match="DEEPGRAM_API_KEY"):
            main.main()


class TestMainMissingAudioFile:
    def test_raises_file_not_found_error(
        self, mock_deepgram_cls, env_with_api_key, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(main, "AUDIO_FILE", tmp_path / "nonexistent.wav")

        with pytest.raises(FileNotFoundError):
            main.main()
