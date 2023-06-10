# coding=utf-8
from __future__ import annotations

import copy
import dataclasses
import datetime
from collections import defaultdict

from stundenplan24_py import indiware_mobil


@dataclasses.dataclass
class Lesson:
    form: str
    current_subject: str | None
    current_teacher: str | None
    class_subject: str | None
    class_group: str | None
    class_teacher: str | None
    class_number: str | None
    rooms: list[str]
    periods: list[int]
    info: str

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool

    begin: datetime.time
    end: datetime.time

    def to_json(self) -> dict:
        return {
            "form": self.form,
            "periods": self.periods,
            "rooms": self.rooms,
            "current_subject": self.current_subject,
            "current_teacher": self.current_teacher,
            "class_subject": self.class_subject,
            "class_group": self.class_group,
            "class_teacher": self.class_teacher,
            "class_number": self.class_number,
            "info": self.info,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "begin": self.begin.isoformat() if self.begin else None,
            "end": self.end.isoformat() if self.end else None
        }


@dataclasses.dataclass
class Lessons:
    lessons: list[Lesson]

    def group_by(self, attribute: str) -> dict[str, list[Lesson]]:
        grouped = defaultdict(list)

        for lesson in self.lessons:
            value = getattr(lesson, attribute)

            if not isinstance(value, list):
                value = [value]

            for element in value:
                grouped[element].append(lesson)

        return grouped

    def blocks_grouped(self) -> Lessons:
        assert all(len(x.periods) <= 1 for x in self.lessons)

        sorted_lessons = sorted(
            self.lessons,
            key=lambda x: (x.form, x.class_number if x.class_number is not None else "", x.periods[0])
        )

        grouped: list[Lesson] = []

        previous_lesson: Lesson | None = None
        for lesson in sorted_lessons:
            should_get_grouped = (
                    previous_lesson is not None and
                    lesson.form == previous_lesson.form and
                    lesson.periods[0] - 1 == previous_lesson.periods[0] and
                    previous_lesson.periods[0] % 2 == 1 and
                    lesson.class_number == previous_lesson.class_number and
                    lesson.rooms == previous_lesson.rooms and
                    lesson.current_subject == previous_lesson.current_subject and
                    lesson.current_teacher == previous_lesson.current_teacher
            )

            if should_get_grouped:
                grouped[-1].periods.append(lesson.periods[0])
                grouped[-1].info = "\n".join(filter(lambda x: x, [grouped[-1].info, lesson.info]))
                grouped[-1].end = lesson.end
            else:
                grouped.append(copy.deepcopy(lesson))

            previous_lesson = lesson

        return Lessons(sorted(grouped, key=lambda x: x.periods[0]))

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
                lessons.append(Lesson(
                    form=form.short_name,
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
                    periods=[lesson.period] if lesson.period is not None else [],
                    info=lesson.information if lesson.information is not None else "",
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
