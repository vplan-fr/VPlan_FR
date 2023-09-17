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
    begin: datetime.time | None
    end: datetime.time | None

    forms: set[str]
    teachers: set[str] | None
    rooms: set[str] | None
    course: str | None  # class group if available else subject

    info: str
    parsed_info: ParsedLessonInfo

    # taken directly from plan xml
    class_: ClassData | None

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool

    is_scheduled: bool
    takes_place: bool | None = None  # whether this lesson in its current form takes place

    is_internal: bool = False
    _lesson_date: datetime.date = None

    @property
    def class_opt(self):
        if self.class_ is None:
            # noinspection PyTypeChecker
            return ClassData(None, None, None, None)
        else:
            return self.class_

    @classmethod
    def create_internal(cls):
        return cls(
            periods=set(),
            forms=set(),
            teachers=None,
            rooms=None,
            course=None,
            info="",
            parsed_info=ParsedLessonInfo([]),
            class_=None,
            subject_changed=False,
            teacher_changed=False,
            room_changed=False,
            begin=None,
            end=None,
            takes_place=True,
            is_internal=True,
            is_scheduled=False,
            _lesson_date=None,
        )

    def serialize(self) -> dict:
        return {
            "periods": sorted(self.periods),
            "forms": sorted(self.forms),
            "teachers": sorted(self.teachers) if self.teachers is not None else None,
            "rooms": sorted(self.rooms) if self.rooms is not None else None,
            "course": self.course,
            "begin": self.begin.strftime("%H:%M") if self.begin else None,
            "end": self.end.strftime("%H:%M") if self.end else None,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "takes_place": self.takes_place,
            "is_internal": self.is_internal,
            "is_scheduled": self.is_scheduled,
            "class_data": repr(self.class_),
        }


@dataclasses.dataclass
class ClassData(indiware_mobil.Class):
    number: str


@dataclasses.dataclass
class PlanLesson:
    periods: set[int]
    begin: datetime.time | None
    end: datetime.time | None

    # None means we don't know
    scheduled_forms: set[str]
    scheduled_teachers: set[str] | None
    scheduled_rooms: set[str] | None
    scheduled_course: str | None

    current_forms: set[str]
    current_teachers: set[str]
    current_rooms: set[str]
    current_course: str | None

    class_number: str

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool
    forms_changed: bool

    info: str
    parsed_info: ParsedLessonInfo

    takes_place: bool | None = None

    is_internal: bool = False
    _lesson_date: datetime.date = None

    def serialize(self) -> dict:
        return {
            "periods": sorted(self.periods),
            "scheduled_forms": sorted(self.scheduled_forms) if self.scheduled_forms is not None else None,
            "scheduled_forms_str": (
                vplan_utils.forms_to_str(self.scheduled_forms) if self.scheduled_forms is not None else None
            ),
            "scheduled_teachers": sorted(self.scheduled_teachers) if self.scheduled_teachers is not None else None,
            "scheduled_rooms": sorted(self.current_rooms) if self.current_rooms is not None else None,
            "scheduled_class": self.scheduled_course,
            "current_forms": sorted(self.current_forms),
            "current_forms_str": vplan_utils.forms_to_str(self.current_forms),
            "current_rooms": sorted(self.current_rooms) if self.current_rooms is not None else None,
            "current_teachers": sorted(self.current_teachers) if self.current_teachers is not None else None,
            "current_class": self.current_course,
            "class_number": self.class_number,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "forms_changed": self.forms_changed,
            # "info": self.info,
            "info": self.parsed_info.serialize(self._lesson_date, self),
            "begin": self.begin.strftime("%H:%M") if self.begin else None,
            "takes_place": self.takes_place,
            "end": self.end.strftime("%H:%M") if self.end else None,
        }


