from __future__ import annotations

import abc
import dataclasses
import datetime
import logging
import re
import typing

from .vplan_utils import periods_to_block_label, parse_periods
from . import models


# Nicht verfügbare Räume:	1302 (1-2,7-10), 1306 (1-2,4,6)


class _InfoParsers:
    _teacher_name = r"[A-ZÄÖÜ][a-zäöüß]+(?: [A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)+"
    _teacher_abbreviation = r"[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß]*"
    _teacher = fr"(?:{_teacher_name})|(?:{_teacher_abbreviation})"

    # teacher a,teacher b
    _teachers = fr"{_teacher}(?:, ?{_teacher})*"
    _course = r"([A-Za-z0-9ÄÖÜäöüß\/-]{2,8})"  # maybe be more strict?
    _period = r"St\.(?P<periods>(?P<period_begin>\d{1,2})(?:-(?P<period_end>\d{1,2}))?)"
    _periods = fr""
    _form = (
        r"(?:(?P<major>\d+|[A-Za-zÄÖÜäöüß]+)(?P<sep>[^A-Za-zÄÖÜäöüß0-9]?) ?(?P<minor>\d+|[A-Za-zÄÖÜäöüß]+?)|"
        r"(?P<alpha>[A-Za-zÄÖÜäöüß]+|\d+))"
    )

    _weekday = r"(?:Mo|Di|Mi|Do|Fr|Sa|So)"
    _date = r"(?:\d{2}\.\d{2}\.)"

    _lesson_specifier = fr"{_weekday} \((?P<date>{_date})\) {_period}"

    # SUBSTITUTION (current lesson)
    # verlegt von St.7
    moved_from = re.compile(rf'verlegt von {_period}')

    # course is always a subject
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
    cancelled = re.compile(rf'(?P<course>{_course}) (?P<teachers>{_teachers}) fällt aus')

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
    whole_form = re.compile(rf'gesamte Klasse (?P<form>{_form})')

    # individuelle Nachbearbeitung des aktuellen Stoffes in der Bibo bzw. 10/1 zu Hause
    individual_revision = re.compile(rf'individuelle Nachbearbeitung des aktuellen Stoffes (?P<location>in der Bibo)?')

    # Exams
    # Prüfung Nachname
    exam = re.compile(rf'Prüfung (?P<last_name>[A-ZÄÖÜ][a-zäöüß]+)')

    # Aufsicht Vorbereitungsraum mündliche Prüfung

    """
    eigentliche Stunde findet nicht statt, weil sie auf andere Stunde verlegt wurde
    "verlegt in die Vergangenheit"          =: "gehalten am"
    "verlegt in die Zukunft"                =: "verlegt nach"
    
    eigentliche Stunde findet nicht statt, weil andere Stunde auf diese verlegt wurde 
    "verlegt aus der Zukunft/Vergangenheit" =: "statt"
    "verlegt aus der Zukunft/Vergangenheit" =: "verlegt von" (gleicher Tag)

"""


class SerializeMixin:
    def serialize(self: dataclasses.dataclass) -> dict[str, typing.Any]:
        def convert(obj: typing.Any) -> typing.Any:
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            else:
                return obj

        return {
            "type": getattr(self, "__serialize_type__", self.__class__.__name__),
            **{k: convert(v) for k, v in dataclasses.asdict(self).items()}
        }


def de_weekday_to_str(weekday: int) -> str:
    return [
        "Mo",
        "Di",
        "Mi",
        "Do",
        "Fr",
        "Sa",
        "So"
    ][weekday]


class ParsedLessonInfoMessage(abc.ABC):
    before: str
    after: str
    original_messages: list[str]

    @abc.abstractmethod
    def serialize(self) -> dict[str, typing.Any]:
        ...

    def to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        return [
            *([LessonInfoTextSegment(self.before)] if self.before else []),
            *self._to_text_segments(lesson_date, lesson),
            *([LessonInfoTextSegment(self.after)] if self.after else [])
        ]

    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        return [
            LessonInfoTextSegment("\n".join(self.original_messages))
        ]


