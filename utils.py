import os
import re
import pymongo
from bson import ObjectId
from werkzeug.security import safe_join
import contextlib
import hashlib

from flask import Flask, Response, jsonify
from flask_login import UserMixin, current_user

from dotenv import load_dotenv

from var import *

load_dotenv()

db = pymongo.MongoClient(os.getenv("MONGO_URL") if os.getenv("MONGO_URL") else "", 27017).vplan
users = db.user


def send_success(data=None) -> Response:
    if data is not None:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": True})


def send_error(msg: str) -> Response:
    return jsonify({"success": False, "error": msg})


class User(UserMixin):
    def __init__(self, mongo_id: str):
        self.mongo_id = mongo_id
        self.user = None

    def get_id(self):
        return self.mongo_id

    def get_user(self):
        self.user = users.find_one({'_id': ObjectId(self.mongo_id)})
        return self.user

    def update_field(self, field, value):
        self.get_user()
        users.update_one({'_id': ObjectId(self.mongo_id)}, {"$set": {field: value}})

    def get_field(self, field):
        self.get_user()
        return self.user.get(field)

    def get_authorized_schools(self):
        self.get_user()
        return self.user.get("authorized_schools")

    def authorize_school(self, school_num: str):
        self.get_user()
        tmp_authorized_schools = self.user.get("authorized_schools", [])
        if school_num not in tmp_authorized_schools:
            tmp_authorized_schools.append(school_num)
            users.update_one({'_id': ObjectId(self.mongo_id)},
                             {"$set": {'authorized_schools': tmp_authorized_schools}})

    def get_settings(self):
        self.get_user()
        cur_settings = DEFAULT_SETTINGS
        user_settings = self.user.get("settings", {})
        for setting, value in user_settings.items():
            cur_settings[setting] = value
        return cur_settings

    def update_settings(self, user_settings: DEFAULT_SETTINGS) -> Response:
        self.get_user()
        authorized_schools = self.user.get("authorized_schools", [])

        new_settings = {}
        try:
            new_settings["normal_greetings"] = bool(user_settings.get("normal_greetings", False))
        except Exception:
            return send_error("ungültiger Wert für normal_greetings Einstellung")
        try:
            new_settings["chatgpt_greetings"] = bool(user_settings.get("chatgpt_greetings", False))
        except Exception:
            return send_error("ungültiger Wert für chatgpt_greetings Einstellung")
        try:
            new_settings["day_switch_keys"] = bool(user_settings.get("day_switch_keys", True))
        except Exception:
            return send_error("ungültiger Wert für day_switch_keys Einstellung")
        new_settings["background_color"] = user_settings.get("background_color", "#121212")
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_settings["background_color"]):
            return send_error("ungültiger Wert für background_color Einstellung")
        new_settings["accent_color"] = user_settings.get("accent_color", "#BB86FC")
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_settings["accent_color"]):
            return send_error("ungültiger Wert für accent_color Einstellung")

        new_settings["favorite"] = user_settings.get("favorite", [])
        if new_settings["favorite"]:
            if new_settings["favorite"][0] not in authorized_schools:
                return send_error("Schulnummer für Benutzer nicht authentifiziert")
            # if new_settings["favorite"][1] not in MetaExtractor(new_settings["favorite"][0]).course_list():
            #    return make_response('Course not recognized', 400)

        users.update_one({'_id': ObjectId(self.mongo_id)}, {"$set": {'settings': new_settings}})
        return send_success()

    def set_user_preferences(self, preferences):
        users.update_one({'_id': ObjectId(self.mongo_id)}, {'$set': {'preferences': preferences}})
        return "Success"

    # get setting for user, if setting not set get default setting
    def get_setting(self, setting_key):
        self.get_user()
        return self.user.get("settings", {}).get(setting_key, DEFAULT_SETTINGS.get(setting_key, None))


class AddStaticFileHashFlask(Flask):
    def __init__(self, *args, **kwargs):
        super(AddStaticFileHashFlask, self).__init__(*args, **kwargs)
        self._file_hash_cache = {}

    def inject_url_defaults(self, endpoint, values):
        super(AddStaticFileHashFlask, self).inject_url_defaults(endpoint, values)
        if endpoint == "static" and "filename" in values and "site.webmanifest" not in values["filename"]:
            filepath = safe_join(self.static_folder, values["filename"])
            if os.path.isfile(filepath):
                cache = self._file_hash_cache.get(filepath)
                mtime = os.path.getmtime(filepath)
                if cache is not None:
                    cached_mtime, cached_hash = cache
                    if cached_mtime == mtime:
                        values["h"] = cached_hash
                        return
                h = hashlib.md5()
                with contextlib.closing(open(filepath, "rb")) as f:
                    h.update(f.read())
                h = h.hexdigest()
                self._file_hash_cache[filepath] = (mtime, h)
                values["h"] = h


def get_user(user_id):
    try:
        return users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return






