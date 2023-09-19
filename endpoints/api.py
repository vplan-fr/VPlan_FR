from typing import List

import json
import datetime
from pathlib import Path

from discord_webhook import DiscordEmbed
from flask import Blueprint, request, Response
from flask_login import login_required, current_user
from endpoints.authorization import school_authorized

import backend.cache
import backend.load_plans
from backend.vplan_utils import find_closest_date
from utils import send_success, send_error, get_all_schools_by_number, get_all_schools
from utils import get_school_by_id
from utils import webhook_send, BetterEmbed

from var import *

api = Blueprint('api', __name__)


@api.route(f"/api/v69.420/schools", methods=["GET"])
@login_required
def schools() -> Response:
    # school_data = get_all_schools_by_number()
    school_data = get_all_schools()
    print(school_data)
    return send_success(school_data)


@api.route(f"{API_BASE_URL}/meta", methods=["GET"], endpoint="meta_api")
@login_required
@school_authorized
def meta(school_num) -> Response:
    if school_num not in VALID_SCHOOLS:
        return send_error("Schulnummer unbekannt")

    cache: backend.cache.Cache = backend.cache.Cache(Path(".cache") / school_num)
    meta_data: dict = json.loads(cache.get_meta_file("meta.json"))
    teachers_data: dict = json.loads(cache.get_meta_file("teachers.json"))["teachers"]
    forms_data: dict = json.loads(cache.get_meta_file("forms.json"))
    rooms_data: dict = json.loads(cache.get_meta_file("rooms.json"))
    dates_data: dict = json.loads(cache.get_meta_file("dates.json"))

    dates = sorted([datetime.datetime.strptime(elem, "%Y-%m-%d").date() for elem in list(dates_data.keys())])
    date = find_closest_date(dates)

    return send_success({
        "meta": meta_data,
        "teachers": teachers_data,
        "forms": forms_data,
        "rooms": rooms_data,
        "dates": dates_data,
        "date": date.strftime("%Y-%m-%d")
    })


@api.route(f"{API_BASE_URL}/plan", methods=["GET"], endpoint="plan_api")
@login_required
@school_authorized
def plan(school_num: str) -> Response:
    if school_num not in VALID_SCHOOLS:
        return send_error("Schulnummer unbekannt")

    cache = backend.cache.Cache(Path(".cache") / school_num)

    _date = request.args.get("date")
    if not _date:
        return send_error("Missing date url parameter (YYYY-MM-DD).")

    try:
        date = datetime.datetime.strptime(_date, "%Y-%m-%d").date()
    except ValueError:
        return send_error("Invalid date format. Must be YYYY-MM-DD.")

    _revision = request.args.get("revision", default=".newest")

    try:
        revision = datetime.datetime.fromisoformat(_revision) if _revision != ".newest" else ".newest"
    except ValueError:
        return send_error("Invalid revision timestamp format. Must be in ISO format.")

    try:
        data = cache.get_all_json_plan_files(date, revision)
    except FileNotFoundError:
        return send_error("Invalid date or revision.")

    return send_success(data)


@api.route(f"{API_BASE_URL}/authorize", methods=["POST"])
@login_required
def authorize(school_num: str) -> Response:
    school_data = get_school_by_id(school_num)
    embed = BetterEmbed(title="AUTH ATTEMPT", color="0000ff")
    embed.add_embed_field("School number:", f"```{school_num}```", inline=False)
    embed.add_embed_field("Schulname:", f"{school_data.get('display_name') if school_data else 'Unbekannt'}", inline=False)
    embed.add_embed_field("Nickname of user:", f"{current_user.get_field('nickname')}", inline=False)
    embed.add_embed_field("username:", f"```{request.form.get('username')}```", inline=False)
    embed.add_cleaned_field("password:", f"||```{request.form.get('pw')}```||", inline=False)
    embed.set_footer("A detailed log can be found under .cache/auth.log")
    embed.set_timestamp()
    webhook_send("WEBHOOK_SCHOOL_AUTHORIZATION", embeds=[embed])
    with open(".cache/auth.log", "a") as f:
        f.write(f"New auth attempt for {request.form.get('school_num')}\nargs: {request.args}\nbody: {request.form}")
    if not school_data:
        return send_error("Schulnummer unbekannt, falls du eine Schule hinzufügen möchtest, nimm bitte Kontakt mit uns auf")
    username = request.form.get("username")
    if username is None:
        return send_error("Kein Nutzername für die Schule angegeben")
    pw = request.form.get("pw")
    if pw is None:
        return send_error("Kein Passwort für die Schule angegeben")
    if username != school_data["hosting"]["creds"]["students"]["username"] or pw != \
            school_data["hosting"]["creds"]["students"]["password"]:
        return send_error("Nutzername oder Password falsch")
    current_user.authorize_school(school_num)
    return send_success()