@dataclasses.dataclass
class MovedFrom(SerializeMixin, ParsedLessonInfoMessage):
    periods: list[int]
    date: datetime.date | None

    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        # TODO: Fallback when len(periods) == 1
        if self.date is None:
            return [
                LessonInfoTextSegment("verlegt von "),
                LessonInfoTextSegment(
                    f"Block {periods_to_block_label(self.periods)}",
                    link=LessonInfoTextSegmentLink(
                        type="forms",
                        value=sorted(lesson.scheduled_forms),
                        date=lesson_date,
                        periods=self.periods
                    )
                )
            ]
        else:
            return [
                LessonInfoTextSegment("statt "),
                LessonInfoTextSegment(
                    f"{de_weekday_to_str(self.date.weekday())} ({self.date.strftime('%d.%m.%Y')}) "
                    f"{periods_to_block_label(self.periods)}. Block",
                    link=LessonInfoTextSegmentLink(
                        type="forms",
                        value=sorted(lesson.scheduled_forms),
                        date=self.date,
                        periods=self.periods
                    )
                )
            ]

    def is_groupable(self, other: MovedFrom):
        return self.date == other.date


class _HasTeachersAndCourse(ParsedLessonInfoMessage, abc.ABC):
    _teachers: list[str]
    course: str


@dataclasses.dataclass
class MovedTo(SerializeMixin, _HasTeachersAndCourse):
    course: str
    _teachers: list[str]
    date: datetime.date | None
    periods: list[int]
    teachers: list[str] = dataclasses.field(init=False, default=None)

    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        if self.date is None:
            return [
                LessonInfoTextSegment(f"{self.course} "),
                LessonInfoTextSegment(
                    f"{', '.join(self._teachers)}",
                    link=LessonInfoTextSegmentLink(
                        type="teachers",
                        value=self.teachers,
                        date=lesson_date,
                        periods=self.periods
                    )
                ),
                LessonInfoTextSegment(" verlegt nach "),
                LessonInfoTextSegment(
                    f"Block {periods_to_block_label(self.periods)}",
                    link=LessonInfoTextSegmentLink(
                        type="forms",
                        value=sorted(lesson.scheduled_forms),
                        date=lesson_date,
                        periods=self.periods
                    )
                )
            ]
        elif self.date < lesson_date:
            return [
                LessonInfoTextSegment(f"{self.course} "),
                LessonInfoTextSegment(
                    f"{', '.join(self._teachers)}",
                    link=LessonInfoTextSegmentLink(
                        type="teachers",
                        value=self.teachers,
                        date=self.date,
                        periods=self.periods
                    )
                ),
                LessonInfoTextSegment(" gehalten am "),
                LessonInfoTextSegment(
                    f"{de_weekday_to_str(self.date.weekday())} ({self.date.strftime('%d.%m.%Y')}) "
                    f"{periods_to_block_label(self.periods)}. Block",
                    link=LessonInfoTextSegmentLink(
                        type="forms",
                        value=sorted(lesson.scheduled_forms),
                        date=self.date,
                        periods=self.periods
                    )
                )
            ]
        else:
            return [
                LessonInfoTextSegment(f"{self.course} "),
                LessonInfoTextSegment(
                    f"{', '.join(self._teachers)}",
                    link=LessonInfoTextSegmentLink(
                        type="teachers",
                        value=self.teachers,
                        date=self.date,
                        periods=self.periods
                    )
                ),
                LessonInfoTextSegment(" verlegt nach "),
                LessonInfoTextSegment(
                    f"{de_weekday_to_str(self.date.weekday())} ({self.date.strftime('%d.%m.%Y')}) "
                    f"{periods_to_block_label(self.periods)}. Block",
                    link=LessonInfoTextSegmentLink(
                        type="forms",
                        value=sorted(lesson.scheduled_forms),
                        date=self.date,
                        periods=self.periods
                    )
                )
            ]

    def is_groupable(self, other: MovedTo):
        return (
                self.course == other.course
                and set(self._teachers) == set(other._teachers)
                and self.date == other.date
        )


