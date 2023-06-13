from __future__ import annotations

import dataclasses
import datetime
import re
import typing


# Nicht verfügbare Räume:	1302 (1-2,7-10), 1306 (1-2,4,6)


class MessageParseRegexes:
    _teacher = r"[A-ZÄÖÜ][a-zäöüß]+(?: [A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)+"
    # teacher a,teacher b
    _teachers = fr"{_teacher}(?:,{_teacher})*"
    _course = r"[A-Za-z0-9ÄÖÜäöüß-]{2,7}"  # maybe be more strict?
    _period = r"St\.(?P<period_begin>\d{1,2})(?:-(?P<period_end>\d{1,2}))?"
    _periods = fr""

    _weekday = r"(?:Mo|Di|Mi|Do|Fr|Sa|So)"
    _date = r"(?:\d{2}\.\d{2}\.)"

    _lesson_specifier = fr"{_weekday} \((?P<date>{_date})\) {_period}"

    # SUBSTITUTION (current lesson)
    # verlegt von St.7
    moved_from = re.compile(rf'verlegt von {_period}')

    substitution = re.compile(rf'für (?P<course>{_course}) (?P<teachers>{_teachers})')

    # What Happens With The Substituted Lesson
    # statt Mi (07.06.) St.1-2
    # statt Mo (05.06.) St.1-2
    # statt Mo (05.06.) St.5-6
    # statt Di (06.06.) St.7-8
    instead_of = re.compile(rf'statt {_weekday} \((?P<date>{_date})\) {_period}')

    # DE Frau Musterfrau gehalten am Mo (05.06.) St.1-2
    # GEO Frau Musterfrau gehalten am Mo (05.06.) St.5-6
    held_at = re.compile(rf'(?P<course>{_course}) (?P<teachers>{_teachers}) gehalten am {_lesson_specifier}')

    # MA Frau Musterfrau verlegt nach St.3
    # EN Frau Musterfrau verlegt nach St.5-6
    # GE Frau Musterfrau verlegt nach Do (08.06.) St.3-4
    moved_to = re.compile(rf'(?P<course>{_course}) (?P<teachers>{_teachers}) verlegt nach {_period}')
    moved_to_date = re.compile(rf'(?P<course>{_course}) (?P<teachers>{_teachers}) verlegt nach {_lesson_specifier}')

    # CANCELLED
    # SPO Herr Mustermann fällt aus
    # 11spo3 Frau Musterfrau fällt aus
    # GRW Frau Musterfrau fällt aus
    # 10Et12 Frau Musterfrau fällt aus
    cancelled = re.compile(
        rf'(?P<course>{_course}) (?P<teachers>{_teachers}) fällt aus')  # 1. group: subject, 2. group: teacher name

    # Not Quite Cancelled
    # selbst. (v), Aufgaben stehen im LernSax, bitte in der Bibo bearbeiten
    # selbst. (v), Aufgaben stehen im LernSax, bitte zu Hause bearbeiten
    # selbst. (v), Aufgaben stehen im LernSax
    # selbst. (v), Aufgaben wurden erteilt, bitte zu Hause erledigen
    independent = re.compile(rf'selbst\. \(v\)')

    tasks_in_lernsax = re.compile(rf'Aufgaben stehen im LernSax')
    tasks_were_given = re.compile(rf'Aufgaben wurden erteilt')

    do_where = re.compile(rf'bitte(( \w+)+) bearbeiten')  # 1. group: where

    # gesamte Klasse 6/2

    # individuelle Nachbearbeitung des aktuellen Stoffes in der Bibo bzw. 10/1 zu Hause
    individual_revision = re.compile(rf'individuelle Nachbearbeitung des aktuellen Stoffes (?P<location>in der Bibo)?')

    # Exams
    # Prüfung Nachname
    exam = re.compile(rf'Prüfung (?P<last_name>[A-ZÄÖÜ][a-zäöüß]+)')

    # Aufsicht Vorbereitungsraum mündliche Prüfung


