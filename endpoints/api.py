import logging
import random
from typing import List

import json
import os
import datetime
from pathlib import Path

from flask import Blueprint, request, Response
from flask_login import login_required, current_user

import backend.teacher
import utils
from endpoints.authorization import school_authorized
import endpoints.webpush

import shared.cache
from backend import vplan_utils
from utils import send_success, send_error, get_all_schools, get_school_by_id, webhook_send, BetterEmbed, VALID_SCHOOLS
from school_test import SchoolCandidate

api = Blueprint('api', __name__)


@api.route(f"/api/v69.420/schools", methods=["GET"])
@login_required
def schools() -> Response:
    if current_user.get_field("admin"):
        school_data = get_all_schools(only_shown=False)
    else:
        school_data = get_all_schools(only_shown=True, include_ids=current_user.get_authorized_schools())

    return send_success(school_data)


API_BASE_URL = "/api/v69.420/<school_num>"


@api.route(f"{API_BASE_URL}/meta", methods=["GET"], endpoint="meta_api")
@login_required
@school_authorized
def meta(school_num) -> Response:
    if school_num not in VALID_SCHOOLS:
        return send_error("Schulnummer unbekannt")

    cache: shared.cache.Cache = shared.cache.Cache(Path(".cache") / school_num)
    meta_data: dict = json.loads(cache.get_meta_file("meta.json"))
    teachers_data: dict = json.loads(cache.get_meta_file("teachers.json"))["teachers"]
    forms_data: dict = json.loads(cache.get_meta_file("forms.json"))
    rooms_data: dict = json.loads(cache.get_meta_file("rooms.json"))
    dates_data: dict = json.loads(cache.get_meta_file("dates.json"))

    dates = sorted([datetime.datetime.strptime(elem, "%Y-%m-%d").date() for elem in list(dates_data.keys())])
    date = vplan_utils.find_closest_date(dates)

    return send_success({
        "school_num": school_num,
        "meta": meta_data,
        "teachers": teachers_data,
        "forms": forms_data,
        "rooms": rooms_data,
        "dates": dates_data,
        "date": date.strftime("%Y-%m-%d") if date else None
    })


@api.route(f"{API_BASE_URL}/plan", methods=["GET"], endpoint="plan_api")
@login_required
@school_authorized
def plan(school_num: str) -> Response:
    if school_num not in VALID_SCHOOLS:
        return send_error("Schulnummer unbekannt")

    cache = shared.cache.Cache(Path(".cache") / school_num)

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
        data = {
            "info": json.loads(cache.get_plan_file(date, revision, "info.json")),
            "rooms": json.loads(cache.get_plan_file(date, revision, "rooms.json")),
            "plans": json.loads(cache.get_plan_file(date, revision, "plans.json")),
            "exams": json.loads(cache.get_plan_file(date, revision, "exams.json")),
            "is_default_plan": False
        }
    except FileNotFoundError:
        # use default plan

        if revision != ".newest":
            return send_error("Only valid timestamp for predicted default plans is '.newest'.")

        holidays = list(map(datetime.date.fromisoformat, json.loads(cache.get_meta_file("meta.json"))["free_days"]))
        default_plan_data = json.loads(cache.get_meta_file("default_plan.json"))

        newest_date = cache.get_days()[0]
        try:
            newest_date_week = json.loads(cache.get_plan_file(newest_date, ".newest", "_default_plan.json"))["week"]
        except FileNotFoundError:
            # TODO temporary fix oops, use newest _default_plan.json instead
            return send_error("No default plan available for this date.")

        week = vplan_utils.get_future_week(
            holidays=holidays,
            weeks=len(default_plan_data),
            ref_date=newest_date,
            ref_week=newest_date_week,
            date=date
        )
        try:
            plans = default_plan_data[str(week) if week is not None else "null"][str(date.weekday())]
        except KeyError:
            # raise
            return send_error("No default plan available for this date.")

        data = {
            "info": {
                "additional_info": [],
                "processed_additional_info": [],
                "timestamp": None,
                "week": vplan_utils.week_to_letter(week)
            },
            "rooms": None,
            "plans": plans,
            "exams": {},
            "is_default_plan": True
        }

    data["last_fetch"] = json.loads(cache.get_meta_file("last_fetch.json"))["timestamp"]

    return send_success(data)