@dataclasses.dataclass
class InsteadOfCourse(SerializeMixin, _HasTeachersAndCourse):
    course: str
    _teachers: list[str]
    teachers: list[str] = dataclasses.field(init=False, default=None)

    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        return [
            LessonInfoTextSegment(f"für {self.course} "),
            LessonInfoTextSegment(
                f"{', '.join(self._teachers)}",
                link=LessonInfoTextSegmentLink(
                    type="teachers",
                    value=self.teachers,
                    date=lesson_date,
                    periods=sorted(lesson.periods)
                )
            )
        ]


@dataclasses.dataclass
class Cancelled(SerializeMixin, _HasTeachersAndCourse):
    course: str
    _teachers: list[str]
    teachers: list[str] = dataclasses.field(init=False, default=None)

    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        return [
            LessonInfoTextSegment(f"{self.course} "),
            LessonInfoTextSegment(
                f"{', '.join(self._teachers)}",
                link=LessonInfoTextSegmentLink(
                    type="teachers",
                    value=self.teachers,
                    date=lesson_date,
                    periods=sorted(lesson.periods)
                )
            ),
            LessonInfoTextSegment(" fällt aus")
        ]


@dataclasses.dataclass
class DoIndependently(SerializeMixin, ParsedLessonInfoMessage):
    pass


@dataclasses.dataclass
class TasksInLernsax(SerializeMixin, ParsedLessonInfoMessage):
    pass


@dataclasses.dataclass
class TasksWereGiven(SerializeMixin, ParsedLessonInfoMessage):
    pass


@dataclasses.dataclass
class DoAtLocation(SerializeMixin, ParsedLessonInfoMessage):
    location: str


@dataclasses.dataclass
class IndividualRevision(SerializeMixin, ParsedLessonInfoMessage):
    location: str | None


@dataclasses.dataclass
class Exam(SerializeMixin, ParsedLessonInfoMessage):
    last_name: str


@dataclasses.dataclass
class WholeForm(SerializeMixin, ParsedLessonInfoMessage):
    form: str

    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        return [
            LessonInfoTextSegment(f"gesamte "),
            LessonInfoTextSegment(
                f"Klasse {self.form}",
                link=LessonInfoTextSegmentLink(
                    type="forms",
                    value=[self.form],
                    date=lesson_date,
                    periods=sorted(lesson.periods)
                )
            )
        ]


@dataclasses.dataclass
class FailedToParse(SerializeMixin, ParsedLessonInfoMessage):
    def _to_text_segments(self, lesson_date: datetime.date, lesson: models.Lesson) -> list[LessonInfoTextSegment]:
        return [
            LessonInfoTextSegment(", ".join(self.original_messages))
        ]


def create_literal_parsed_info(msg: str) -> ParsedLessonInfo:
    obj = FailedToParse()
    obj.original_messages = [msg]
    obj.before = ""
    obj.after = ""

    return ParsedLessonInfo(
        paragraphs=[
            LessonInfoParagraph(
                messages=[
                    LessonInfoMessage(
                        parsed=obj,
                        index=0
                    )
                ],
                index=0
            )
        ]
    )


def resolve_teacher_abbreviations(surnames: list[str], abbreviation_by_surname: dict[str, str]) -> list[str]:
    return [abbreviation_by_surname.get(surname, surname) for surname in surnames]


