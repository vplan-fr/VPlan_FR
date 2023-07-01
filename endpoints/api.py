import json
import datetime
from pathlib import Path

from flask import Blueprint, request, Response, jsonify
from flask_login import login_required, current_user
from endpoints.authorization import school_authorized

import backend.cache
import backend.load_plans
from backend.vplan_utils import find_closest_date

from var import *


api = Blueprint('api', __name__)


@api.route(f"{API_BASE_URL}/schools", methods=["GET"])
def schools() -> Response:
    with open("creds.json", "r") as f:
        creds: dict = json.load(f)
    return jsonify([
        {
            k: v for k, v in elem.items() if k in ["school_number", "school_name", "display_name"]
        } for elem in creds.values()
    ])


@api.route(f"{API_BASE_URL}/meta", methods=["GET"], endpoint="meta_api")
@login_required
@school_authorized
def meta(school_num) -> Response:
    if school_num not in VALID_SCHOOLS:
        return jsonify({"error": "Invalid school."})

    cache = backend.cache.Cache(Path(".cache") / school_num)
    meta_data = json.loads(cache.get_meta_file("meta.json"))
    teachers_data = json.loads(cache.get_meta_file("teachers.json"))["teachers"]
    forms_data = json.loads(cache.get_meta_file("forms.json"))
    rooms_data = json.loads(cache.get_meta_file("rooms.json"))
    dates_data = json.loads(cache.get_meta_file("dates.json"))

    dates = sorted([datetime.datetime.strptime(elem, "%Y-%m-%d").date() for elem in list(dates_data.keys())])
    date = find_closest_date(dates)

    return Response(json.dumps({
        "meta": meta_data,
        "teachers": teachers_data,
        "forms": forms_data,
        "rooms": rooms_data,
        "dates": dates_data,
        "date": date.strftime("%Y-%m-%d")
    }), mimetype='application/json')


@api.route(f"{API_BASE_URL}/plan", methods=["GET"], endpoint="plan_api")
@login_required
@school_authorized
def plan(school_num: str) -> Response:
    if school_num not in VALID_SCHOOLS:
        return jsonify({"error": "Invalid school."})

    cache = backend.cache.Cache(Path(".cache") / school_num)

    _date = request.args.get("date")
    if not _date:
        return jsonify({"error": "Missing date url parameter (YYYY-MM-DD)."})

    try:
        date = datetime.datetime.strptime(_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Must be YYYY-MM-DD."})

    _revision = request.args.get("revision", default=".newest")

    try:
        revision = datetime.datetime.fromisoformat(_revision) if _revision != ".newest" else ".newest"
    except ValueError:
        return jsonify({"error": "Invalid revision timestamp format. Must be in ISO format."})

    try:
        data = cache.get_all_json_plan_files(date, revision)
    except FileNotFoundError:
        return jsonify({"error": "Invalid revision."})

    return jsonify(data)


@api.route(f"/authorize", methods=["POST"])
def authorize() -> Response:
    school_num = request.form.get("school_num")
    if school_num is None:
        return jsonify({"error": "no school number provided"})
    with open(".cache/auth.log", "a") as f:
        f.write(f"New auth attempt for {request.form.get('school_num')}\nargs: {request.args}\nbody: {request.form}")
    with open("creds.json", "r") as f:
        creds = json.load(f)
    if school_num not in creds:
        return jsonify({"error": "school number not known, please contact us, if you want to provide additional credentials"})
    username = request.form.get("username")
    if username is None:
        return jsonify({"error": "school username not provided"})
    pw = request.form.get("pw")
    if pw is None:
        return jsonify({"error": "school password not provided"})
    if username != creds[school_num]["username"] or pw != creds[school_num]["password"]:
        return jsonify({"error": "username or password wrong"})
    current_user.authorize_school(school_num)
    return Response("Success!")


@api.route(f"{API_BASE_URL}/instant_authorization", methods=["GET"])
@login_required
def instant_authorize(school_num: str) -> Response:
    if "username" not in request.args:
        return jsonify({"error": "username required"})
    if "pw" not in request.args:
        return jsonify({"error": "password required"})
    with open("creds.json", "r") as f:
        creds = json.load(f)
    if school_num not in creds:
        return jsonify({"error": "school number not found"})
    username = request.args.get("username")
    pw = request.args.get("username")
    if username != creds[school_num]["username"] or pw != creds[school_num]["password"]:
        return jsonify({"error": "username or password wrong"})
    current_user.authorize_school(school_num)
    return Response("Success!")
