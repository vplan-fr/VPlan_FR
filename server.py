import datetime
import os
import json
from pathlib import Path

from flask import Flask, send_from_directory, request, Response

import backend.cache
import backend.load_plans
from backend.vplan_utils import find_closest_date

VALID_SCHOOLS = os.listdir(".cache")
API_BASE_URL = "/api/v69.420/<school_num>"

app = Flask(__name__)


# COMPILED SVELTE FILES


@app.route("/")
def base():
    return send_from_directory('client/public', 'index.html')


@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)


# PLAN JSON API


@app.route(f"{API_BASE_URL}/meta")
def meta(school_num):
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
        "date": date.strftime("%Y-%m-%d")
    }), mimetype='application/json')


@app.route(f"{API_BASE_URL}/plan")
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
        plan_data = cache.get_plan_file(date, revision, "plans.json")
        rooms_data = cache.get_plan_file(date, revision, "rooms.json")
        info_data = cache.get_plan_file(date, revision, "info.json")
        exams_data = cache.get_plan_file(date, revision, "exams.json")
    except FileNotFoundError:
        return {"error": "Invalid revision."}

    return {
        "plans": json.loads(plan_data),
        "rooms": json.loads(rooms_data),
        "exams": json.loads(exams_data),
        "info": json.loads(info_data)
    }


@app.route(f"{API_BASE_URL}/authorize", methods=["GET", "POST"])
def authorize(school_num: str):
    with open(".cache/auth.log", "a") as f:
        f.write(f"New auth attempt for {school_num}\nargs: {request.args}\nbody: {request.form}")
    return {"error": "not yet implemented"}


if __name__ == "__main__":
    app.run(debug=True)
