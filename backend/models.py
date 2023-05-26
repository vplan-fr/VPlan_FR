# coding=utf-8
from __future__ import annotations

import dataclasses
import datetime
from collections import defaultdict

from stundenplan24_py import indiware_mobil


@dataclasses.dataclass
class Lesson:
    form_name: str
    # subject_name: str
    subject: str
    course_id: str
    room: list[str]
    teacher: str
    period: int
    info: str

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool

    begin: datetime.time
    end: datetime.time

    def to_json(self) -> dict:
        return {
            "form": self.form_name,
            "period": self.period,
            "room": self.room,
            "subject": self.subject,
            # "subject_name": self.subject_name,
            "info": self.info,
            "teacher": self.teacher,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "begin": self.begin.isoformat() if self.begin else None,
            "end": self.end.isoformat() if self.end else None,
            "course_id": self.course_id
        }


@dataclasses.dataclass
class Plan:
    lessons: list[Lesson]
    additional_info: list[str]

    form_plan: indiware_mobil.FormPlan

    # exams: list[Exam]
    # TODO: reimplement exams

    def group_by(self, attribute: str) -> dict[str, list[Lesson]]:
        grouped = defaultdict(list)

        for lesson in self.lessons:
            value = getattr(lesson, attribute)

            if not isinstance(value, list):
                value = [value]

            for element in value:
                grouped[element].append(lesson)

        return grouped

    # def get_plan_filtered_courses(self, course):
    #     group_list = MetaExtractor(self.school_num).group_list(course)
    #     unselected_courses = [elem[0] for elem in group_list if elem[0] not in self.preferences]
    #     normal_plan = self.get_plan_normal(course)
    #     return self.render(
    #         [lesson for lesson in normal_plan["lessons"] if lesson["subject_name"] not in unselected_courses])

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
                    form_name=form.short_name,
                    subject=lesson.subject(),
                    course_id=lesson.number,
                    room=lesson.room().split(" ") if lesson.room() else [],
                    teacher=lesson.teacher(),
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
