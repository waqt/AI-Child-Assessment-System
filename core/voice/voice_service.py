"""
voice_service.py
================
火山引擎（豆包）语音服务封装模块。

包含：
  - TTS 语音合成（OpenSpeech V3 HTTP 非流式接口）
  - STT 语音识别（OpenSpeech V3 WebSocket 双向流式接口）

鉴权方式：新版控制台 X-Api-Key
TTS 接口：POST https://openspeech.bytedance.com/api/v3/tts/unidirectional
STT 接口：WSS  wss://openspeech.bytedance.com/api/v3/sauc/bigmodel
"""
import os
import json

_VOICE_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "voice_config.json")

def load_voice_config():
    """加载语音配置"""
    if not os.path.exists(_VOICE_CONFIG_FILE):
        return {}
    with open(_VOICE_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

import json
import struct
import uuid
import base64
import requests
import urllib3
import websocket

# ──────────────────────────────────────────────
# 公共工具
# ──────────────────────────────────────────────

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VOLC_BASE_URL = "https://openspeech.bytedance.com"


def _make_session() -> requests.Session:
    """
    创建一个彻底绕过系统代理（Clash 等）的 requests Session。
    设置 trust_env=False 可防止 requests 读取 HTTP_PROXY / HTTPS_PROXY 环境变量。
    """
    session = requests.Session()
    session.trust_env = False
    return session


# ──────────────────────────────────────────────
# TTS：语音合成
# ──────────────────────────────────────────────

TTS_API_URL = f"{VOLC_BASE_URL}/api/v3/tts/unidirectional"


def tts_generate(
    text: str,
    api_key: str,
    resource_id: str,
    voice: str,
    audio_format: str = "mp3",
    sample_rate: int = 24000,
) -> bytes:
    """
    调用火山引擎 OpenSpeech V3 TTS 接口，将文字合成为音频字节流。

    Args:
        text:        需要合成的文字内容
        api_key:     新版控制台 API Key（X-Api-Key）
        resource_id: TTS 模型资源 ID，如 volc.megatts.voiceclone / seed-tts-2.0
        voice:       音色代号，如 zh_female_yingyujiaoxue_uranus_bigtts
        audio_format: 音频格式，默认 mp3
        sample_rate:  采样率，默认 24000

    Returns:
        合成好的音频二进制内容（bytes）

    Raises:
        Exception: 接口报错或未收到音频数据时抛出
    """
    req_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": req_id,
    }
    payload = {
        "user": {"uid": "aiteacher_user"},
        "req_params": {
            "text": text,
            "speaker": voice,
            "audio_params": {
                "format": audio_format,
                "sample_rate": sample_rate,
            },
        },
    }

    print("\n==== [Volcengine TTS Request] ====")
    print(f"URL   : {TTS_API_URL}")
    print(f"ResID : {resource_id}  |  Voice: {voice}")
    print(f"Payload(text): {text[:50]}...")
    print("==================================\n")

    session = _make_session()
    response = session.post(TTS_API_URL, headers=headers, json=payload, verify=False)

    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    # 响应格式：JSON Lines 流式，每行一个 JSON 对象，音频 base64 在 "data" 字段里
    # 结尾包的 data 字段值为 null，需跳过
    audio_chunks = []
    error_msg = ""

    for line in response.iter_lines():
        if not line:
            continue
        try:
            line_str = line.decode("utf-8")
            if line_str.startswith("data:"):
                line_str = line_str[5:]
            chunk = json.loads(line_str)
            if chunk.get("data"):
                audio_chunks.append(base64.b64decode(chunk["data"]))
            elif "code" in chunk and chunk.get("code", 0) not in (0, 30000000):
                error_msg = f"服务端错误: {chunk}"
        except json.JSONDecodeError:
            # 极少数情况下服务端直接返回原生二进制
            audio_chunks.append(line)

    if audio_chunks:
        return b"".join(audio_chunks)

    raise Exception(error_msg if error_msg else "未收到任何音频数据包！可能是配额不足或参数错误。")


# ──────────────────────────────────────────────

# 使用流式输入模式（bigmodel_nostream）：
# - 客户端分片发送音频，服务端只在收到最后一包后返回识别结果
# - 不需要双向并发读写，Windows 兼容性好
# - 平均 5 秒音频可在 300~400ms 内返回结果
# - 准确率比双向流式更高（官方文档说明）
STT_WS_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"

# 火山引擎自定义 WebSocket 二进制协议 Header 常量
_HDR_FULL_CLIENT_REQ = b"\x11\x10\x10\x00"  # type=1(full req), flags=0, json, no compress
_HDR_AUDIO_ONLY      = b"\x11\x20\x00\x00"  # type=2(audio), flags=0(非最后一包)
_HDR_AUDIO_ONLY_LAST = b"\x11\x22\x00\x00"  # type=2(audio), flags=2(last packet)

