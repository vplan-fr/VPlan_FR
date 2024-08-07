import re


def validate_bool(elem):
    try:
        bool(elem)
        return True
    except Exception:
        return False


def validate_color(elem):
    if not re.fullmatch(r'^#(?:[0-9a-fA-F]{3}){1,2}$', elem):
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
    "show_revision_selector": {
        "default": False,
        "type": "bool",
    },
    "day_switch_keys": {
        "default": True,
        "type": "bool",
    },
    "background_color": {
        "default": "#121212",
        "type": "color",
    },
    "accent_color": {
        "default": "#A860FF",
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
    "filled_in_buttons": {
        "default": True,
        "type": "bool",
    },
    "swipe_day_change": {
        "default": False,
        "type": "bool",
    },
    "external_times": {
        "default": True,
        "type": "bool",
    },
    "load_first_favorite": {
        "default": True,
        "type": "bool",
    },
    "weekplan_default": {
        "default": False,
        "type": "bool",
    },
    "filled_in_weekplan": {
        "default": False,
        "type": "bool"
    }
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
