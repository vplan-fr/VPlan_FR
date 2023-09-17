import os
import re
import json


VALID_SCHOOLS = os.listdir(".cache")
API_BASE_URL = "/api/v69.420/<school_num>"
AUTH_PATH = "/auth"


def validate_bool(elem):
    try:
        bool(elem)
        return True
    except Exception:
        return False


def validate_color(elem):
    if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', elem):
        return False
    return True


SETTINGS = {
    "normal_greetings": {
        "default": True,
        "type": "bool",
    },
    "chatgpt_greetings": {
        "default": False,
        "type": "bool",
    },
    "show_plan_file_timestamps": {
        "default": False,
        "type": "bool",
    },
    "day_switch_keys": {
        "default": False,
        "type": "bool",
    },
    "background_color": {
        "default": "#121212",
        "type": "color",
    },
    "accent_color": {
        "default": "#bb86fc",
        "type": "color",
    },
    "text_color": {
        "default": "#ffffff",
        "type": "color",
    },
    "cancelled_color": {
        "default": "#ff1744",
        "type": "color",
    },
    "rainbow": {
        "default": False,
        "type": "bool",
    },
}

TYPE_FUNCTIONS = {
    "bool": {
        "validation": validate_bool,
        "conversion": bool,
    },
    "color": {
        "validation": validate_color,
        "conversion": str,
    }
}

DEFAULT_SETTINGS = {
    key: value["default"] for key, value in SETTINGS.items()
}


with open("creds.json", "r", encoding="utf-8") as f:
    CREDS = json.load(f)

