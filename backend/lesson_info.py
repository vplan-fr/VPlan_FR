from __future__ import annotations

import dataclasses
import datetime
import re
import typing

from backend.vplan_utils import periods_to_block_label


# Nicht verfügbare Räume:	1302 (1-2,7-10), 1306 (1-2,4,6)


class _InfoParsers:
    _teacher = r"[A-ZÄÖÜ][a-zäöüß]+(?: [A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)+"
    # teacher a,teacher b
    _teachers = fr"{_teacher}(?:,{_teacher})*"
    _course = r"[A-Za-z0-9ÄÖÜäöüß-]{2,7}"  # maybe be more strict?
    _period = r"St\.(?P<periods>(?P<period_begin>\d{1,2})(?:-(?P<period_end>\d{1,2}))?)"
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
    independent = re.compile(rf'selbst\. \(.\)')

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

    @classmethod
    def _parse_periods(cls, period_str: str) -> list[int]:
        if "-" not in period_str:
            return [int(period_str)]
        else:
            begin, end = period_str.split("-")
            return list(range(int(begin), int(end) + 1))

    @classmethod
    def parse_periods(cls, period_str: str) -> list[int]:
        return sum([cls._parse_periods(p) for p in period_str.split(",")], [])


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


def de_weekday_to_str(weekday: int) -> str:
    return {
        0: "Mo",
        1: "Di",
        2: "Mi",
        3: "Do",
        4: "Fr",
        5: "Sa",
        6: "So"
    }[weekday]


@dataclasses.dataclass
class MovedFromPeriod(ToJsonMixin):
    periods: list[int]

    def to_blocked_str(self):
        return f"verlegt von Block {periods_to_block_label(self.periods)}"

    @staticmethod
    def is_groupable(other: MovedFromPeriod):
        return True


@dataclasses.dataclass
class InsteadOfCourse(ToJsonMixin):
    course: str
    teachers: list[str]


@dataclasses.dataclass
class InsteadOfPeriod(ToJsonMixin):
    date: datetime.date
    periods: list[int]

    def to_blocked_str(self):
        return (
            f"statt {de_weekday_to_str(self.date.weekday())} ({self.date.strftime('%d.%m.%Y')}) "
            f"Block {periods_to_block_label(self.periods)}"
        )

    def is_groupable(self, other: InsteadOfPeriod):
        return self.date == other.date


@dataclasses.dataclass
class CourseHeldAt(ToJsonMixin):
    course: str
    teachers: list[str]
    date: datetime.date
    periods: list[int]

    def to_blocked_str(self):
        return (
            f"{self.course} {', '.join(self.teachers)} gehalten am {de_weekday_to_str(self.date.weekday())} "
            f"({self.date.strftime('%d.%m.%Y')}) Block {periods_to_block_label(self.periods)}"
        )

    def is_groupable(self, other: CourseHeldAt):
        return (
                self.course == other.course
                and set(self.teachers) == set(other.teachers)
                and self.date == other.date
        )


@dataclasses.dataclass
class MovedTo(ToJsonMixin):
    course: str
    teachers: list[str]
    date: datetime.date | None
    periods: list[int]

    def to_blocked_str(self):
        if self.date is None:
            return f"{self.course} {', '.join(self.teachers)} verlegt nach Block {periods_to_block_label(self.periods)}"
        else:
            return (
                f"{self.course} {', '.join(self.teachers)} verlegt nach {de_weekday_to_str(self.date.weekday())} "
                f"({self.date.strftime('%d.%m.%Y')}) Block {periods_to_block_label(self.periods)}"
            )

    def is_groupable(self, other: MovedTo):
        return (
                self.course == other.course
                and set(self.teachers) == set(other.teachers)
                and self.date == other.date
        )


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
class DoAtLocation(ToJsonMixin):
    location: str


@dataclasses.dataclass
class IndividualRevision(ToJsonMixin):
    location: str | None


@dataclasses.dataclass
class Exam(ToJsonMixin):
    last_name: str


def _parse_info(info: str, plan_year: int) -> ToJsonMixin | None:
    if match := _InfoParsers.moved_from.search(info):
        return MovedFromPeriod([int(match.group("period_begin"))])
    elif match := _InfoParsers.substitution.search(info):
        return InsteadOfCourse(match.group("course"), match.group("teachers").split(","))
    elif match := _InfoParsers.instead_of.search(info):
        return InsteadOfPeriod(
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            _InfoParsers.parse_periods(match.group("periods"))
        )
    elif match := _InfoParsers.held_at.search(info):
        return CourseHeldAt(
            match.group("course"),
            match.group("teachers").split(","),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            _InfoParsers.parse_periods(match.group("periods"))
        )
    elif match := _InfoParsers.moved_to.search(info):
        return MovedTo(
            match.group("course"),
            match.group("teachers").split(","),
            None,
            _InfoParsers.parse_periods(match.group("periods"))
        )
    elif match := _InfoParsers.moved_to_date.search(info):
        return MovedTo(
            match.group("course"),
            match.group("teachers").split(","),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            _InfoParsers.parse_periods(match.group("periods"))
        )
    elif match := _InfoParsers.cancelled.search(info):
        return Cancelled(match.group("course"), match.group("teachers").split(","))
    elif match := _InfoParsers.exam.search(info):
        return Exam(match.group("last_name"))
    elif match := _InfoParsers.do_where.search(info):
        return DoAtLocation(match.group(1).strip())
    elif match := _InfoParsers.individual_revision.search(info):
        return IndividualRevision(match.groupdict(None)["location"])
    elif _InfoParsers.independent.search(info):
        return DoIndependent()
    elif _InfoParsers.tasks_in_lernsax.search(info):
        return TasksInLernsax()
    elif _InfoParsers.tasks_were_given.search(info):
        return TasksWereGiven()
    else:
        return None


ParsedLessonInfo = list[list[tuple[str, typing.Optional[ToJsonMixin]]]]


def sort_info(info: ParsedLessonInfo) -> ParsedLessonInfo:
    return sorted([
        sorted(part_info, key=lambda x: x[0])
        for part_info in info
    ], key=lambda part_info: [part_part_info[0] for part_part_info in part_info])


def parse_info(info: str, plan_year: int) -> ParsedLessonInfo:
    return [
        [(part_part_info.strip(), _parse_info(part_part_info, plan_year)) for part_part_info in part_info.split(", ")]
        for part_info in info.split(";")
    ]
