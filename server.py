import os
import json
from flask import Flask, send_from_directory, request, jsonify
import random

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
        return {"error": "school not in database"}
    with open(f".cache/{school_num}/meta.json", "r") as f:
        data = json.load(f)
        return jsonify(data)


@app.route(f"{API_BASE_URL}/plan")
def plan(school_num: str):
    print("getting plan")
    if school_num not in VALID_SCHOOLS:
        return {"error": "school not in database"}
    date = request.args.get("date")
    if not date:
        return {"error": "please specify a date"}
    if date not in os.listdir(f".cache/{school_num}/plans"):
        return {"error": "date not found"}
    revision_stamp = request.args.get("revision", ".newest")
    if revision_stamp not in os.listdir(f".cache/{school_num}/plans/{date}"):
        return {"error": "revision not found"}
    data = {}
    for plan_type in ["plans", "rooms"]:
        with open(f".cache/{school_num}/plans/{date}/{revision_stamp}/{plan_type}.json", "r") as f:
            data[plan_type] = json.load(f)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
