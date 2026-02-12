import os
from pathlib import Path

from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

AUDIO_FILE = Path("tests/data/audio/bueller-life-moves-pretty-fast_uud9ip.wav")


def main():
    client = DeepgramClient(api_key=os.environ["DEEPGRAM_API_KEY"])
    response = client.listen.v1.media.transcribe_file(
        request=AUDIO_FILE.read_bytes(),
        model="nova-3",
        smart_format=True,
    )
    print(response.model_dump_json(indent=4))


if __name__ == "__main__":
    main()
