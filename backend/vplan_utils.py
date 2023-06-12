# coding=utf-8
from __future__ import annotations

import datetime
import re
from collections import defaultdict


def group_forms(forms: list[str]) -> dict[str, list[str]]:
    groups: dict[str | None, list[str]] = defaultdict(list)

    pattern = re.compile(r"^((?P<alpha>([A-Za-zÄÖÜäöüß]+)|(\d+))|((?P<major>[\dA-Za-zÄÖÜäöüß]+?)[^A-Za-zÄÖÜäöüß0-9]?(?P"
                         r"<minor>(\d+)|([A-Za-zÄÖÜäöüß]+?))))$")
    for form in forms:
        match = pattern.match(form)
        if match is None or match.group("alpha"):
            groups[None].append(form)
        else:
            major = match.group("major")
            groups[major].append(form)

    def sort_key(form):
        if form is None:
            return float("inf"), 1, ""
        try:
            return int(form), 0, ""
        except ValueError:
            return float("inf"), 0, form

    return {k: v for k, v in sorted(groups.items(), key=lambda x: sort_key(x[0]))}


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
