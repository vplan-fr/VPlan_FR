# coding=utf-8
import datetime


def group_forms(forms: list[str]) -> list[list[str]]:
    klassen = list(forms)

    groups = []
    while len(klassen) > 0:
        cur_klasse = klassen[0]
        if "/" in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split("/")[0] == cur_klasse.split("/")[0]]
        elif "-" in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split("-")[0] == cur_klasse.split("-")[0]]
        elif "." in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split(".")[0] == cur_klasse.split(".")[0]]
        elif cur_klasse.isdigit():
            cur_group = [elem for elem in klassen if elem.isdigit()]
        elif not cur_klasse[0].isdigit():
            identifier = "".join([char for char in cur_klasse if not char.isdigit()])
            cur_group = [elem for elem in klassen if elem.startswith(identifier)]
        elif cur_klasse[0].isdigit():
            identifier = "".join([char for char in cur_klasse if char.isdigit()])
            cur_group = [elem for elem in klassen if elem.startswith(identifier)]
        else:
            cur_group = [cur_klasse]
        for elem in cur_group:
            if elem in klassen:
                klassen.remove(elem)
        groups.append(cur_group)
    return groups


def find_closest_date(dates):
    now = datetime.datetime.now()
    today = now.date()
    future_dates = [d for d in dates if d > today]
    past_dates = [d for d in dates if d < today]

    if today in dates and now.time().hour < 17:
        return today
    elif future_dates:
        return min(future_dates)
    elif past_dates:
        return max(past_dates)
    else:
        return None