@api.route(f"{API_BASE_URL}/instant_authorization", methods=["GET"])
@login_required
def instant_authorize(school_num: str) -> Response:
    if "username" not in request.args:
        return send_error("Nutzername benötigt")
    if "pw" not in request.args:
        return send_error("Passwort benötigt")
    school_data = get_school_by_id(school_num)
    if not school_data:
        return send_error("Schulnummer nicht gefunden")
    username = request.args.get("username")
    pw = request.args.get("username")
    if username != school_data["username"] or pw != school_data["password"]:
        return send_error("Nutzername oder Passwort falsch")
    current_user.authorize_school(school_num)
    return send_success()


@api.route(f"{API_BASE_URL}/preferences", methods=['GET', 'POST'])
@login_required
def preferences(school_num: str) -> Response:
    cache = backend.cache.Cache(Path(".cache") / school_num)

    current_preferences = current_user.get_user().get("preferences", {})

    if request.method == "GET":
        if "form" in request.args:
            return send_success(current_preferences.get(school_num, {}).get(request.args["form"], []))
        else:
            return send_success(current_preferences.get(school_num, {}))

    elif request.method == "POST":
        try:
            class_groups = json.loads(cache.get_meta_file("forms.json"))["forms"][request.args["form"]]["class_groups"]
        except KeyError:
            return send_error(f"Invalid or missing form {request.args.get('form')!r}!")

        stored_classes = []

        try:
            data = json.loads(request.data)
            print(data)
        except json.JSONDecodeError:
            return send_error("Invalid JSON data.")

        for requested_class in data:
            if requested_class not in class_groups:
                continue

            stored_classes.append(requested_class)

        current_preferences.setdefault(school_num, {})[request.args["form"]] = stored_classes

        current_user.set_user_preferences(current_preferences)

        return send_success()


@api.route(f"/api/v69.420/changelog", methods=["GET", "POST"])
@login_required
def changelog() -> Response:
    read_changelog: List[int] = current_user.get_user().get("read_changelog", [])
    with open("changelog.json", "r", encoding="utf-8") as f:
        all_changelog = json.load(f)
    for ind, value in enumerate(all_changelog):
        if "content" not in value:
            filename = f"docs/changelog/{value['version']}.md"
            if not os.path.exists(f"docs/changelog/{value['version']}.md"):
                value["content"] = ""
            else:
                with open(filename, "r", encoding="utf-8") as f:
                    value["content"] = f.read()
        all_changelog[ind] = value
    if request.method == "GET":
        all_changelog = [[ind, value] for ind, value in enumerate(all_changelog)]
        user_changelog = [[ind in read_changelog, value] for ind, value in all_changelog]
        return send_success(user_changelog)
    if request.method == "POST":
        try:
            num = int(request.data)
        except ValueError:
            return send_error("Keine Zahl")
        if num > len(all_changelog):
            return send_error("Zu große Zahl")
        if num in read_changelog:
            return send_error("Nachricht schon gelesen")
        read_changelog.append(num)
        read_changelog.sort()
        current_user.update_field("read_changelog", read_changelog)
        return send_success()


@api.route(f"/api/v69.420/contact", methods=["POST"])
def contact() -> Response:
    data = json.loads(request.data)
    category = data.get("category")
    if not category:
        return send_error("Keine Nachrichtenkategorie angegeben")
    if category not in ["bug", "enhancement", "authorization", "advertisement", "sponsoring", "questions", "else"]:
        return send_error("Nachrichtenkategorie nicht valide")
    person = data.get("person")
    if not person:
        return send_error("Keine Person angegeben")
    if person not in ["student", "teacher", "head_teacher", "developer", "else"]:
        return send_error("Person nicht valide")
    contact_data = data.get("contact_data")
    if not contact_data:
        return send_error("Keine Kontaktdaten angegeben")
    message = data.get("message")
    if not message:
        return send_error("Keine Nachricht angegeben")

    embed = BetterEmbed(title="Neue Kontaktaufnahme!", color="ffffff", inline=False)
    embed.add_embed_field("Kategorie:", category, inline=False)
    embed.add_embed_field("Nutzerart:", person, inline=False)
    if current_user:
        embed.add_embed_field("Nutzername:", current_user.get_field("nickname"), inline=False)
    else:
        embed.add_embed_field("Nutzername:", "Nicht eingeloggt", inline=False)
    embed.add_cleaned_field("Kontaktdaten:", f"```{contact_data}```", inline=False)
    embed.add_cleaned_field("Nachricht:", f"```{message}```", inline=False)
    webhook_send("WEBHOOK_CONTACT", embeds=[embed])
    return send_success()