# nostream 模式下不需要模拟实时流，可以用较大的分片快速上传
# 1 秒的 PCM 音频 (16kHz, 16bit, mono) = 16000 * 2 = 32000 bytes
_CHUNK_SIZE = 32000
_CHUNK_INTERVAL = 0.04  # 发包间隔仅用于防止网络拥塞


def _parse_server_frame(frame: bytes) -> tuple:
    """
    解析服务端二进制帧，返回 (msg_type, msg_flag, payload_json_or_none)。
    """
    if len(frame) < 4:
        return None, None, None

    msg_type = (frame[1] & 0xF0) >> 4
    msg_flag = frame[1] & 0x0F

    if msg_type in (0b1001, 0b1111):  # Full server response / Error
        if len(frame) < 12:
            return msg_type, msg_flag, None
        payload_size = struct.unpack(">I", frame[8:12])[0]
        raw_payload = frame[12: 12 + payload_size]
        try:
            payload = json.loads(raw_payload.decode("utf-8"))
        except Exception:
            payload = raw_payload.decode("utf-8", errors="replace")
        return msg_type, msg_flag, payload

    return msg_type, msg_flag, None


def stt_recognize(
    audio_bytes: bytes,
    api_key: str,
    resource_id: str,
    audio_format: str = "wav",
    sample_rate: int = 16000,
    language: str = "",
) -> str:
    """
    调用火山引擎 OpenSpeech V3 WebSocket 流式输入 STT 接口，将音频字节转为文字。

    使用 bigmodel_nostream（流式输入模式）：
    - 客户端分片发送音频
    - 服务端在收到最后一包后统一返回识别结果
    - 准确率高于双向流式模式

    Args:
        audio_bytes:  原始音频字节（WAV 格式）
        api_key:      新版控制台 API Key
        resource_id:  STT 模型资源 ID，如 volc.bigasr.auc_turbo
        audio_format: 音频格式，默认 wav
        sample_rate:  采样率，默认 16000
        language:     指定语言（留空则自动检测）

    Returns:
        识别出的文字字符串
    """
    import time

    req_id = str(uuid.uuid4())
    ws_headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": req_id,
    }

    total_chunks = (len(audio_bytes) + _CHUNK_SIZE - 1) // _CHUNK_SIZE

    print("\n==== [Volcengine STT Request (nostream)] ====")
    print(f"WS URL  : {STT_WS_URL}")
    print(f"ResID   : {resource_id}  |  Format: {audio_format}")
    print(f"AudioLen: {len(audio_bytes)} bytes  |  Chunks: {total_chunks}")
    print("=============================================")

    ws = websocket.WebSocket()
    ws.connect(STT_WS_URL, header=ws_headers)

    # ① 发送 Full client request（含音频元数据 JSON）
    audio_cfg = {
        "format": audio_format,
        "codec": "raw",
        "rate": sample_rate,
        "bits": 16,
        "channel": 1,
    }
    if language:
        audio_cfg["language"] = language

    init_payload = {
        "user": {"uid": "aiteacher_user"},
        "audio": audio_cfg,
        "request": {
            "model_name": "bigmodel",
            "show_utterances": False,
        },
    }
    init_bytes = json.dumps(init_payload).encode("utf-8")
    size_bytes = struct.pack(">I", len(init_bytes))
    ws.send_binary(_HDR_FULL_CLIENT_REQ + size_bytes + init_bytes)
    print("[STT] Sent full client request")

    # ② 分片发送音频数据
    for i in range(total_chunks):
        start = i * _CHUNK_SIZE
        end = min(start + _CHUNK_SIZE, len(audio_bytes))
        chunk = audio_bytes[start:end]

        is_last = (i == total_chunks - 1)
        hdr = _HDR_AUDIO_ONLY_LAST if is_last else _HDR_AUDIO_ONLY
        size_bytes = struct.pack(">I", len(chunk))
        ws.send_binary(hdr + size_bytes + chunk)

        if is_last:
            print(f"[STT] Sent chunk {i+1}/{total_chunks} (LAST, {len(chunk)} bytes)")
        elif (i + 1) % 20 == 0:
            print(f"[STT] Sent chunk {i+1}/{total_chunks}")

        if not is_last:
            time.sleep(_CHUNK_INTERVAL)

    print("[STT] All chunks sent, waiting for result...")

    # ③ nostream 模式：服务端只在收到最后一包后才返回结果
    final_text = ""
    while True:
        frame = ws.recv()
        if not frame:
            break

        msg_type, msg_flag, payload = _parse_server_frame(frame)

        if msg_type == 0b1001:  # Full server response
            if isinstance(payload, dict):
                result = payload.get("result", {})
                text = result.get("text", "")
                if text:
                    final_text = text
                    print(f"[STT] Result: \"{text[:80]}\"")
            if msg_flag == 0b0011:
                break

        elif msg_type == 0b1111:  # Error
            ws.close()
            raise Exception(f"WebSocket 服务端错误: {payload}")

    ws.close()
    print(f"Recognized Text: {final_text}\n=============================================")

    if not final_text:
        raise Exception("未能识别出语音文字内容，识别结果为空。请检查麦克风权限和录音质量。")

    return final_text
