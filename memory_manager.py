import json
import os

PROFILE_FILE = "student_profile.json"
SETTINGS_FILE = "settings.json"
CHAT_HISTORY_FILE = "chat_history.json"

DEFAULT_PROFILE = {
    "basic_info": {
        "name": "未知",
        "age": "未知",
        "grade": "未知"
    },
    "interests": [],
    "educational_profile": {
        "personality": {
            "status": "待评估",
            "hypotheses": [],
            "confirmed_traits": ""
        },
        "behavioral_traits": {
            "status": "待评估",
            "hypotheses": [],
            "confirmed_traits": ""
        },
        "learning_style": {
            "status": "待评估",
            "hypotheses": [],
            "confirmed_traits": ""
        },
        "math_capability": {
            "status": "待评估",
            "hypotheses": [],
            "confirmed_traits": ""
        }
    },
    "expert_inner_thoughts": "",
    "assessment_progress": "未开始，需通过自然对话逐步摸底四大维度。"
}

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_PROFILE

def save_profile(profile_data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=4)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_settings(settings_data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings_data, f, ensure_ascii=False, indent=4)

def load_chat_history():
    if not os.path.exists(CHAT_HISTORY_FILE):
        return None
    with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
            return None
        except json.JSONDecodeError:
            return None

def save_chat_history(messages):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)