@api.route(f"/api/v69.420/plan_ical/<token>", methods=["GET"])
def plan_ical(token: str) -> Response:
    out = utils.resolve_ical_token(token)
    if out is None:
        return Response(status=404)

    user_id, favorite_index = out

    user = utils.User(user_id)

    favs = user.get_field("favourites", {})

    try:
        fav = favs[favorite_index]
    except IndexError:
        return Response(status=404)

    preferences = fav.get("preferences", [])  # disabled class ids
    school_num = fav.get("school_num")
    plan_type = fav.get("plan_type")
    plan_value = fav.get("plan_value")

    cache = shared.cache.Cache(Path(".cache") / school_num)
    teachers = backend.teacher.Teachers.deserialize(json.loads(cache.get_meta_file("teachers.json")))

    import icalendar
    import html

    def generate_html_list(elements: list[str]) -> str:
        if not elements:
            return ""
        else:
            return "<ul>" + "".join(f"<li>{element}</li>" for element in elements) + "</ul>"

    if plan_type != "forms":
        calendar = icalendar.Calendar()
        calendar.add("x-wr-calname", f"NICHT UNTERSTÜTZT :( {fav['name']} (vplan.fr)")
        calendar.add("x-wr-caldesc", "Aktuell werden leider nur Klassenpläne unterstützt. :(")
        calendar.add("x-wr-timezone", "Europe/Berlin")
        calendar.add("prodid", "-//VPlan FR//vplan.fr//DE")
        calendar.add("version", "2.0")

        return Response(
            calendar.to_ical(),
            content_type="text/calendar",
        )

    calendar = icalendar.Calendar()
    calendar.add("x-wr-calname", f"{fav['name']} (vplan.fr)")
    calendar.add("x-wr-caldesc", (
        "Stundenplankalender, exportiert von vplan.fr\n"
        f"Schulnummer: „{school_num}“\n"
        f"Planart: „{plan_type}“\n"
        f"Planwert: „{plan_value}“\n"
        f"Benutzer: „{user.get_field('nickname')}“"
    ))
    calendar.add("x-wr-timezone", "Europe/Berlin")
    calendar.add("prodid", f"-//vplan.fr//{token}//DE")
    calendar.add("version", "2.0")

    utcnow = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    today = datetime.date.today()
    for date in cache.get_days():
        if date < today - datetime.timedelta(days=7 * 6):
            continue

        try:
            data = json.loads(cache.get_plan_file(date, ".newest", "plans.json", newest_before=True))
            info_data = json.loads(cache.get_plan_file(date, ".newest", "info.json", newest_before=True))
        except FileNotFoundError:
            continue

        lessons = data.get(plan_type, {}).get(plan_value, [])

        lessons = [lesson for lesson in lessons if lesson["class_number"] not in preferences]

        for i, lesson in enumerate(lessons):
            begin = datetime.datetime.combine(date, datetime.time.fromisoformat(lesson["begin"]))
            end = datetime.datetime.combine(date, datetime.time.fromisoformat(lesson["end"]))

            subject = lesson["current_class"] if lesson["current_class"] is not None else "-"

            if lesson["takes_place"]:
                if not lesson["current_teachers"] and lesson["scheduled_teachers"]:
                    teacher = ", ".join(lesson["scheduled_teachers"]) if lesson["scheduled_teachers"] else "-"
                    teacher = f"({teacher})"
                else:
                    teacher = ", ".join(lesson["current_teachers"]) if lesson["current_teachers"] else "-"
                    teacher = teacher if not lesson["teacher_changed"] else f"[{teacher}]"

                subject_ = subject if not lesson["subject_changed"] else f"[{subject}]"

                summary = f"{subject_} {teacher}"
            else:
                scheduled_subject = lesson["scheduled_class"] if lesson["scheduled_class"] is not None else "-"
                scheduled_teacher = ", ".join(lesson["scheduled_teachers"]) if lesson["scheduled_teachers"] else "-"

                summary = (
                    f"({scheduled_subject} {scheduled_teacher})"
                )

            def annotate_teacher(plan_short: str | list[str]):
                if isinstance(plan_short, list):
                    return " ".join(annotate_teacher(x) for x in plan_short)
                else:
                    teacher = teachers.query_plan_teacher(plan_short, date=date)
                    if teacher is not None:
                        return f'<abbr title="{teacher.fullest_available_name}">{plan_short}</abbr>'
                    else:
                        return plan_short

            def text_segments_to_html(segments: list[dict]) -> str:
                line_parts = []

                for s in segments:
                    if s["link"] is not None and s["link"]["type"] == "teachers":
                        line_parts.append(annotate_teacher(s["link"]["value"]))
                    else:
                        line_parts.append(html.escape(s["text"]))

                return "".join(line_parts)

            info_paragraphs = []
            for paragraph in lesson["info"]:
                lines = []
                for line in paragraph:
                    lines.append(text_segments_to_html(line["text_segments"]))

                info_paragraphs.append(lines)

            description = []

            if info_paragraphs:
                description.append("".join(
                    f"<p>{generate_html_list(paragraph)}</p>"
                    for paragraph in info_paragraphs
                ))

            def cond_b(x: str, condition: bool) -> str:
                if condition:
                    return f"<b>{x}</b>"
                else:
                    return x

            def s(x: str) -> str:
                if not x:
                    return x
                return f"<s>{x}</s>"

            current_teachers: list[str] = lesson["current_teachers"] or []
            s_teachers = set(lesson["scheduled_teachers"] or []) - set(current_teachers)
            current_rooms = lesson["current_rooms"] or []
            s_rooms = set(lesson["scheduled_rooms"] or []) - set(current_rooms)

            current_teachers = [annotate_teacher(teacher) for teacher in current_teachers]
            s_teachers = [annotate_teacher(teacher) for teacher in s_teachers]

            current_rooms = ["-"] if not (current_rooms or s_rooms) else current_rooms
            current_teachers = ["-"] if not (current_teachers or s_teachers) else current_teachers
            description.append(
                "<table>"
                # "<thead><tr><th>Attribut</th><th>Wert</th></tr></thead>"
                "<tbody>"
                f"<tr><td>Stunde: </td><td>{', '.join(map(str, lesson['periods']))}<br></td></tr>"
                f"<tr><td>Fach: </td><td>{cond_b(subject, lesson['subject_changed'])}<br></td></tr>"
                f"<tr><td>Lehrer: </td><td>{cond_b(', '.join(current_teachers) + ' ' + s(' '.join(s_teachers)), lesson['teacher_changed'])}<br></td></tr>"
                # f"<tr><td>Klassen</td><td>{', '.join(current_forms)} {s(', '.join(s_forms))}</td></tr>"
                f"<tr><td>Raum: </td><td>{', '.join(current_rooms)} {s(', '.join(s_rooms))}<br></td></tr>"
                # f"<tr><td>Klasse</td><td>{lesson['current_forms_str'] if lesson['current_forms'] else lesson['scheduled_forms_str']}</td></tr>"
                f"<tr><td>Findet statt: </td><td>{'Ja' if lesson['takes_place'] else 'Nein'}<br></td></tr>"
                "</tbody>"
                "</table>"
            )

            if i == len(lessons) - 1:
                description.append(
                    "<p>" + ("<br>".join(text_segments_to_html(segs) for segs in info_data["processed_additional_info"])) + "</p>"
                )

                description.append(
                    f"<small>Diese Anfrage:</small><br><small>{utcnow}</small><br>"
                    f"<small>Zuletzt auf neue Pläne überprüft:</small><br><small>{json.loads(cache.get_meta_file('last_fetch.json'))['timestamp']}</small><br>"
                    f"<small>Zuletzt aktualisiert:</small><br><small>{cache.get_timestamps(date)[0].isoformat()}"
                )

            event = icalendar.Event()
            event.add("summary", summary)
            event.add("description", (
                "<hr/><br>".join(description)
            ))
            event.add("dtstart", begin)
            event.add("dtend", end)
            event.add("dtstamp", datetime.datetime.now())
            event.add("uid", f"{token}-{random.randbytes(16).hex()}@vplan.fr")

            if lesson["current_rooms"]:
                event.add("location", ", ".join(lesson["current_rooms"]))

            calendar.add_component(event)

    return Response(
        calendar.to_ical(),
        content_type="text/calendar",
    )


