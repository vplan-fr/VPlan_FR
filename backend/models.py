# coding=utf-8
from __future__ import annotations

import copy
import dataclasses
import datetime
from collections import defaultdict

from stundenplan24_py import indiware_mobil

from .lesson_info import parse_info, ParsedLessonInfo, sort_info, MovedFromPeriod, InsteadOfPeriod, CourseHeldAt, \
    MovedTo


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

    def to_json(self) -> dict:
        return {
            "forms": sorted(self.forms),
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
            "parsed_info": [[(info_str, info.to_json() if info is not None else None) for info_str, info in infos]
                            for infos in self.parsed_info]
        }


@dataclasses.dataclass
class Lessons:
    lessons: list[Lesson]

    def group_by(self, *attributes: str, include_none: bool = False) -> dict[str, list[Lesson]]:
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

        return {attribute: sorted(lessons, key=lambda x: list(x.periods)[0])
                for attribute, lessons in grouped.items()}

    @staticmethod
    def _group_lesson_info(
            parsed_info1: ParsedLessonInfo,
            parsed_info2: ParsedLessonInfo
    ) -> ParsedLessonInfo | None:
        info1 = sort_info(parsed_info1)
        info2 = sort_info(parsed_info2)

        new_info = []

        for info1_part, info2_part in zip(info1, info2):
            new_part_info = []
            for (info_str1, info1), (info_str2, info2) in zip(info1_part, info2_part):
                if type(info1) != type(info2):
                    # both infos are definitely not the same
                    return None

                # info string not the same, but groupable
                if isinstance(info1, (MovedFromPeriod, InsteadOfPeriod, CourseHeldAt, MovedTo)):
                    if info1.is_groupable(info2):
                        new_part_part_info = copy.deepcopy(info1)
                        new_part_part_info.periods += info2.periods
                        new_info_str = new_part_part_info.to_blocked_str()
                        new_part_info.append((new_info_str, new_part_part_info))
                    else:
                        return None

                # not groupable, so info string must be the same
                elif info_str1 == info_str2:
                    new_part_info.append((info_str1, info1))

                else:
                    return None

            new_info.append(new_part_info)

        return new_info

    def blocks_grouped(self) -> Lessons:
        assert all(len(x.periods) <= 1 and len(x.forms) for x in self.lessons), \
            "Lessons must be ungrouped. (Must only have one period.)"

        sorted_lessons = sorted(
            self.lessons,
            key=lambda x: (x.current_subject if x.current_subject is not None else "", x.forms, x.periods)
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
                if list(lesson.forms)[0] in grouped[-1].forms:
                    should_get_grouped &= (
                        # lesson.periods[0] - previous_lesson.periods[0] == 1 and

                        list(lesson.periods)[0] % 2 == 0
                    )
                else:
                    should_get_grouped &= (
                        list(lesson.periods)[-1] in grouped[-1].periods
                    )

            if should_get_grouped:
                grouped[-1].periods |= lesson.periods
                grouped[-1].forms |= lesson.forms
                grouped[-1].info = "\n".join(filter(lambda x: x, [grouped[-1].info, lesson.info]))
                grouped[-1].parsed_info = grouped_additional_info
                grouped[-1].end = lesson.end
            else:
                grouped.append(copy.deepcopy(lesson))

            previous_lesson = lesson

        return Lessons(sorted(grouped, key=lambda x: x.periods))

    def __iter__(self):
        return iter(self.lessons)


@dataclasses.dataclass
class Plan:
    lessons: Lessons
    additional_info: list[str]

    form_plan: indiware_mobil.FormPlan

    # exams: list[Exam]
    # TODO: reimplement exams

    def to_json(self) -> dict:
        return {
            "lessons": sorted([lesson.to_json() for lesson in self.lessons], key=lambda x: x["period"]),
            "additional_info": self.additional_info,
            # "exams": self.exams
        }

    @classmethod
    def from_form_plan(cls, form_plan: indiware_mobil.FormPlan) -> Plan:
        lessons = []
        for form in form_plan.forms:
            for lesson in form.lessons:
                parsed_info = (
                    parse_info(lesson.information, form_plan.timestamp.year)
                    if lesson.information is not None else []
                )

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

        return cls(
            lessons=Lessons(lessons),
            additional_info=form_plan.additional_info,

            form_plan=form_plan
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

    def to_json(self) -> dict:
        return {
            "abbreviation": self.abbreviation,
            "full_name": self.full_name,
            "surname": self.surname,
            "info": self.info,
            "subjects": self.subjects
        }

    def merge(self, other: Teacher) -> Teacher:
        return Teacher(
            full_name=self.full_name or other.full_name,
            surname=self.surname or other.surname,
            info=self.info or other.info,
            abbreviation=self.abbreviation or other.abbreviation,
            subjects=list(set(self.subjects + other.subjects))
        )


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

    def to_json(self) -> dict:
        return {
            "house": self.house,
            "floor": self.floor,
            "room_nr": self.room_nr,
            "appendix": self.appendix
        }


@dataclasses.dataclass
class DefaultTimesInfo:
    data: dict[int, tuple[datetime.time, datetime.time]]

    def to_json(self) -> dict:
        return {
            period: (start.isoformat(), end.isoformat()) for period, (start, end) in self.data.items()
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