class ToJsonMixin:
    def to_json(self: dataclasses.dataclass) -> dict[str, typing.Any]:
        def convert(obj: typing.Any) -> typing.Any:
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            else:
                return obj

        return {
            "type": self.__class__.__name__,
            **{k: convert(v) for k, v in dataclasses.asdict(self).items()}
        }


@dataclasses.dataclass
class MovedFromPeriod(ToJsonMixin):
    period: int


@dataclasses.dataclass
class InsteadOfCourse(ToJsonMixin):
    course: str
    teachers: list[str]


@dataclasses.dataclass
class InsteadOfPeriod(ToJsonMixin):
    date: datetime.date
    period: int


@dataclasses.dataclass
class CourseHeldAt(ToJsonMixin):
    course: str
    teachers: list[str]
    date: datetime.date
    period_begin: int
    period_end: int


@dataclasses.dataclass
class MovedTo(ToJsonMixin):
    course: str
    teachers: list[str]
    date: datetime.date | None
    period_begin: int
    period_end: int


@dataclasses.dataclass
class Cancelled(ToJsonMixin):
    course: str
    teachers: list[str]


@dataclasses.dataclass
class DoIndependent(ToJsonMixin):
    pass


@dataclasses.dataclass
class TasksInLernsax(ToJsonMixin):
    pass


@dataclasses.dataclass
class TasksWereGiven(ToJsonMixin):
    pass


@dataclasses.dataclass
class DoWhere(ToJsonMixin):
    where: str


@dataclasses.dataclass
class IndividualRevision(ToJsonMixin):
    where: str


@dataclasses.dataclass
class Exam(ToJsonMixin):
    last_name: str

def _parse_info(info: str, plan_year: int) -> ToJsonMixin | None:
    if match := MessageParseRegexes.moved_from.search(info):
        return MovedFromPeriod(int(match.group("period_begin")))
    elif match := MessageParseRegexes.substitution.search(info):
        return InsteadOfCourse(match.group("course"), match.group("teachers").split(","))
    elif match := MessageParseRegexes.instead_of.search(info):
        return InsteadOfPeriod(
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            int(match.group("period_begin"))
        )
    elif match := MessageParseRegexes.held_at.search(info):
        return CourseHeldAt(
            match.group("course"),
            match.group("teachers").split(","),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            int(match.group("period_begin")),
            int(match.group("period_end")) if match.group("period_end") else int(match.group("period_begin"))
        )
    elif match := MessageParseRegexes.moved_to.search(info):
        return MovedTo(
            match.group("course"),
            match.group("teachers").split(","),
            None,
            int(match.group("period_begin")),
            int(match.group("period_end")) if match.group("period_end") else int(match.group("period_begin"))
        )
    elif match := MessageParseRegexes.moved_to_date.search(info):
        return MovedTo(
            match.group("course"),
            match.group("teachers").split(","),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            int(match.group("period_begin")),
            int(match.group("period_end")) if match.group("period_end") else int(match.group("period_begin"))
        )
    elif match := MessageParseRegexes.cancelled.search(info):
        return Cancelled(match.group("course"), match.group("teachers").split(","))
    elif match := MessageParseRegexes.exam.search(info):
        return Exam(match.group("last_name"))
    elif match := MessageParseRegexes.do_where.search(info):
        return DoWhere(match.group(1).strip())
    elif match := MessageParseRegexes.individual_revision.search(info):
        return IndividualRevision(match.groupdict(None)["location"])
    elif MessageParseRegexes.independent.search(info):
        return DoIndependent()
    elif MessageParseRegexes.tasks_in_lernsax.search(info):
        return TasksInLernsax()
    elif MessageParseRegexes.tasks_were_given.search(info):
        return TasksWereGiven()
    else:
        return None


def parse_info(info: str, plan_year: int) -> list[list[tuple[str, ToJsonMixin | None]]]:
    return [
        [(part_part_info.strip(), _parse_info(part_part_info, plan_year)) for part_part_info in part_info.split(", ")]
        for part_info in info.split(";")
    ]
