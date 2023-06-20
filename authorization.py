from bson import ObjectId
from flask import Blueprint, request, session
from flask_login import login_required, current_user, login_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash
from utils import User, users, get_user
import time

authorization = Blueprint('authorization', __name__, template_folder='templates')


@authorization.route('/login', methods=['POST'])
def login():
    nickname = request.form.get('nickname')
    password = request.form.get('pw')
    
    user = users.find_one({'nickname': nickname})

    if user is not None and check_password_hash(user["password_hash"], password):
        tmp_user = User(str(user["_id"]))
        login_user(tmp_user)
        session.permanent = True
        print("logged in!!!")
        return "Success!!"
    return {"error": "Wrong username or password"}


@authorization.route('/signup', methods=['POST'])
def signup():
    nickname = request.form.get("nickname")
    password = request.form.get("pw")

    tmp_user = users.find_one({'nickname': nickname})
    if tmp_user is not None:
        return {"error": "username already taken"}

    if (len(nickname) < 3) or (len(nickname) > 15):
        return {"error": "username has to have length between 3 and 15 characters"}

    if len(password) < 10:
        return {"error": "password needs to have at least 10 characters"}

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
    return "Success!!"


@authorization.route('/logout')
def logout():
    logout_user()
    return "Success!!"


@authorization.route('/account', methods=['GET', 'DELETE'])
@login_required
def account():
    if request.method == "GET":
        tmp_user = current_user.get_user()
        return {
                'nickname': tmp_user['nickname'], 
                'authorized_schools': tmp_user['authorized_schools'], 
                'preferences': tmp_user['preferences'], 
                'settings': tmp_user['settings'], 
                'time_joined': tmp_user['time_joined']
            }
    else:
        x = users.delete_one({'_id': ObjectId(current_user.mongo_id)})
        return {"success": True} if x.deleted_count == 1 else {"success": False}