@api.route(f"/api/v69.420/plan_ical_renew_links", methods=["GET"])
@login_required
def plan_ical_renew_links() -> Response:
    current_user.generate_ical_tokens(overwrite=True)

    return send_success()


@api.route(f"{API_BASE_URL}/authorize", methods=["POST"])
@login_required
def authorize(school_num: str) -> Response:
    school_data = get_school_by_id(school_num)
    embed = BetterEmbed(title="AUTH ATTEMPT", color="0000ff")
    embed.add_embed_field("School number:", f"```{school_num}```", inline=False)
    embed.add_embed_field("Schulname:", f"{school_data.get('display_name') if school_data else 'Unbekannt'}",
                          inline=False)
    embed.add_embed_field("Nickname of user:", f"{current_user.get_field('nickname')}", inline=False)
    embed.add_embed_field("username:", f"```{request.form.get('username')}```", inline=False)
    embed.add_cleaned_field("password:", f"||```{request.form.get('pw')}```||", inline=False)
    embed.set_footer("A detailed log can be found under .cache/auth.log")
    embed.set_timestamp()
    webhook_send("WEBHOOK_SCHOOL_AUTHORIZATION", embeds=[embed])

    with open(".cache/auth.log", "a") as f:
        f.write(f"New auth attempt for {request.form.get('school_num')}\nargs: {request.args}\nbody: {request.form}")
    if not school_data:
        return send_error(
            "Schulnummer unbekannt, falls du eine Schule hinzufügen möchtest, nimm bitte Kontakt mit uns auf")
    if school_data["hosting"]["creds"] == {}:
        current_user.authorize_school(school_num)
        return send_success()
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


