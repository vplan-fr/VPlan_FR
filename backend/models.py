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
    periods: set[int]

    # None means we don't know
    scheduled_forms: set[str]
    scheduled_teachers: set[str] | None
    scheduled_rooms: set[str] | None
    scheduled_class: str | None

    current_forms: set[str]
    current_teachers: set[str]
    current_rooms: set[str]
    current_class: str | None  # is class group if available, then subject

    # taken directly from plan xml
    class_subject: str | None
    class_group: str | None
    class_teachers: set[str] | None
    class_number: str | None

    # taken directly from plan xml
    subject_changed: bool
    teacher_changed: bool
    room_changed: bool

    info: str
    parsed_info: ParsedLessonInfo

    begin: datetime.time | None
    end: datetime.time | None

    # different for different plan types
    takes_place: bool | None = None

    is_internal: bool = False

    def serialize(self, lesson_date: datetime.date) -> dict:
        return {
            "periods": sorted(self.periods),
            "scheduled_forms": sorted(self.scheduled_forms),
            "scheduled_forms_str": vplan_utils.forms_to_str(self.scheduled_forms),
            "scheduled_teachers": sorted(self.scheduled_teachers) if self.scheduled_teachers else None,
            "scheduled_rooms": sorted(self.current_rooms) if self.scheduled_rooms else None,
            "scheduled_class": self.scheduled_class,
            "current_forms": sorted(self.current_forms),
            "current_forms_str": vplan_utils.forms_to_str(self.current_forms),
            "current_rooms": sorted(self.current_rooms),
            "current_teachers": sorted(self.current_teachers),
            "current_class": self.current_class,
            "class_subject": self.class_subject,
            "class_group": self.class_group,
            "class_teachers": sorted(self.class_teachers) if self.class_teachers else None,
            "class_number": self.class_number,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            # "info": self.info,
            "info": self.parsed_info.serialize(lesson_date, self),
            "begin": self.begin.strftime("%H:%M") if self.begin else None,
            "takes_place": self.takes_place,
            "end": self.end.strftime("%H:%M") if self.end else None,
        }

    @classmethod
    def create_internal(cls):
        return cls(
            periods=set(),
            scheduled_forms=set(),
            scheduled_teachers=None,
            scheduled_rooms=None,
            scheduled_class=None,
            current_forms=set(),
            current_teachers=set(),
            current_rooms=set(),
            current_class=None,
            info="",
            parsed_info=ParsedLessonInfo([]),
            class_subject=None,
            class_group=None,
            class_teachers=None,
            class_number=None,
            subject_changed=False,
            teacher_changed=False,
            room_changed=False,
            begin=None,
            end=None,
            is_internal=True
        )

    def with_takes_place(self, plan_type: typing.Literal["rooms", "forms", "teachers"], value: str) -> Lesson:
        takes_place = value in getattr(self, f"current_{plan_type}")
        return dataclasses.replace(self, takes_place=takes_place)


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

    def with_takes_place(self, plan_type: typing.Literal["rooms", "forms", "teachers"], value: str) -> Lessons:
        return Lessons(
            [lesson.with_takes_place(plan_type, value) for lesson in self.lessons],
            self.date
        )

    def make_plan(self, attributes: tuple[str, ...],
                  plan_type: typing.Literal["rooms", "forms", "teachers"]) -> dict[str, Lessons]:
        grouped = self.group_by(*attributes)

        return {
            attribute: lessons.with_takes_place(plan_type, attribute)
            for attribute, lessons in grouped.items()
        }

    def serialize(self) -> list[dict]:
        return [lesson.serialize(self.date) for lesson in self.lessons]

    @staticmethod
    def _group_lesson_info(
            parsed_info1: ParsedLessonInfo,
            parsed_info2: ParsedLessonInfo
    ) -> ParsedLessonInfo | None:
        """Group two parsed lesson infos if possible."""

        if len(parsed_info1.paragraphs) != len(parsed_info2.paragraphs):
            return None

        info1: ParsedLessonInfo = parsed_info1.sorted_canonical()
        info2: ParsedLessonInfo = parsed_info2.sorted_canonical()

        new_info = []

        for paragraph1, paragraph2 in zip(info1.paragraphs, info2.paragraphs):
            if len(paragraph1.messages) != len(paragraph2.messages):
                return None

            new_paragraph = []
            for message1, message2 in zip(paragraph1.messages, paragraph2.messages):
                message1: LessonInfoMessage
                message2: LessonInfoMessage

                if type(message1.parsed) != type(message2.parsed):
                    # only infos of same type could possibly be grouped -> not groupable
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

                # periods not groupable, so, to group, info string must be the same
                elif message1.parsed.original_messages == message2.parsed.original_messages:
                    new_paragraph.append(message1)

                else:
                    return None

            new_info.append(LessonInfoParagraph(new_paragraph, paragraph1.index))

        out = ParsedLessonInfo(new_info)
        out.sort_original()
        return out

    def blocks_grouped(self) -> Lessons:
        assert all(len(x.periods) <= 1 for x in self.lessons), \
            "Lessons must be ungrouped. (Must only have one period.)"

        sorted_lessons = sorted(
            self.lessons,
            key=lambda x: (x.current_class if x.current_class is not None else "",
                           x.current_teachers,
                           x.parsed_info.lesson_group_sort_key(),
                           x.class_group if x.class_group is not None else "",
                           x.scheduled_forms,
                           x.periods)
        )

        grouped: list[Lesson] = []

        previous_lesson: Lesson | None = None
        for lesson in sorted_lessons:
            can_get_grouped = (
                    previous_lesson is not None and
                    lesson.current_rooms == previous_lesson.current_rooms and
                    lesson.current_class == previous_lesson.current_class and
                    lesson.current_teachers == previous_lesson.current_teachers and
                    lesson.class_number == previous_lesson.class_number
            )

            if previous_lesson is not None:
                grouped_additional_info = self._group_lesson_info(lesson.parsed_info, previous_lesson.parsed_info)

                can_get_grouped &= grouped_additional_info is not None
            else:
                grouped_additional_info = None

            if previous_lesson is not None:
                if (
                        # both lessons have no form
                        (not lesson.scheduled_forms and not grouped[-1].scheduled_forms)
                        # or lesson form is the same as previous lesson form
                        # when this method is called, lessons should only have one form
                        or (lesson.scheduled_forms and list(lesson.scheduled_forms)[0] in grouped[-1].scheduled_forms)
                ):
                    # "temporal" grouping, since lesson is duplicated for each period of block,
                    # period must be even to get grouped onto first lesson of block
                    can_get_grouped &= list(lesson.periods)[0] % 2 == 0
                else:
                    # lesson is duplicated for each form -> periods must be the same ("spacial" grouping)
                    can_get_grouped &= list(lesson.periods)[-1] in grouped[-1].periods

            if can_get_grouped:
                grouped[-1].periods |= lesson.periods
                grouped[-1].scheduled_forms |= lesson.scheduled_forms
                grouped[-1].current_forms |= lesson.current_forms
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
    def serialize(self) -> dict:
        return {
            "year": self.year,
            "course": self.course,
            "course_teacher": self.course_teacher,
            "period": self.period,
            "begin": self.begin.strftime("%H:%M"),
            "duration": self.duration,
            "info": self.info
        }


