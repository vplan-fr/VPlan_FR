import dataclasses
from collections import defaultdict

from . import models


@dataclasses.dataclass
class LessonsStatistics:
    count: int = 0
    cancelled: int = 0
    changed: int = 0
    absent_teachers: int = 0

    @classmethod
    def from_lessons(cls, lessons: models.Lessons):
        out = LessonsStatistics()

        teacher_is_absent = defaultdict(lambda: True)

        for lesson in lessons:
            # TODO
            if lesson._is_scheduled:
                continue

            out.count += 1

            if not lesson.takes_place:
                out.cancelled += 1
                out.changed += 1

            elif lesson.teacher_changed or lesson.room_changed or lesson.subject_changed:
                out.changed += 1

            for teacher in lesson.teachers or []:
                teacher_is_absent[teacher] &= not lesson.takes_place

        out.absent_teachers = sum(teacher_is_absent.values())

        return out

    def serialize(self) -> dict:
        return dataclasses.asdict(self)