@api.route(f"/api/v69.420/favorites", methods=["GET", "POST"])
@login_required
def favorites() -> Response:
    if request.method == "GET":
        current_user.generate_ical_tokens()
        return send_success(current_user.get_field("favourites", []))
    try:
        data = json.loads(request.data)
    except json.JSONDecodeError:
        return send_error("Invalid JSON data.")
    return current_user.set_favorites(data)


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
        user_changelog = [[ind, ind in read_changelog, value] for ind, value in all_changelog]
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
    if current_user.is_authenticated:
        embed.add_embed_field("Nutzername:", current_user.get_field("nickname"), inline=False)
    else:
        embed.add_embed_field("Nutzername:", "Nicht eingeloggt", inline=False)
    embed.add_cleaned_field("Kontaktdaten:", f"```{contact_data}```", inline=False)
    embed.add_cleaned_field("Nachricht:", f"```{message}```", inline=False)
    webhook_send("WEBHOOK_CONTACT", embeds=[embed])
    return send_success()


@api.route(f"/api/v69.420/add_school", methods=["POST"])
@login_required
def add_school() -> Response:
    data = request.form
    contact = data.get("contact")
    if contact is None:
        return send_error("Keine Kontaktmöglichkeit angegeben")
    school_num = data.get("school_num")
    if school_num is None:
        return send_error("Keine Schulnummer angegeben")
    display_name = data.get("display_name")
    if display_name is None:
        return send_error("Kein Schulname angegeben")
    username = data.get("username")
    if username is None:
        return send_error("Kein Nutzername angegeben")
    pw = data.get("pw")
    if pw is None:
        return send_error("Kein Passwort angegeben")
    if not school_num and not username and not pw:
        return send_error("Bitte gib alle Daten an")

    candidate = SchoolCandidate("", school_num, username, pw)
    embed = BetterEmbed(title="Neue Schulanfrage!", color="ffffff", inline=False)
    embed.add_embed_field("Nickname des users:", f"{current_user.get_field('nickname')}", inline=False)
    embed.add_embed_field("Kontakt:", contact, inline=False)
    embed.add_embed_field("Schulnummer:", school_num, inline=False)
    embed.add_embed_field("Schulname:", display_name, inline=False)
    embed.add_embed_field("Nutzername:", username, inline=False)
    embed.add_cleaned_field("Passwort:", f"||```{pw}```||", inline=False)
    embed.add_embed_field("Schule existiert:", str(candidate.school_exists), inline=False)
    embed.add_embed_field("Daten korrekt:", str(candidate.is_valid), inline=False)
    embed.add_embed_field("Benötigt Passwort:", str(candidate.needs_password), inline=False)
    if school_num in VALID_SCHOOLS:
        embed.add_embed_field("Bemerkung:", "Schule schon vorhanden", inline=False)
    webhook_send("WEBHOOK_ADD_SCHOOL", embeds=[embed])
    if not candidate.school_exists:
        return send_error("Schule existiert nicht")
    if not candidate.is_valid:
        return send_error("Nutzername oder Passwort falsch")

    if school_num in VALID_SCHOOLS:
        return send_error("Schule schon bekannt, Daten trotzdem übermittelt.")
    return send_success("Die Daten sind korrekt, wir werden nun innerhalb weniger Tage deine Schule hinzufügen.")


