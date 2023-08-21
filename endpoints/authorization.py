from bson import ObjectId
from flask import Blueprint, request, session, Response, jsonify
from flask_login import login_required, current_user, login_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash
from utils import User, users
import time

authorization = Blueprint('authorization', __name__)


@authorization.route('/login', methods=['POST'])
def login() -> Response:
    nickname = request.form.get('nickname')
    password = request.form.get('pw')
    
    user = users.find_one({'nickname': nickname})

    if user is not None and check_password_hash(user["password_hash"], password):
        tmp_user = User(str(user["_id"]))
        login_user(tmp_user)
        session.permanent = True
        print("logged in!!!")
        return Response("Success!!")
    return jsonify({"error": "Wrong username or password"})


@authorization.route('/signup', methods=['POST'])
def signup() -> Response:
    nickname = request.form.get("nickname")
    password = request.form.get("pw")

    tmp_user = users.find_one({'nickname': nickname})
    if tmp_user is not None:
        return jsonify({"error": "username already taken"})

    if (len(nickname) < 3) or (len(nickname) > 15):
        return jsonify({"error": "username has to have length between 3 and 15 characters"})

    if len(password) < 10:
        return jsonify({"error": "password needs to have at least 10 characters"})

    tmp_id = users.insert_one({
        'nickname': nickname,
        'admin': False,
        'authorized_schools': [],
        'password_hash': generate_password_hash(password, method='sha256'),
        'time_joined': time.time(),
        'settings': {}
    })
    tmp_user = User(str(tmp_id.inserted_id))
    login_user(tmp_user)
    session.permanent = True
    current_user.update_settings({})
    return Response("Success!!")


@authorization.route('/logout')
def logout() -> Response:
    logout_user()
    return Response("Success!!")


@authorization.route('/account', methods=['GET', 'DELETE'])
@login_required
def account() -> Response:
    if request.method == "GET":
        tmp_user = current_user.get_user()
        return jsonify({
                'nickname': tmp_user['nickname'], 
                'authorized_schools': tmp_user['authorized_schools'], 
                'preferences': tmp_user['preferences'], 
                'settings': tmp_user['settings'], 
                'time_joined': tmp_user['time_joined']
            })
    else:
        x = users.delete_one({'_id': ObjectId(current_user.mongo_id)})
        return jsonify({"success": True}) if x.deleted_count == 1 else jsonify({"success": False})


def school_authorized(func):
    def wrapper_thing(*args, **kwargs):
        if not current_user.user:
            current_user.get_user()
        if kwargs.get("school_num") is None:
            return {"error": "no school number provided"}
        if not current_user.user.get("admin"):
            if kwargs.get("school_num") not in current_user.user.get("authorized_schools"):
                return {"error": "user not authorized for specified school"}
        return func(*args, **kwargs)
    return wrapper_thing


@authorization.route("/check_login", methods=["GET"])
def check_login():
    if current_user.is_authenticated:
        response_data = {'logged_in': True}
    else:
        response_data = {'logged_in': False}
    return jsonify(response_data)

