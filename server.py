from __future__ import annotations

import datetime
import os
import json
from pathlib import Path

from flask import send_from_directory, request, Response
from flask_login import LoginManager, login_required, current_user
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect

import backend.cache
import backend.load_plans
from backend.vplan_utils import find_closest_date
from authorization import authorization

from utils import User, AddStaticFileHashFlask, get_user

VALID_SCHOOLS = os.listdir(".cache")
API_BASE_URL = "/api/v69.420/<school_num>"

app = AddStaticFileHashFlask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "DEBUG_KEY"
app.secret_key = SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 32140800

compress = Compress()
compress.init_app(app)

# csrf = CSRFProtect(app)
# csrf.init_app(app)


# authorization (+ endpoints)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
app.register_blueprint(authorization)


@login_manager.user_loader
def user_loader(user_id: str) -> User | None:
    tmp_user = get_user(user_id)
    if tmp_user is None:
        return
    tmp_user = User(user_id)
    return tmp_user


@login_manager.unauthorized_handler
def unauthorized_callback():
    return {"error": "request without authorization"}


# COMPILED SVELTE FILES
@app.route("/")
def base():
    return send_from_directory('client/public', 'index.html')


@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)


# API endpoints

@app.route(f"{API_BASE_URL}/schools")
def schools():
    with open("creds.json", "r") as f:
        creds: dict = json.load(f)
    return [
        {
            k: v for k, v in elem.items() if k in ["school_number", "school_name", "display_name"]
        } for elem in creds.values()
    ]


@app.route(f"{API_BASE_URL}/meta")
# @login_required
def meta(school_num):
    print(current_user)
    if school_num not in VALID_SCHOOLS:
        return {"error": "Invalid school."}

    cache = backend.cache.Cache(Path(".cache") / school_num)
    meta_data = json.loads(cache.get_meta_file("meta.json"))
    teachers_data = json.loads(cache.get_meta_file("teachers.json"))["teachers"]
    forms_data = json.loads(cache.get_meta_file("forms.json"))
    rooms_data = json.loads(cache.get_meta_file("rooms.json"))
    dates_data = json.loads(cache.get_meta_file("dates.json"))

    dates = sorted([datetime.datetime.strptime(elem, "%Y-%m-%d").date() for elem in list(dates_data.keys())])
    date = find_closest_date(dates)
    print(date)

    return Response(json.dumps({
        "meta": meta_data,
        "teachers": teachers_data,
        "forms": forms_data,
        "rooms": rooms_data,
        "dates": dates_data,
        "date": date.strftime("%Y-%m-%d")
    }), mimetype='application/json')


@app.route(f"{API_BASE_URL}/plan")
#@login_required
def plan(school_num: str):
    if school_num not in VALID_SCHOOLS:
        return {"error": "Invalid school."}

    cache = backend.cache.Cache(Path(".cache") / school_num)

    _date = request.args.get("date")
    if not _date:
        return {"error": "Missing date url parameter (YYYY-MM-DD)."}

    try:
        date = datetime.datetime.strptime(_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Must be YYYY-MM-DD."}

    _revision = request.args.get("revision", default=".newest")

    try:
        revision = datetime.datetime.fromisoformat(_revision) if _revision != ".newest" else ".newest"
    except ValueError:
        return {"error": "Invalid revision timestamp format. Must be in ISO format."}

    try:
        data = cache.get_all_json_plan_files(date, revision)
    except FileNotFoundError:
        return {"error": "Invalid revision."}

    return data


@app.route(f"{API_BASE_URL}/authorize", methods=["GET", "POST"])
def authorize(school_num: str):
    with open(".cache/auth.log", "a") as f:
        f.write(f"New auth attempt for {school_num}\nargs: {request.args}\nbody: {request.form}")
    return {"error": "not yet implemented"}


@app.route(f"{API_BASE_URL}/instant_authorization")
#@login_required
def instant_authorize(school_num: str):
    if "username" not in request.args:
        return {"error": "username required"}
    if "pw" not in request.args:
        return {"error": "password required"}
    with open("creds.json", "r") as f:
        creds = json.load(f)
    if school_num not in creds:
        return {"error": "school number not found"}
    username = request.args.get("username")
    pw = request.args.get("username")
    if username != creds[school_num]["username"] or pw != creds[school_num]["password"]:
        return {"error": "username or password wrong"}
    current_user.authorize_school(school_num)
    return "User authorized"


if __name__ == "__main__":
    app.run(debug=True)