@dataclasses.dataclass
class Lessons:
    lessons: list[Lesson]

    def group_by(self, *attributes: str, include_none: bool = False) -> dict[str, Lessons]:
        grouped_i = defaultdict(set)

        for lesson_i, lesson in enumerate(self.lessons):
            for attribute in attributes:
                value = getattr(lesson, attribute, None)

                if not include_none and value is None:
                    continue

                if not isinstance(value, (list, set)):
                    value = [value]

                for element in value:
                    grouped_i[element].add(lesson_i)

        grouped = {attribute: [self.lessons[i] for i in indices] for attribute, indices in grouped_i.items()}

        return {attribute: Lessons(sorted(lessons, key=lambda x: list(x.periods)[0]))
                for attribute, lessons in grouped.items()}

    def to_plan_lessons(self) -> list[PlanLesson]:

        lessons_by_periods: dict[frozenset[int], list[Lesson]] = defaultdict(list)
        for lesson in self:
            lessons_by_periods[frozenset(lesson.periods)].append(lesson)

        out: list[PlanLesson] = []

        for periods, lessons in lessons_by_periods.items():
            scheduled_lessons = [lesson for lesson in lessons if lesson.is_scheduled]
            used_scheduled_lessons = []
            lessons.sort(key=lambda l: (
                not l.subject_changed,
                l.takes_place,
                l.course if l.course else "",
            ), reverse=True)

            for current_lesson in lessons:
                if current_lesson.is_scheduled:
                    continue

                # if len(scheduled_lessons) == 1 and scheduled_lessons[0].course is not None:
                #     scheduled_lesson = scheduled_lessons[0]
                # else:
                for scheduled_lesson in scheduled_lessons:
                    if scheduled_lesson.class_opt.number is not None is not current_lesson.class_opt.number:
                        if scheduled_lesson.class_opt.number == current_lesson.class_opt.number:
                            break
                else:
                    for scheduled_lesson in scheduled_lessons:
                        # if None is not scheduled_lesson.class_opt.number == current_lesson.class_opt.number is not None:
                        #     break
                        if (
                                # scheduled_lesson.course is not None is not current_lesson.course and
                                (scheduled_lesson.course != current_lesson.course) in (
                                False, current_lesson.subject_changed)
                        ):
                            break
                    else:
                        scheduled_lesson = None

                if not current_lesson.takes_place:
                    # try to find corresponding used scheduled lesson to drop this lesson
                    found = False
                    for used_scheduled_lesson in used_scheduled_lessons:
                        if (
                                used_scheduled_lesson.course == current_lesson.course and
                                used_scheduled_lesson.teachers == current_lesson.teachers and
                                used_scheduled_lesson.forms == current_lesson.forms
                        ):
                            found = True
                            break

                    if found:
                        continue

                if scheduled_lesson is not None:
                    scheduled_lessons.remove(scheduled_lesson)
                    used_scheduled_lessons.append(scheduled_lesson)

                plan_lesson = PlanLesson(
                    periods=set(periods),
                    begin=current_lesson.begin,
                    end=current_lesson.end,
                    scheduled_forms=scheduled_lesson.forms if scheduled_lesson is not None else None,
                    scheduled_teachers=scheduled_lesson.teachers if scheduled_lesson is not None else None,
                    scheduled_rooms=scheduled_lesson.rooms if scheduled_lesson is not None else None,
                    scheduled_course=scheduled_lesson.course if scheduled_lesson is not None else None,
                    current_forms=current_lesson.forms,
                    current_teachers=current_lesson.teachers,
                    current_rooms=current_lesson.rooms,
                    current_course=current_lesson.course,
                    class_number=current_lesson.class_opt.number,
                    subject_changed=current_lesson.subject_changed,
                    teacher_changed=current_lesson.teacher_changed,
                    room_changed=current_lesson.room_changed,
                    forms_changed=current_lesson.forms != scheduled_lesson.forms if scheduled_lesson is not None else True,
                    info=current_lesson.info,  # TODO
                    parsed_info=current_lesson.parsed_info,
                    takes_place=current_lesson.takes_place,
                    is_internal=current_lesson.is_internal,
                    _lesson_date=current_lesson._lesson_date
                )

                if not plan_lesson.takes_place and scheduled_lesson is not None:
                    plan_lesson.current_forms = set()
                    plan_lesson.current_teachers = set()
                    plan_lesson.current_rooms = set()
                    plan_lesson.current_course = None

                out.append(plan_lesson)

            # convert remaining scheduled lessons
            for scheduled_lesson in scheduled_lessons:
                out.append(PlanLesson(
                    periods=set(periods),
                    begin=scheduled_lesson.begin,
                    end=scheduled_lesson.end,
                    scheduled_forms=scheduled_lesson.forms,
                    scheduled_teachers=scheduled_lesson.teachers,
                    scheduled_rooms=scheduled_lesson.rooms,
                    scheduled_course=scheduled_lesson.course,
                    current_forms=set(),
                    current_teachers=set(),
                    current_rooms=set(),
                    current_course=None,
                    class_number=scheduled_lesson.class_opt.number,
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    forms_changed=False,
                    info=scheduled_lesson.info,  # TODO
                    parsed_info=scheduled_lesson.parsed_info,
                    takes_place=False,
                    is_internal=scheduled_lesson.is_internal,
                    _lesson_date=scheduled_lesson._lesson_date
                ))

        return out

    def make_plan(self, plan_type: str,
                  *additional_attrs: str) -> dict[str, list[PlanLesson]]:
        grouped_lessons = self.group_by(plan_type, *additional_attrs)

        return {
            group: lessons.to_plan_lessons()
            for group, lessons in grouped_lessons.items()
        }

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
            key=lambda x: (str(x.is_scheduled),
                           x.class_.number if x.class_ else (x.course if x.course else ""),
                           x.teachers or set(),
                           x.parsed_info.lesson_group_sort_key(),
                           x.class_opt.group or "",
                           x.forms or set(),
                           x.periods or set())
        )

        grouped: list[Lesson] = []

        previous_lesson: Lesson | None = None
        for lesson in sorted_lessons:
            can_get_grouped = (
                    previous_lesson is not None and
                    lesson.rooms == previous_lesson.rooms and
                    lesson.course == previous_lesson.course and
                    lesson.teachers == previous_lesson.teachers and
                    lesson.class_opt.number == previous_lesson.class_opt.number
            )

            if previous_lesson is not None:
                grouped_additional_info = self._group_lesson_info(lesson.parsed_info, previous_lesson.parsed_info)

                can_get_grouped &= grouped_additional_info is not None
            else:
                grouped_additional_info = None

            if previous_lesson is not None:
                if (
                        # both lessons have no form
                        (not lesson.forms and not grouped[-1].forms)
                        # or lesson form is the same as previous lesson form
                        # when this method is called, lessons should only have one form
                        or (lesson.forms and list(lesson.forms)[0] in grouped[-1].forms)
                ):
                    # "temporal" grouping, since lesson is duplicated for each period of block,
                    # period must be even to get grouped onto first lesson of block
                    can_get_grouped &= list(lesson.periods)[0] % 2 == 0
                else:
                    # lesson is duplicated for each form -> periods must be the same ("spacial" grouping)
                    can_get_grouped &= list(lesson.periods)[-1] in grouped[-1].periods

            if can_get_grouped:
                grouped[-1].periods |= lesson.periods
                grouped[-1].forms |= lesson.forms
                grouped[-1].info = "\n".join(filter(lambda x: x, [grouped[-1].info, lesson.info]))
                grouped[-1].parsed_info = grouped_additional_info
                grouped[-1].begin = min(filter(lambda x: x, (grouped[-1].begin, lesson.begin)), default=None)
                grouped[-1].end = min(filter(lambda x: x, (grouped[-1].end, lesson.end)), default=None)
            else:
                grouped.append(copy.deepcopy(lesson))

            previous_lesson = lesson

        return Lessons(sorted(grouped, key=lambda x: x.periods))

    def filter(self, function: typing.Callable[[Lesson], bool]) -> Lessons:
        return Lessons(list(filter(function, self.lessons)))

    def serialize(self) -> list:
        return [lesson.serialize() for lesson in self.lessons]

    def __iter__(self):
        return iter(self.lessons)

    def __len__(self):
        return len(self.lessons)


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

    indiware_plan: indiware_mobil.IndiwareMobilPlan

    @classmethod
    def from_form_plan(cls, form_plan: indiware_mobil.IndiwareMobilPlan) -> Plan:
        lessons: list[Lesson] = []
        exams: dict[str, list[Exam]] = defaultdict(list)
        all_classes = {number: class_ for form in form_plan.forms for number, class_ in form.classes.items()}
        for form in form_plan.forms:
            for lesson in form.lessons:
                # lesson.information = "lesson information unavailable"  # TODO
                parsed_info = ParsedLessonInfo.from_str(
                    lesson.information, form_plan.timestamp.year
                ) if lesson.information is not None else ParsedLessonInfo([])

                if lesson.class_number in all_classes:
                    _class = all_classes[lesson.class_number]

                    class_data = ClassData(
                        teacher=_class.teacher,
                        subject=_class.subject,
                        group=_class.group,
                        number=lesson.class_number
                    )
                else:
                    class_data = None

                current_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms={form.short_name},
                    teachers=set(lesson.teacher().split()) if lesson.teacher() else set(),
                    # TODO: Some schools use rooms with spaces
                    rooms=set(lesson.room().split(" ")) if lesson.room() else set(),
                    course=lesson.subject(),

                    info=lesson.information if lesson.information is not None else "",
                    parsed_info=parsed_info,

                    class_=class_data,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=lesson.teacher.was_changed,
                    room_changed=lesson.room.was_changed,
                    _lesson_date=form_plan.date,
                    is_scheduled=False
                )

                scheduled_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms={form.short_name},
                    teachers={class_data.teacher} if class_data is not None else None,
                    rooms=current_lesson.rooms if not current_lesson.room_changed else None,
                    course=(
                            lesson.course2
                            or (class_data.group if class_data is not None else None)
                            or (class_data.subject if class_data is not None else None)
                            or (current_lesson.course if not current_lesson.room_changed else None)
                    ),

                    info=lesson.information if lesson.information is not None else "",
                    parsed_info=parsed_info,

                    class_=class_data,
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    takes_place=None,
                    is_scheduled=True,
                    _lesson_date=form_plan.date,
                )

                if current_lesson.course == "---" and current_lesson.subject_changed:
                    # Indiware Stundenplaner's way of telling us that the lesson is cancelled
                    current_lesson.course = scheduled_lesson.course
                    current_lesson.teachers = scheduled_lesson.teachers
                    current_lesson.rooms = scheduled_lesson.rooms
                    current_lesson.takes_place = False
                    scheduled_lesson.takes_place = False
                    # the following should be true already
                    current_lesson.subject_changed = True
                    current_lesson.teacher_changed = True
                    current_lesson.room_changed = True
                else:
                    current_lesson.takes_place = True
                    scheduled_lesson.takes_place = False
                #
                # if current_lesson.subject_changed:
                #     scheduled_lesson.class_ = None

                for l in current_lesson, scheduled_lesson:
                    l._grouped_form_plan_current_course = current_lesson.course
                    l._grouped_form_plan_current_teachers = current_lesson.teachers
                    l._grouped_form_plan_current_rooms = current_lesson.rooms
                    l._grouped_form_plan_current_forms = current_lesson.forms
                    l._grouped_form_plan_scheduled_course = scheduled_lesson.course
                    l._grouped_form_plan_scheduled_teachers = scheduled_lesson.teachers
                    l._grouped_form_plan_scheduled_rooms = scheduled_lesson.rooms
                    l._grouped_form_plan_scheduled_forms = scheduled_lesson.forms

                lessons.append(scheduled_lesson)
                lessons.append(current_lesson)

            for exam in form.exams:
                exam = copy.deepcopy(exam)
                exam.__class__ = Exam

                exams[form.short_name].append(exam)

        return cls(
            lessons=Lessons(lessons),
            additional_info=form_plan.additional_info,

            indiware_plan=form_plan,
            exams=exams
        )

    def week_letter(self):
        return {
            1: "A",
            2: "B"
        }.get(self.indiware_plan.week, "?")

    def get_all_classes(self) -> dict[str, Class]:
        out: dict[str, Class] = {}

        for form in self.indiware_plan.forms:
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
