from langchain_core.tools import tool
from ttsLLM import create_tts as tts_create  # 重命名导入，避免冲突

@tool(description="Create TTS audio file for the final answer. Only call this once at the end after providing the complete text answer.")
def create_tts(text: str, voice: str = "ballad", path: str = "output.mp3") -> str:
    tts_create(text, voice, path)  # 调用正确的函数
    return f"TTS audio saved to {path}"