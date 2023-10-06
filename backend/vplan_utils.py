# coding=utf-8
from __future__ import annotations

import abc
import dataclasses
import datetime
import re
import typing
from collections import defaultdict

_parse_form_pattern = re.compile(
    r"(?<!\S)(?:"
    r"(?P<major>\d{1,2}(?!\d)|[A-Za-zÄÖÜäöüß]+(?![A-Za-zÄÖÜäöüß]))"
    r"(?P<sep>[/.] |[^A-Za-zÄÖÜäöüß0-9() \n]?)"
    r"(?P<minor>(?:\d{1,2}[A-Za-zÄÖÜäöüß]?|[A-Za-zÄÖÜäöüß]+?)(?:,(?:\d{1,2}[A-Za-zÄÖÜäöüß]?|[A-Za-zÄÖÜäöüß]+?))*)"
    r"|(?P<alpha>\d{1,2})"
    r")(?![^\s,:])"
)
_loose_parse_form_pattern = re.compile(
    r"(?<!\S)(?:"
    r"(?P<major>\d{1,2}(?!\d)|[A-Za-zÄÖÜäöüß]+(?![A-Za-zÄÖÜäöüß]))"
    r"(?P<sep>[/.]? |[^A-Za-zÄÖÜäöüß0-9() \n]?)"
    r"(?P<minor>(?:\d{1,2}[A-Za-zÄÖÜäöüß]?|[A-Za-zÄÖÜäöüß]+?)(?:,(?:\d{1,2}[A-Za-zÄÖÜäöüß]?|[A-Za-zÄÖÜäöüß]+?))*)"
    r"|(?P<alpha>\d{1,2})"
    r")(?![^\s,:()])"
)


class ParsedForm(abc.ABC):
    @classmethod
    def from_str(cls, form: str) -> ParsedForm:
        match = _parse_form_pattern.fullmatch(form)
        if match is None or match.group("alpha"):
            return AlphanumParsedForm(form)
        else:
            return MajorMinorParsedForm(*match.group("major", "sep", "minor"))

    @classmethod
    def from_form_match(cls, match: re.Match) -> ParsedForm:
        if match.group("alpha"):
            return AlphanumParsedForm(match.group("alpha"))
        else:
            return MajorMinorParsedForm(*match.group("major", "sep", "minor"))

    @abc.abstractmethod
    def to_tuple(self) -> tuple[str, ...]:
        ...

    @abc.abstractmethod
    def expand_forms(self) -> list[ParsedForm]:
        ...

    def to_str(self):
        return "".join(self.to_tuple())

    def __iter__(self):
        return iter(self.to_tuple())

    def __getitem__(self, item):
        return self.to_tuple()[item]


@dataclasses.dataclass(frozen=True)
class MajorMinorParsedForm(ParsedForm):
    major: str
    separator: str
    minor: str

    def to_tuple(self) -> tuple[str, str, str]:
        return self.major, self.separator, self.minor

    def expand_forms(self) -> list[ParsedForm]:
        return [MajorMinorParsedForm(self.major, self.separator, minor.strip()) for minor in self.minor.split(",")]


@dataclasses.dataclass(frozen=True)
class AlphanumParsedForm(ParsedForm):
    alpha: str | None

    def to_tuple(self) -> tuple[str]:
        return self.alpha,

    def expand_forms(self) -> list[ParsedForm]:
        return [self]


def form_sort_key(major: str | None):
    if major is None:
        return float("inf"), 1, ""
    try:
        return int(major), 0, ""
    except ValueError:
        return float("inf"), 0, major


def group_forms(forms: list[str]) -> dict[str | None, list[str]]:
    groups: dict[str | None, list[str]] = defaultdict(list)

    for form_str in forms:
        form = ParsedForm.from_str(form_str)
        if isinstance(form, MajorMinorParsedForm):
            group_name = form.major
        else:
            group_name = None

        groups[group_name].append(form_str)

    return {k: v for k, v in sorted(groups.items(), key=lambda x: form_sort_key(x[0]))}


