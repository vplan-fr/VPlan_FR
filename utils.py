from typing import List

import os
import re
import pymongo
from bson import ObjectId
from werkzeug.security import safe_join
from copy import deepcopy
import contextlib
import hashlib

from flask import Flask, Response, jsonify, request
from flask_login import UserMixin, current_user

from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed

from var import *

load_dotenv()

db = pymongo.MongoClient(os.getenv("MONGO_URL") if os.getenv("MONGO_URL") else "", 27017).vplan
users = db.user


def send_success(data=None) -> Response:
    if data is None:
        data = {}
    return jsonify({"success": True, "data": data})


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
        cur_settings = deepcopy(DEFAULT_SETTINGS)
        user_settings = self.user.get("settings", {})
        for setting, value in user_settings.items():
            cur_settings[setting] = value
        return cur_settings

    def update_settings(self, user_settings=DEFAULT_SETTINGS) -> Response:
        self.get_user()

        new_settings = {}
        for setting, setting_data in SETTINGS.items():
            validate_function = TYPE_FUNCTIONS[setting_data["type"]]["validation"]
            cur_setting = user_settings.get(setting, setting_data["default"])
            if not validate_function(cur_setting):
                send_error(f"ungültiger Wert für {cur_setting} Einstellung({setting_data['type']} erwartet)")
            conversion_function = TYPE_FUNCTIONS[setting_data["type"]]["conversion"]
            try:
                cur_setting = conversion_function(cur_setting)
            except Exception:
                send_error(f"ungültiger Wert für {cur_setting} Einstellung ({setting_data['type']} erwartet)")
            new_settings[setting] = cur_setting

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


def webhook_send(key: str, message: str = "", embeds: List[DiscordEmbed] = None):
    meta_env = "WEBHOOK_META"
    if not request or request.host.startswith("127.0.0.1"):
        meta_env = "WEBHOOK_TEST"
        key = "WEBHOOK_TEST"
    embeds = [] if not embeds else embeds
    key = key.upper()
    if not os.getenv(key):
        return
    url = os.getenv(key)
    webhook = DiscordWebhook(url=url, content=message, username="VPlan-Bot", avatar_url="https://vplan.fr/static/images/icons/android-chrome-192x192.png")

    for embed in embeds:
        webhook.add_embed(embed)
    if request:
        if os.getenv("WEBHOOK_META"):
            meta_webhook = DiscordWebhook(url=os.getenv(meta_env), content=message, username="VPlan-Bot", avatar_url="https://vplan.fr/static/images/icons/android-chrome-192x192.png")
            meta_embed = DiscordEmbed(title="Metadaten", color="808080")
            if current_user:
                meta_embed.add_embed_field("Username:", f"{current_user.get_field('nickname')}", inline=False)
            meta_embed.add_embed_field("IP-Adresse:", f"`{request.remote_addr}`\n more info at https://whatismyipaddress.com/ip/{request.remote_addr}", inline=False)
            meta_embed.add_embed_field("User-Agent:", f"`{request.headers.get('user-agent')}`")
            meta_webhook.add_embed(meta_embed)
            meta_webhook.execute()

    webhook.execute()
    return


if __name__ == "__main__":
    new_embed = DiscordEmbed(title="Moin again", description="Test", color="03b2f8")
    new_embed.set_author("VPlan Bot")
    webhook_send("WEBHOOK_TEST", "Hi guys")