def __parse_message(info: str, plan_year: int) -> tuple[ParsedLessonInfoMessage, re.Match | None]:
    if match := _InfoParsers.substitution.search(info):
        return InsteadOfCourse(
            match.group("course"),
            teachers := match.group("teachers").split(","),
            # resolve_teacher_abbreviations(teachers, teacher_abbreviation_by_surname)
        ), match
    elif match := _InfoParsers.moved_from.search(info):
        return MovedFrom([int(match.group("period_begin"))], None), match
    elif match := _InfoParsers.instead_of.search(info):
        return MovedFrom(
            parse_periods(match.group("periods")),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date()
        ), match
    elif match := _InfoParsers.held_at.search(info):
        return MovedTo(
            match.group("course"),
            teachers := match.group("teachers").split(","),
            # resolve_teacher_abbreviations(teachers, teacher_abbreviation_by_surname),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            parse_periods(match.group("periods"))
        ), match
    elif match := _InfoParsers.moved_to.search(info):
        return MovedTo(
            match.group("course"),
            teachers := match.group("teachers").split(","),
            # resolve_teacher_abbreviations(teachers, teacher_abbreviation_by_surname),
            None,
            parse_periods(match.group("periods"))
        ), match
    elif match := _InfoParsers.moved_to_date.search(info):
        return MovedTo(
            match.group("course"),
            teachers := match.group("teachers").split(","),
            # resolve_teacher_abbreviations(teachers, teacher_abbreviation_by_surname),
            datetime.datetime.strptime(f'{match.group("date")}{plan_year}', "%d.%m.%Y").date(),
            parse_periods(match.group("periods"))
        ), match
    elif match := _InfoParsers.cancelled.search(info):
        return Cancelled(
            match.group("course"),
            teachers := match.group("teachers").split(","),
            # resolve_teacher_abbreviations(teachers, teacher_abbreviation_by_surname)
        ), match
    elif match := _InfoParsers.exam.search(info):
        return Exam(match.group("last_name")), match
    elif match := _InfoParsers.do_where.search(info):
        return DoAtLocation(match.group(1).strip()), match
    elif match := _InfoParsers.individual_revision.search(info):
        return IndividualRevision(match.groupdict(None)["location"]), match
    elif match := _InfoParsers.whole_form.search(info):
        return WholeForm(match.group("form").replace(" ", "")), match
    elif match := _InfoParsers.independent.search(info):
        return DoIndependently(), match
    elif match := _InfoParsers.tasks_in_lernsax.search(info):
        return TasksInLernsax(), match
    elif match := _InfoParsers.tasks_were_given.search(info):
        return TasksWereGiven(), match
    else:
        return FailedToParse(), None


def _parse_message(info: str, plan_year: int) -> ParsedLessonInfoMessage:
    info = info.strip()
    info = re.sub(r"(?<=\w)\/\s", "/", info)  # remove spaces after slashes like in G/ R/ W
    parsed_info, match = __parse_message(info, plan_year)
    parsed_info.original_messages = [info]

    if match:
        parsed_info.before = info[:match.start()]
        parsed_info.after = info[match.end():]
    else:
        parsed_info.before = ""
        parsed_info.after = ""

    return parsed_info


@dataclasses.dataclass
class LessonInfoTextSegmentLink(SerializeMixin):
    type: typing.Literal["forms", "teachers", "rooms"]
    value: list[str]
    date: datetime.date | None
    periods: list[int] | None

    @property
    def __serialize_type__(self):
        return self.type


@dataclasses.dataclass
class LessonInfoTextSegment:
    text: str
    link: LessonInfoTextSegmentLink | None = None

    def serialize(self) -> dict:
        return {
            "text": self.text,
            "link": self.link.serialize() if self.link is not None else None
        }


@dataclasses.dataclass
class LessonInfoMessage:
    parsed: ParsedLessonInfoMessage
    index: int

    @classmethod
    def from_str(cls, message: str, plan_year: int, index: int) -> LessonInfoMessage:
        parsed = _parse_message(message, plan_year)

        return cls(
            parsed=parsed,
            index=index
        )

    def serialize(self, lesson_date: datetime.date, lesson: models.Lesson) -> dict:
        return {
            "parsed": (
                self.parsed.serialize()
                if not isinstance(self.parsed, FailedToParse) else None
            ),
            "text_segments": [segment.serialize() for segment in self.parsed.to_text_segments(lesson_date, lesson)]
        }


@dataclasses.dataclass
class LessonInfoParagraph:
    messages: list[LessonInfoMessage]
    index: int

    @classmethod
    def from_str(cls, paragraph: str, plan_year: int, index: int) -> LessonInfoParagraph:
        messages = [
            LessonInfoMessage.from_str(message.strip(), plan_year, i)
            for i, message in enumerate(paragraph.split(","))
        ]
        new_messages = []
        for message in messages:
            can_merge = (
                    new_messages
                    and isinstance(new_messages[-1].parsed, FailedToParse)
                    and isinstance(message.parsed, FailedToParse)
            )
            if can_merge:
                new_messages[-1].parsed.original_messages += message.parsed.original_messages
            else:
                new_messages.append(message)

        return cls(new_messages, index=index)

    def serialize(self, lesson_date: datetime.date, lesson: models.Lesson) -> list:
        return [info.serialize(lesson_date, lesson) for info in self.messages]

    def sorted(self, key: typing.Callable[[LessonInfoMessage], typing.Any]) -> LessonInfoParagraph:
        return LessonInfoParagraph(sorted(self.messages, key=key), self.index)

    def sort(self, key: typing.Callable[[LessonInfoMessage], typing.Any]):
        self.messages.sort(key=key)