@api.route(f"/api/v69.420/webpush_subscription", methods=["POST", "DELETE"])
@login_required
def add_webpush_subscription() -> Response:
    if request.method == "DELETE" and request.data.decode("utf-8") == "__all__":
        current_user.update_field("webpush_subscriptions", [])
        return send_success("Alle Subscriptions entfernt.")

    try:
        subscription = json.loads(request.data.decode("utf-8"))
    except json.JSONDecodeError:
        return send_error("Subscription ist kein JSON")

    try:
        subscription = {
            "endpoint": subscription["endpoint"],
            "expirationTime": subscription["expirationTime"],
            "keys": {
                "p256dh": subscription["keys"]["p256dh"],
                "auth": subscription["keys"]["auth"]
            }
        }
    except KeyError:
        return send_error("Ungültige WebPush-Subscription.")

    current_subs: list = current_user.get_field("webpush_subscriptions", [])
    if request.method == "POST":
        if subscription not in current_subs:
            current_subs.append(subscription)
        else:
            send_success("Subscription schon vorhanden.")
    elif request.method == "DELETE":
        try:
            current_subs.remove(subscription)
        except ValueError:
            return send_success("Subscription nicht vorhanden.")
    else:
        assert False
    current_subs = list(current_subs)
    del current_subs[-(10 + 1)::-1]

    current_user.update_field(
        "webpush_subscriptions", current_subs
    )
    if request.method == "POST":
        return send_success("Subscription hinzugefügt.")
    elif request.method == "DELETE":
        return send_success("Subscription entfernt.")


@api.route(f"/api/v69.420/webpush_test", methods=["POST"])
@login_required
def webpush_test() -> Response:
    try:
        subscription = json.loads(request.data.decode("utf-8"))
    except json.JSONDecodeError:
        return send_error("Subscription ist kein JSON")

    try:
        subscription = {
            "endpoint": subscription["endpoint"],
            "expirationTime": subscription["expirationTime"],
            "keys": {
                "p256dh": subscription["keys"]["p256dh"],
                "auth": subscription["keys"]["auth"]
            }
        }
    except KeyError:
        return send_error("Ungültige WebPush-Subscription.")

    try:
        endpoints.webpush.send_message(
            subscription,
            {"type": "test", "data": "Hallo Welt!"}
        )
    except endpoints.webpush.pywebpush.WebPushException as e:
        logging.error(f"WebPushException: {e.response.text}", exc_info=e)
        return send_error("Fehler!")

    return send_success("Benachrichtigung gesendet.")


@api.route(f"/api/v69.420/get_webpush_public_key", methods=["GET"])
@login_required
def get_webpush_public_key() -> Response:
    return send_success(os.environ.get("VAPID_PUBLIC"))
