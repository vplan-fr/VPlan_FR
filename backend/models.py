# coding=utf-8
from __future__ import annotations

import copy
import dataclasses
import datetime
from collections import defaultdict

import typing
from stundenplan24_py import indiware_mobil
import stundenplan24_py

from .lesson_info import ParsedLessonInfo, MovedFrom, MovedTo, LessonInfoParagraph, LessonInfoMessage
from . import vplan_utils


@dataclasses.dataclass
class Lesson:
    forms: set[str]
    current_subject: str | None
    current_teacher: str | None
    class_subject: str | None
    class_group: str | None
    class_teacher: str | None
    class_number: str | None
    rooms: set[str]
    periods: set[int]
    info: str
    parsed_info: ParsedLessonInfo

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool

    begin: datetime.time
    end: datetime.time

    is_internal: bool = False

    def to_dict(self, lesson_date: datetime.date) -> dict:
        return {
            "forms": sorted(self.forms),
            "forms_str": vplan_utils.forms_to_str(self.forms),
            "periods": list(self.periods),
            "rooms": list(self.rooms),
            "current_subject": self.current_subject,
            "current_teacher": self.current_teacher,
            "class_subject": self.class_subject,
            "class_group": self.class_group,
            "class_teacher": self.class_teacher,
            # "class_number": self.class_number,
            "info": self.info,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "begin": self.begin.strftime("%H:%M") if self.begin else None,
            "end": self.end.strftime("%H:%M") if self.end else None,
            "parsed_info": self.parsed_info.serialize(lesson_date, self)
        }


@dataclasses.dataclass
class Lessons:
    lessons: list[Lesson]
    date: datetime.date

    def group_by(self, *attributes: str, include_none: bool = False) -> dict[str, Lessons]:
        grouped_i = defaultdict(set)

        for lesson_i, lesson in enumerate(self.lessons):
            for attribute in attributes:
                value = getattr(lesson, attribute)

                if not include_none and value is None:
                    continue

                if not isinstance(value, (list, set)):
                    value = [value]

                for element in value:
                    grouped_i[element].add(lesson_i)

        grouped = {attribute: [self.lessons[i] for i in indices] for attribute, indices in grouped_i.items()}

        return {attribute: Lessons(sorted(lessons, key=lambda x: list(x.periods)[0]), self.date)
                for attribute, lessons in grouped.items()}

    def serialize(self) -> list[dict]:
        return [lesson.to_dict(self.date) for lesson in self.lessons]

    @staticmethod
    def _group_lesson_info(
            parsed_info1: ParsedLessonInfo,
            parsed_info2: ParsedLessonInfo
    ) -> ParsedLessonInfo | None:
        info1: ParsedLessonInfo = parsed_info1.sorted_canonical()
        info2: ParsedLessonInfo = parsed_info2.sorted_canonical()

        new_info = []

        for paragraph1, paragraph2 in zip(info1.paragraphs, info2.paragraphs):
            new_paragraph = []
            for message1, message2 in zip(paragraph1.messages, paragraph2.messages):
                message1: LessonInfoMessage
                message2: LessonInfoMessage

                if type(message1.parsed) != type(message2.parsed):
                    # both infos are definitely not the same
                    return None

                # info string not the same but periods may be groupable
                # noinspection PyTypeChecker
                parsed1, parsed2 = message1.parsed, message2.parsed
                if isinstance(parsed1, (MovedFrom, MovedTo)):
                    parsed2: MovedFrom | MovedTo

                    if parsed1.is_groupable(parsed2):
                        new_message = copy.deepcopy(message1)
                        # noinspection PyTypeHints
                        new_message.parsed: MovedFrom | MovedTo
                        new_message.parsed.periods += parsed2.periods
                        new_message.parsed.original_messages += parsed2.original_messages
                        new_paragraph.append(new_message)
                    else:
                        return None

                # not groupable, so, to group, info string must be the same
                elif message1.parsed.original_messages == message2.parsed.original_messages:
                    new_paragraph.append(message1)

                else:
                    return None

            new_info.append(LessonInfoParagraph(new_paragraph, paragraph1.index))

        return ParsedLessonInfo(new_info).sorted_original()

    def blocks_grouped(self) -> Lessons:
        assert all(len(x.periods) <= 1 for x in self.lessons), \
            "Lessons must be ungrouped. (Must only have one period.)"

        sorted_lessons = sorted(
            self.lessons,
            key=lambda x: (x.current_subject if x.current_subject is not None else "",
                           x.class_group if x.class_group is not None else "",
                           x.forms,
                           x.periods)
        )

        grouped: list[Lesson] = []

        previous_lesson: Lesson | None = None
        for lesson in sorted_lessons:
            should_get_grouped = (
                    previous_lesson is not None and
                    lesson.rooms == previous_lesson.rooms and
                    lesson.current_subject == previous_lesson.current_subject and
                    lesson.current_teacher == previous_lesson.current_teacher and
                    lesson.class_number == previous_lesson.class_number
            )

            if previous_lesson is not None:
                grouped_additional_info = self._group_lesson_info(lesson.parsed_info, previous_lesson.parsed_info)

                should_get_grouped &= grouped_additional_info is not None
            else:
                grouped_additional_info = None

            if previous_lesson is not None:
                if (
                        (not lesson.forms and not grouped[-1].forms)
                        or (lesson.forms and list(lesson.forms)[0] in grouped[-1].forms)
                ):
                    should_get_grouped &= list(lesson.periods)[0] % 2 == 0
                else:
                    should_get_grouped &= list(lesson.periods)[-1] in grouped[-1].periods

            if should_get_grouped:
                grouped[-1].periods |= lesson.periods
                grouped[-1].forms |= lesson.forms
                grouped[-1].info = "\n".join(filter(lambda x: x, [grouped[-1].info, lesson.info]))
                grouped[-1].parsed_info = grouped_additional_info
                grouped[-1].end = lesson.end
            else:
                grouped.append(copy.deepcopy(lesson))

            previous_lesson = lesson

        return Lessons(sorted(grouped, key=lambda x: x.periods), self.date)

    def filter(self, function: typing.Callable[[Lesson], bool]) -> Lessons:
        return Lessons(list(filter(function, self.lessons)), self.date)

    def __iter__(self):
        return iter(self.lessons)


