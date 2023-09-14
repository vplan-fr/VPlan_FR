import os


VALID_SCHOOLS = os.listdir(".cache")
API_BASE_URL = "/api/v69.420/<school_num>"
AUTH_PATH = "/auth"

DEFAULT_SETTINGS = {
    "normal_greetings": True,
    "chatgpt_greetings": False,
    "day_switch_keys": False,
    "background_color": "#121212",
    "accent_color": "#bb86fc",
    "text_color": "#ffffff",
    "cancelled_color": "#ff1744",
    "rainbow": False,
    "favorite": [],
}
