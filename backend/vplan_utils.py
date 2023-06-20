# coding=utf-8
from __future__ import annotations

import datetime
import re
import typing
from collections import defaultdict

ParsedForm = typing.Union[typing.Tuple[str], typing.Tuple[str, str, str]]

_parse_form_pattern = re.compile(
    r"(?P<major>"
    r"(?P<_major_only_digits>11|12|13)"
    r"|\d+"
    r"|[A-Za-zÄÖÜäöüß]+(?![A-Za-zÄÖÜäöüß]))"

    r"(?P<sep>(?P<_contains_sep>[^A-Za-zÄÖÜäöüß0-9 \n])?)"

    r"(?(_contains_sep)(?P<_contains_whitespace> )?|)"

    r"(?P<minor>"
    r"\d+"
    r"|[A-Za-zÄÖÜäöüß]+?"
    r"|(?(_major_only_digits)(?(_contains_sep)yes(?!.)|(?(_contains_whitespace)yes(?!.)|))|no(?!.)))"
    
    r"|(?P<alpha>[A-ZÄÖÜ]+|\d+)"
)


def parse_form(form: str) -> ParsedForm:
    match = _parse_form_pattern.match(form)
    if match is None or match.group("alpha"):
        return form,
    else:
        return match.group("major"), match.group("sep"), match.group("minor")


def form_sort_key(major: str | None):
    if major is None:
        return float("inf"), 1, ""
    try:
        return int(major), 0, ""
    except ValueError:
        return float("inf"), 0, major


def group_forms(forms: list[str]) -> dict[str, list[str]]:
    groups: dict[str | None, list[str]] = defaultdict(list)

    for form in forms:
        group_name, *_ = parse_form(form)

        groups[group_name].append(form)

    return {k: v for k, v in sorted(groups.items(), key=lambda x: form_sort_key(x[0]))}


def _parse_form_minor(minor: str) -> int | None:
    try:
        return int(minor)
    except ValueError:
        pass

    if minor.isalpha():
        return ord(minor.lower()) - ord("a") + 1

    return None


def parse_form_minor(minor: str) -> int | None:
    minor_int = _parse_form_minor(minor)

    if minor_int is None:
        return None
    elif not 1 <= minor_int <= 8:
        return None
    else:
        return minor_int


def _increasing_sequences(seq: typing.Iterable, key=lambda x: x) -> list[list]:
    out = []
    current_seq = []
    last = None

    for elem in seq:
        if last is None or key(elem) == key(last) + 1:
            current_seq.append(elem)
        else:
            out.append(current_seq)
            current_seq = [elem]

        last = elem

    out.append(current_seq)

    return out


def _group_form_minors(first_part: str, minors: list[str]) -> list[str]:
    _parsed_minors = {minor: parse_form_minor(minor) for minor in minors}
    _non_invalid_parsed_minors = {k: v for k, v in _parsed_minors.items() if v is not None}
    invalid_minors = [k for k, v in _parsed_minors.items() if v is None]
    parsed_minors = {k: v for k, v in sorted(_non_invalid_parsed_minors.items(), key=lambda x: x[1])}

    seqs = _increasing_sequences(parsed_minors.keys(), key=lambda x: parsed_minors[x])

    out = []
    for seq in seqs:
        if not seq:
            continue
        elif len(seq) == 1:
            out.append(f"{first_part}{seq[0]}")
        else:
            out.append(f"{first_part}{seq[0]}-{seq[-1]}")

    for invalid_minor in invalid_minors:
        out.append(f"{first_part}{invalid_minor}")

    return out


def _forms_to_str(forms: list[ParsedForm]) -> str:
    alphanum_forms = [form for form in forms if len(form) == 1]
    other_forms = [form for form in forms if len(form) != 1]

    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)

    for form in other_forms:
        major, sep, minor = form
        grouped[major, sep].append(minor)

    # sort my major
    grouped = {k: v for k, v in sorted(grouped.items(), key=lambda x: form_sort_key(x[0][0]))}

    out = []
    for (major, sep), minors in grouped.items():
        out += _group_form_minors(major + sep, minors)

    for form in alphanum_forms:
        out.append(form[0])

    return ", ".join(out)


def forms_to_str(forms: typing.Iterable[str]) -> str:
    return _forms_to_str([parse_form(form) for form in forms])


def periods_to_block_label(periods: list[int]) -> str:
    periods.sort()

    rests = {
        0: "/Ⅱ",  # "²⁄₂",
        1: "/Ⅰ"  # "¹⁄₂",  # ½
    }
    if len(periods) == 1:
        return f"{(periods[0] - 1) // 2 + 1}{rests[periods[0] % 2]}"

    elif len(periods) == 2 and periods[0] % 2 == 1 and periods[1] - periods[0] == 1:
        return f"{periods[-1] // 2}"

    else:
        return ", ".join([periods_to_block_label([p]) for p in periods])


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