class Exam(stundenplan24_py.Exam):
    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "course": self.course,
            "course_teacher": self.course_teacher,
            "period": self.period,
            "begin": self.begin.isoformat(),
            "duration": self.duration,
            "info": self.info
        }


@dataclasses.dataclass
class Plan:
    lessons: Lessons
    additional_info: list[str]
    exams: dict[str, list[Exam]]

    form_plan: indiware_mobil.FormPlan

    @classmethod
    def from_form_plan(cls, form_plan: indiware_mobil.FormPlan,
                       teacher_abbreviation_by_surname: dict[str, str]) -> Plan:
        lessons: list[Lesson] = []
        exams: dict[str, list[Exam]] = defaultdict(list)
        for form in form_plan.forms:
            for lesson in form.lessons:
                parsed_info = ParsedLessonInfo.from_str(
                    lesson.information, form_plan.timestamp.year,
                    teacher_abbreviation_by_surname
                ) if lesson.information is not None else ParsedLessonInfo([])

                lessons.append(Lesson(
                    forms={form.short_name},
                    class_subject=(
                        form.classes[lesson.class_number].subject if lesson.class_number in form.classes else None
                    ),
                    class_group=(
                        form.classes[lesson.class_number].group if lesson.class_number in form.classes else None
                    ),
                    class_teacher=(
                        form.classes[lesson.class_number].teacher if lesson.class_number in form.classes else None
                    ),
                    class_number=lesson.class_number,
                    current_subject=lesson.subject(),
                    current_teacher=lesson.teacher(),
                    rooms=lesson.room().split(" ") if lesson.room() else [],
                    periods={lesson.period} if lesson.period is not None else [],
                    info=lesson.information if lesson.information is not None else "",
                    parsed_info=parsed_info,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=lesson.teacher.was_changed,
                    room_changed=lesson.room.was_changed,
                    begin=lesson.start,
                    end=lesson.end
                ))

            for exam in form.exams:
                exam = copy.deepcopy(exam)
                exam.__class__ = Exam

                exams[form.short_name].append(exam)

        return cls(
            lessons=Lessons(lessons, form_plan.date),
            additional_info=form_plan.additional_info,

            form_plan=form_plan,
            exams=exams
        )

    def week_letter(self):
        return {
            1: "A",
            2: "B"
        }.get(self.form_plan.week, "?")


