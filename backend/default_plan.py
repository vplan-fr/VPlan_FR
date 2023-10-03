from __future__ import annotations

import copy
import dataclasses
import typing

from . import models


@dataclasses.dataclass
class DefaultPlanInfo:
    unchanged_lessons: list[models.Lesson] = dataclasses.field(default_factory=list)
    week: int | None = None

    @classmethod
    def from_lessons(cls, lessons: typing.Iterable[models.Lesson]) -> DefaultPlanInfo:
        out = cls()

        for lesson in lessons:
            if len(lesson.parsed_info.paragraphs) != 0:
                continue

            if not lesson._is_scheduled or lesson.is_internal or lesson.subject_changed:
                continue

            lesson = copy.deepcopy(lesson)

            if lesson.teacher_changed:
                lesson.teachers = None

            if lesson.room_changed:
                lesson.rooms = None

            if lesson.forms_changed:
                lesson.forms = None
                assert False, f"{cls.__name__}.from_lessons() only supports lessons from form plans."

            out.unchanged_lessons.append(lesson)

        return out

    def serialize(self):
        return {
            "unchanged_lessons": [lesson.serialize() for lesson in self.unchanged_lessons],
            "week": self.week
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            unchanged_lessons=[models.Lesson.deserialize(lesson) for lesson in data["unchanged_lessons"]],
            week=data["week"]
        )