@dataclasses.dataclass
class ParsedLessonInfo:
    paragraphs: list[LessonInfoParagraph]

    @classmethod
    def from_str(cls, info: str, plan_year: int) -> ParsedLessonInfo:
        return cls([
            LessonInfoParagraph.from_str(paragraph.strip(), plan_year, i)
            for i, paragraph in enumerate(info.split(";"))
        ])

    def serialize(self, lesson_date: datetime.date, lesson: models.Lesson) -> list:
        return [paragraph.serialize(lesson_date, lesson) for paragraph in self.paragraphs]

    def sorted(self, key: typing.Callable[[LessonInfoParagraph], typing.Any]) -> ParsedLessonInfo:
        return ParsedLessonInfo(sorted(self.paragraphs, key=key))

    def sort(self, key: typing.Callable[[LessonInfoParagraph], typing.Any]):
        self.paragraphs.sort(key=key)

    def sort_original(self):
        self.sort(key=lambda p: p.index)

        for paragraph in self.paragraphs:
            paragraph.sort(key=lambda i: i.index)

    def sorted_canonical(self) -> ParsedLessonInfo:
        paragraphs = [p.sorted(key=lambda i: i.parsed.original_messages) for p in self.paragraphs]

        return ParsedLessonInfo(
            sorted(paragraphs, key=lambda p: [i.parsed.original_messages for i in p.messages])
        )

    def resolve_teachers(self, teacher_abbreviation_by_surname: dict[str, str]):
        for paragraph in self.paragraphs:
            for message in paragraph.messages:
                if hasattr(message.parsed, "_teachers"):
                    message.parsed.teachers = resolve_teacher_abbreviations(
                        message.parsed._teachers,
                        teacher_abbreviation_by_surname
                    )

    def lesson_group_sort_key(self) -> list[list[list[str]]]:
        return [
            [message.parsed.original_messages for message in paragraph.messages]
            for paragraph in self.sorted_canonical().paragraphs
        ]


def extract_teachers(lesson: models.Lesson, classes: dict[str, models.Class], *,
                     logger: logging.Logger) -> dict[str, models.Teacher]:
    out: dict[str, models.Teacher] = {}
    for paragraph in lesson.parsed_info.paragraphs:
        for message in paragraph.messages:
            if isinstance(message.parsed, _HasTeachersAndCourse):
                surname = message.parsed._teachers[0]
                course = message.parsed.course

                if len(surname.split()) == 1:
                    logger.debug(f"Skipping teacher \"surname\" {surname!r}.")
                    continue

                _class: dict[str, models.Class] = {
                    class_nr: class_ for class_nr, class_ in classes.items()
                    if course in (class_.subject, class_.group) and lesson.scheduled_forms.issubset(class_.forms)
                }

                _name = surname.split()[1]
                if len({c.teacher for c in _class.values()}) > 1 and lesson.class_number:
                    new_classes = {c_id: c for c_id, c in _class.items() if c_id == lesson.class_number}
                    if new_classes:
                        _class = new_classes

                if len({c.teacher for c in _class.values()}) > 1:
                    _class = {c_id: c for c_id, c in _class.items() if c.teacher and _name.startswith(c.teacher[0])}

                if len({c.teacher for c in _class.values()}) != 1:
                    logger.debug(
                        f"Could not find class {course!r} in form {lesson.scheduled_forms!r}. "
                        f"Message: {message.parsed.original_messages!r}"
                    )
                    continue

                abbreviation = list(_class.values())[0].teacher
                teacher = models.Teacher(abbreviation, None, surname, None, [])

                out[teacher.abbreviation] = teacher

    return out