@dataclasses.dataclass
class Plan:
    lessons: Lessons
    additional_info: list[str]
    exams: dict[str, list[Exam]]

    form_plan: indiware_mobil.IndiwareMobilPlan

    @classmethod
    def from_form_plan(cls, form_plan: indiware_mobil.IndiwareMobilPlan) -> Plan:
        lessons: list[Lesson] = []
        exams: dict[str, list[Exam]] = defaultdict(list)
        for form in form_plan.forms:
            for lesson in form.lessons:
                parsed_info = ParsedLessonInfo.from_str(
                    lesson.information, form_plan.timestamp.year
                ) if lesson.information is not None else ParsedLessonInfo([])

                new_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else [],

                    scheduled_forms={form.short_name},
                    scheduled_teachers=None,
                    scheduled_rooms=None,
                    scheduled_class=lesson.course2,

                    current_forms={form.short_name},
                    current_teachers=set(lesson.teacher().split()) if lesson.teacher() else set(),
                    current_rooms=lesson.room().split(" ") if lesson.room() else [],
                    current_class=lesson.subject(),

                    info=lesson.information if lesson.information is not None else "",
                    parsed_info=parsed_info,

                    class_subject=(
                        form.classes[lesson.class_number].subject if lesson.class_number in form.classes else None
                    ),
                    class_group=(
                        form.classes[lesson.class_number].group if lesson.class_number in form.classes else None
                    ),
                    class_teachers=(
                        set(form.classes[lesson.class_number].teacher.split())
                        if lesson.class_number in form.classes else None
                    ),
                    class_number=lesson.class_number,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=lesson.teacher.was_changed,
                    room_changed=lesson.room.was_changed,

                    begin=lesson.start,
                    end=lesson.end
                )
                if new_lesson.current_class == "---" and new_lesson.subject_changed:
                    # Indiware Stundenplaner's way of telling us that the lesson is cancelled
                    new_lesson.current_forms = set()
                    new_lesson.current_class = None
                    # the following should be empty already
                    # new_lesson.current_teachers = set()
                    # new_lesson.current_rooms = set()

                new_lesson.scheduled_class = (
                        new_lesson.scheduled_class or new_lesson.class_group or new_lesson.class_subject
                )
                new_lesson.scheduled_teachers = new_lesson.class_teachers

                lessons.append(new_lesson)

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

    def get_all_classes(self) -> dict[str, Class]:
        out: dict[str, Class] = {}

        for form in self.form_plan.forms:
            for class_nr, class_ in form.classes.items():
                if class_nr in out:
                    out[class_nr].forms.add(form.short_name)
                else:
                    out[class_nr] = Class(
                        teacher=class_.teacher,
                        subject=class_.subject,
                        group=class_.group,
                        forms={form.short_name}
                    )

        return out


@dataclasses.dataclass
class Class(indiware_mobil.Class):
    forms: set[str]


@dataclasses.dataclass
class Teacher:
    abbreviation: str | None
    full_name: str | None = None
    surname: str | None = None
    info: str | None = None
    subjects: list[str] = dataclasses.field(default_factory=list)

    def serialize(self) -> dict:
        return {
            "abbreviation": self.abbreviation,
            "full_name": self.full_name,
            "surname": self.surname,
            "info": self.info,
            "subjects": self.subjects
        }

    @classmethod
    def deserialize(cls, data: dict) -> Teacher:
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
    scrape_timestamp: datetime.datetime = datetime.datetime.min

    def serialize(self) -> dict:
        return {
            "teachers": {teacher.abbreviation: teacher.serialize() for teacher in self.teachers},
            "timestamp": self.scrape_timestamp.isoformat()
        }

    @classmethod
    def deserialize(cls, data: dict) -> Teachers:
        return cls(
            teachers=[Teacher.deserialize(teacher) for teacher in data["teachers"].values()],
            scrape_timestamp=datetime.datetime.fromisoformat(data["timestamp"])
        )

    def to_dict(self) -> dict[str, Teacher]:
        return {teacher.abbreviation: teacher for teacher in self.teachers}

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
