# coding=utf-8
from __future__ import annotations

import dataclasses
import datetime
from collections import defaultdict
from .vplan_utils import remove_duplicates

from stundenplan24_py import indiware_mobil


@dataclasses.dataclass
class Lesson:
    form: str
    current_subject: str
    current_teacher: str
    class_subject: str
    class_group: str
    class_teacher: str
    class_number: str
    rooms: list[str]
    period: int
    info: str

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool

    begin: datetime.time
    end: datetime.time

    def to_json(self) -> dict:
        return {
            "form": self.form,
            "period": self.period,
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
class Plan:
    lessons: list[Lesson]
    additional_info: list[str]

    form_plan: indiware_mobil.FormPlan

    # exams: list[Exam]
    # TODO: reimplement exams

    def group_by(self, attribute: str, group_lessons: bool = False) -> dict[str, list[Lesson]]:
        grouped = defaultdict(list)

        for lesson in self.lessons:
            value = getattr(lesson, attribute)

            if not isinstance(value, list):
                value = [value]

            for element in value:
                grouped[element].append(lesson)
        if group_lessons:
            grouped = {k: remove_duplicates(v) for k, v in grouped.items()}
        return grouped

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
                    period=lesson.period,
                    info=lesson.information,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=lesson.teacher.was_changed,
                    room_changed=lesson.room.was_changed,
                    begin=lesson.start,
                    end=lesson.end
                ))

        return cls(
            lessons=lessons,
            additional_info=form_plan.additional_info,

            form_plan=form_plan
        )

    def week_letter(self):
        return {
            1: "A",
            2: "B"
        }.get(self.form_plan.week, "?")
