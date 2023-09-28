from bson import ObjectId
from flask import Blueprint, request, session, Response
from flask_login import login_required, current_user, login_user, logout_user

import json
import time
from random import choice

from werkzeug.security import generate_password_hash, check_password_hash

from discord_webhook import DiscordEmbed

from utils import User, users
from utils import send_error, send_success
from utils import webhook_send
from var import *

authorization = Blueprint('authorization', __name__)


@authorization.route(f"{AUTH_PATH}/login", methods=['POST'])
def login() -> Response:
    nickname = request.form.get('nickname')
    password = request.form.get('pw')
    
    user = users.find_one({'nickname': nickname})

    if user is not None and check_password_hash(user["password_hash"], password):
        tmp_user = User(str(user["_id"]))
        login_user(tmp_user)
        session.permanent = True
        return send_success()
    return send_error("Benutzername oder Passwort waren falsch! Bitte versuch es erneut.")


@authorization.route(f"{AUTH_PATH}/signup", methods=['POST'])
def signup() -> Response:
    nickname = request.form.get("nickname")
    password = request.form.get("pw")

    tmp_user = users.find_one({'nickname': nickname})
    if tmp_user is not None:
        return send_error("Nutzername ist schon vergeben!")

    if (len(nickname) < 3) or (len(nickname) > 15):
        return send_error("Nutzername muss zwischen 3 und 15 Zeichen lang sein!")

    if len(password) < 10:
        return send_error("Passwort muss mindestens 10 Zeichen lang sein!")

    forbidden_chars = ["`"]
    for char in forbidden_chars:
        if char in nickname:
            return send_error("Verbotenes Zeichen in Nutzername")
        if char in password:
            return send_error("Verbotenes Zeichen in Passwort")

    tmp_id = users.insert_one({
        'nickname': nickname,
        'admin': False,
        'authorized_schools': [],
        'password_hash': generate_password_hash(password, method='sha256'),
        'time_joined': time.time(),
        'settings': DEFAULT_SETTINGS
    })
    tmp_user = User(str(tmp_id.inserted_id))
    login_user(tmp_user)
    session.permanent = True
    current_user.update_settings({})
    embed = DiscordEmbed(title="User creation", color="00ff00")
    embed.add_embed_field("", f"```{nickname}```", inline=False)
    embed.add_embed_field("Account created:", f"<t:{int(time.time())}:F>", inline=False)
    webhook_send("WEBHOOK_USER_CREATION", "", embeds=[embed])
    return send_success()


@authorization.route(f'{AUTH_PATH}/logout')
@login_required
def logout() -> Response:
    logout_user()
    return send_success()


@authorization.route(f"{AUTH_PATH}/account", methods=['GET', 'DELETE'])
@login_required
def account() -> Response:
    tmp_user = current_user.get_user()
    if request.method == "GET":
        return send_success({
            key: value for key, value in tmp_user.items() if key not in ["_id", "admin", "password_hash"]
        })
    elif request.method == "DELETE":
        embed = DiscordEmbed(title="User deletion", color="ff0000")
        embed.add_embed_field("", f"```{tmp_user['nickname']}```", inline=False)
        if tmp_user.get("time_joined"):
            embed.add_embed_field("Account created:", f"<t:{int(tmp_user['time_joined'])}:F>", inline=False)
        embed.add_embed_field("Account deleted:", f"<t:{int(time.time())}:F>", inline=False)
        # embed.set_timestamp()
        webhook_send("WEBHOOK_USER_CREATION", "", embeds=[embed])
        x = users.delete_one({'_id': ObjectId(current_user.mongo_id)})
        return send_success() if x.deleted_count == 1 else send_error("Account konnte nicht gelöscht werden, bitte wende dich an den Support")


@authorization.route(f"{AUTH_PATH}/settings", methods=['GET', 'DELETE', 'POST'])
@login_required
def settings() -> Response:
    if request.method == "GET":
        return send_success(current_user.get_settings())
    elif request.method == "DELETE":
        current_user.update_settings()
        return send_success(current_user.get_settings())
    elif request.method == "POST":
        new_settings = json.loads(request.data)
        return current_user.update_settings(new_settings)


@authorization.route(f'{AUTH_PATH}/authorized_schools', methods=['GET'])
@login_required
def authorized_schools() -> Response:
    return send_success(current_user.get_authorized_schools())


def school_authorized(func):
    def wrapper_thing(*args, **kwargs):
        if not current_user.user:
            current_user.get_user()
        if kwargs.get("school_num") is None:
            return send_error("no school number provided")
        if not current_user.user.get("admin"):
            if kwargs.get("school_num") not in current_user.user.get("authorized_schools"):
                return send_error("Benutzer nicht für gewählte Schule autorisiert")
        return func(*args, **kwargs)
    return wrapper_thing


@authorization.route(f"{AUTH_PATH}/check_login", methods=["GET"])
def check_login():
    if current_user.is_authenticated:
        response_data = {'logged_in': True}
    else:
        response_data = {'logged_in': False}
    return send_success(response_data)


@authorization.route(f"{AUTH_PATH}/is_admin", methods=["GET"])
@login_required
def is_admin():
    user_is_admin = current_user.get_field("admin")
    return send_success(user_is_admin)


@authorization.route(f"{AUTH_PATH}/greeting", methods=["GET"])
@login_required
def greeting():
    if not current_user.user:
        current_user.get_user()
    greetings = []
    if current_user.get_setting("normal_greetings"):
        with open("normal_greetings.txt", "r", encoding="utf-8") as f:
            greetings += f.read().split("\n")
    if current_user.get_setting("chatgpt_greetings"):
        with open("chatgpt_greetings.txt", "r", encoding="utf-8") as f:
            greetings += f.read().split("\n")
    if not greetings:
        greetings = ["Was bitte hast du gegen Begrüßungen? 😯"]
    random_greeting = choice(greetings).format(name=current_user.user["nickname"])
    return send_success(random_greeting)

