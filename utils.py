import os
import re
import pymongo
from bson import ObjectId
from werkzeug.security import safe_join
import contextlib
import hashlib

from flask import Flask, make_response, Response, jsonify
from flask_login import UserMixin, current_user

from dotenv import load_dotenv

from var import *

load_dotenv()

db = pymongo.MongoClient(os.getenv("MONGO_URL") if os.getenv("MONGO_URL") else "", 27017).vplan
users = db.user


class User(UserMixin):
    def __init__(self, mongo_id: str):
        self.mongo_id = mongo_id
        self.user = None

    def get_id(self):
        return self.mongo_id

    def get_user(self):
        self.user = users.find_one({'_id': ObjectId(self.mongo_id)})
        return self.user

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

    def update_settings(self, user_settings: DEFAULT_SETTINGS) -> Response:
        self.get_user()
        authorized_schools = self.user.get("authorized_schools", [])

        print(user_settings)
        new_settings = {}
        try:
            new_settings["show_plan_toasts"] = bool(user_settings.get("show_plan_toasts", False))
        except Exception:
            return make_response('Invalid value for show_plan_toasts', 400)
        try:
            new_settings["day_switch_keys"] = bool(user_settings.get("day_switch_keys", True))
        except Exception:
            return make_response('Invalid value for day_switch_keys', 400)
        new_settings["background_color"] = user_settings.get("background_color", "#121212")
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_settings["background_color"]):
            return make_response('Invalid Color for background_color', 400)
        new_settings["accent_color"] = user_settings.get("accent_color", "#BB86FC")
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_settings["accent_color"]):
            return make_response('Invalid Color for accent_color', 400)

        new_settings["favorite"] = user_settings.get("favorite", [])
        if new_settings["favorite"]:
            if new_settings["favorite"][0] not in authorized_schools:
                return make_response('Schoolnumber not authorized for user', 400)
            # if new_settings["favorite"][1] not in MetaExtractor(new_settings["favorite"][0]).course_list():
            #    return make_response('Course not recognized', 400)

        users.update_one({'_id': ObjectId(self.mongo_id)}, {"$set": {'settings': new_settings}})
        return jsonify({"success": True})

    def update_preferences(self, preferences: {}):
        #available_courses =
        users.update_one({'_id': ObjectId(self.mongo_id)}, {"$set": {'preferences': preferences}})

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


def set_user_preferences(user_id, preferences):
    users.update_one({'_id': ObjectId(user_id)}, {'$set': {'preferences': preferences}})
    return "Success"