@dataclasses.dataclass
class Teacher:
    abbreviation: str | None
    full_name: str | None = None
    surname: str | None = None
    info: str | None = None
    subjects: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "abbreviation": self.abbreviation,
            "full_name": self.full_name,
            "surname": self.surname,
            "info": self.info,
            "subjects": self.subjects
        }

    @classmethod
    def from_dict(cls, data: dict) -> Teacher:
        return cls(
            abbreviation=data["abbreviation"],
            full_name=data["full_name"],
            surname=data["surname"],
            info=data["info"],
            subjects=data["subjects"]
        )

    def merge(self, other: Teacher) -> Teacher:
        return Teacher(
            full_name=self.full_name or other.full_name,
            surname=self.surname or other.surname,
            info=self.info or other.info,
            abbreviation=self.abbreviation or other.abbreviation,
            subjects=list(set(self.subjects + other.subjects))
        )

    def surname_no_titles(self):
        """Strip parts of self.surname like "Dr." and return it."""
        if self.surname is not None:
            return " ".join(filter(lambda x: "." not in x, self.surname.split(" ")))
        else:
            return None


@dataclasses.dataclass
class Teachers:
    teachers: list[Teacher] = dataclasses.field(default_factory=list)
    timestamp: datetime.datetime = datetime.datetime.min

    def to_dict(self) -> dict:
        return {
            "teachers": {teacher.abbreviation: teacher.to_dict() for teacher in self.teachers},
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> Teachers:
        return cls(
            teachers=[Teacher.from_dict(teacher) for teacher in data["teachers"].values()],
            timestamp=datetime.datetime.fromisoformat(data["timestamp"])
        )

    def abbreviation_by_surname(self) -> dict[str, str]:
        return {teacher.surname_no_titles(): teacher.abbreviation
                for teacher in self.teachers
                if teacher.surname is not None}


@dataclasses.dataclass
class Room:
    house: int | str
    floor: int | None
    room_nr: int | None
    appendix: str = ""

    def to_short(self) -> str:
        if isinstance(self.house, str):
            assert self.floor is None
            return self.house + (str(self.room_nr) if self.room_nr else "") + self.appendix

        if self.floor < 0:
            return f"-{self.house}{abs(self.floor)}{self.room_nr:02}{self.appendix}"
        elif self.floor == 0:
            return f"{self.house}{self.room_nr:02}{self.appendix}"
        else:
            return f"{self.house}{self.floor}{self.room_nr:02}{self.appendix}"

    def to_dict(self) -> dict:
        return {
            "house": self.house,
            "floor": self.floor,
            "room_nr": self.room_nr,
            "appendix": self.appendix
        }


@dataclasses.dataclass
class DefaultTimesInfo:
    data: dict[int, tuple[datetime.time, datetime.time]]

    def to_dict(self) -> dict:
        return {
            period: (start.strftime("%H:%M"), end.strftime("%H:%M")) for period, (start, end) in self.data.items()
        }

    def current_period(self) -> int:
        """Return the current period based on the current time.

        If we are in the break between two periods, the next period is returned."""

        now = datetime.datetime.now().time()

        for period, (start, end) in self.data.items():
            if now < start:
                return period - 1

            if start <= now < end:
                return period