def _form_minor_to_int(minor: str) -> tuple[int | None, int | None]:
    try:
        return int(minor), 0  # 0 = numeric
    except ValueError:
        pass

    if minor.isalpha() and len(minor) == 1:
        return ord(minor.lower()) - ord("a") + 1, 1  # 1 = alpha

    return None, None


def form_minor_to_int(minor: str) -> tuple[int | None, int | None]:
    minor_int, minor_type = _form_minor_to_int(minor)

    if minor_int is None:
        return None, None
    elif not 1 <= minor_int <= 13:
        return None, None
    else:
        return minor_int, minor_type


def _increasing_sequences(seq: typing.Iterable, key=lambda x: x) -> list[list]:
    out = []
    current_seq = []
    last = None

    for elem in seq:
        if last == elem:
            # fallback if something bad happens
            return [[elem] for elem in seq]

        if last is None or key(elem) == key(last) + 1:
            current_seq.append(elem)
        else:
            out.append(current_seq)
            current_seq = [elem]

        last = elem

    out.append(current_seq)

    return out


def _group_form_minors(first_part: str, minors: list[str]) -> list[str]:
    _parsed_minors: dict[str, tuple[int | None, int | None]] = {minor: form_minor_to_int(minor) for minor in minors}
    _valid_parsed_minors = {
        k: (minor_int, minor_type) for k, (minor_int, minor_type) in _parsed_minors.items() if minor_int is not None
    }
    invalid_minors = [k for k, (minor_int, minor_type) in _parsed_minors.items() if minor_int is None]
    parsed_minors_by_minor_type: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for minor, (minor_int, minor_type) in _valid_parsed_minors.items():
        parsed_minors_by_minor_type[minor_type].append((minor, minor_int))

    # sort by minor int
    parsed_minors_by_minor_type = {
        minor_type: sorted(parsed_minors, key=lambda x: x[1])
        for minor_type, parsed_minors in parsed_minors_by_minor_type.items()
    }

    # sort by minor type
    parsed_minors_by_minor_type = dict(sorted(parsed_minors_by_minor_type.items(), key=lambda x: x[0]))

    out = []

    for minor_type, parsed_minors in parsed_minors_by_minor_type.items():
        seqs = _increasing_sequences(parsed_minors, key=lambda x: x[1])

        for seq in seqs:
            if not seq:
                continue

            if len(seq) < 3:
                for minor_str, minor_int in seq:
                    out.append(minor_str)
            else:
                out.append(f"{seq[0][0]}-{seq[-1][0]}")

    out += invalid_minors

    return [f"{first_part}{','.join(out)}"]


def parsed_forms_to_str(forms: list[ParsedForm]) -> str:
    alphanum_forms = [form for form in forms if isinstance(form, AlphanumParsedForm)]
    other_forms = [form for form in forms if isinstance(form, MajorMinorParsedForm)]

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

    return "; ".join(out)


def forms_to_str(forms: typing.Iterable[str]) -> str:
    return parsed_forms_to_str([ParsedForm.from_str(form) for form in forms])


def periods_to_block_label(periods: typing.Iterable[int]) -> str:
    periods = list(set(periods))

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


def _parse_periods(period_str: str) -> list[int]:
    def period_str_to_int(string: str) -> int:
        return int(string.replace("Stunde", "").replace(".", ""))

    if not period_str:
        return []
    elif "-" not in period_str:
        return [period_str_to_int(period_str)]
    else:
        begin, end = period_str.split("-")
        return list(range(period_str_to_int(begin), period_str_to_int(end) + 1))


def parse_periods(period_str: str) -> set[int]:
    return set(sum([_parse_periods(p) for p in period_str.split(",")], []))


def parse_absent_element(element: str) -> tuple[str, set[int]]:
    """Parse a string like the following: "label (1-2,4)" into label and periods."""

    segments = element.rsplit("(", 1)

    label = segments[0].strip()

    if len(segments) == 1:
        periods = set()
    else:
        periods = parse_periods(segments[1][:-1])

    return label, periods


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
