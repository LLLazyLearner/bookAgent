import os

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# OpenAI 负责 TTS
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

def create_tts(text: str, voice: str = "ballad", path: str = "output.mp3") -> None:
    """创建 TTS 音频文件，失败时抛出异常"""
    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text
    )
    with open(path, "wb") as f:
        f.write(speech.content)
