import dataclasses
from collections import defaultdict

from . import models


@dataclasses.dataclass
class LessonsStatistics:
    count: int = 0

    changed: int = 0

    cancelled: int = 0
    just_changed: int = 0

    just_changed_changed_subject: int = 0
    just_changed_changed_teacher: int = 0
    just_changed_changed_room: int = 0

    just_changed_no_teacher: int = 0
    just_changed_no_subject: int = 0
    just_changed_no_room: int = 0

    absent_teachers: int = 0

    @classmethod
    def from_lessons(cls, lessons: models.Lessons):
        out = LessonsStatistics()

        teacher_is_present = defaultdict(lambda: False)

        for lesson in lessons:
            if lesson.is_internal:
                continue

            for teacher in lesson.teachers or []:
                teacher_is_present[teacher] |= lesson.takes_place

            if lesson._is_scheduled:
                continue

            out.count += 1

            out.changed += (
                not lesson.takes_place
                or lesson.teacher_changed
                or lesson.room_changed
                or lesson.subject_changed
            )

            out.just_changed += (
                lesson.teacher_changed
                or lesson.room_changed
                or lesson.subject_changed
            )

            if not lesson.takes_place:
                out.cancelled += 1
            else:
                out.just_changed_changed_subject += lesson.subject_changed
                out.just_changed_changed_teacher += lesson.teacher_changed
                out.just_changed_changed_room += lesson.room_changed

                out.just_changed_no_teacher += not lesson.teachers
                out.just_changed_no_subject += lesson.course is None
                out.just_changed_no_room += not lesson.rooms

        out.absent_teachers = len(teacher_is_present) - sum(teacher_is_present.values())

        return out

    def serialize(self) -> dict:
        return dataclasses.asdict(self)
