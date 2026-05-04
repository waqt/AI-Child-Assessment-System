"""
volcengine/__init__.py
======================
火山引擎（豆包）语音服务对外接口。

本包封装了所有与火山引擎 OpenSpeech V3 API 的交互细节，
对外仅暴露两个函数和一个配置加载器：

    from volcengine import load_voice_config, tts_generate, stt_recognize

使用方式：
    config = load_voice_config()
    audio  = tts_generate(text="你好", **config["tts"])
    text   = stt_recognize(audio_bytes=wav_bytes, **config["stt"])
"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_DIR, "voice_config.json")


def load_voice_config() -> dict:
    """
    加载 volcengine/voice_config.json 中的语音配置。

    返回格式：
    {
        "tts": {"api_key": "...", "resource_id": "...", "voice": "..."},
        "stt": {"api_key": "...", "resource_id": "..."}
    }
    """
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# 从 voice_service 子模块导出核心函数
from .voice_service import tts_generate, stt_recognize

__all__ = ["load_voice_config", "tts_generate", "stt_recognize"]
