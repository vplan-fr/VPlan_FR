from __future__ import annotations

import copy
import dataclasses
import datetime
import logging
import typing

from . import models, lesson_info


@dataclasses.dataclass
class DefaultPlanInfo:
    unchanged_lessons: list[models.Lesson] = dataclasses.field(default_factory=list)
    week: int | None = None

    @classmethod
    def from_lessons(cls, lessons: typing.Iterable[models.Lesson], week: int | None) -> DefaultPlanInfo:
        out = cls(week=week)

        for lesson in lessons:
            if not lesson._is_scheduled or lesson.is_internal or lesson.takes_place:
                # we only want scheduled, not taking place lessons
                continue

            lesson = copy.deepcopy(lesson)

            lesson.parsed_info = lesson_info.ParsedLessonInfo([])

            if lesson.teacher_changed:
                lesson.teachers = None

            if lesson.room_changed:
                lesson.rooms = None

            if lesson.forms_changed:
                lesson.forms = None
                assert False, f"{cls.__name__}.from_lessons() only supports lessons from form plans."

            out.unchanged_lessons.append(lesson)

        return out

    @classmethod
    def merge(cls, info: DefaultPlanInfo, other_info: DefaultPlanInfo) -> DefaultPlanInfo | None:
        assert info.week == other_info.week

        grouped_info = models.Lessons(info.unchanged_lessons).group_by(("forms", "periods"))
        grouped_other_info = models.Lessons(other_info.unchanged_lessons).group_by(("forms", "periods"))

        all_categories = set(grouped_info.keys()) | set(grouped_other_info.keys())

        all_lessons = []
        for category in all_categories:
            info_lessons = grouped_info.get(category, models.Lessons())
            other_info_lessons = grouped_other_info.get(category, models.Lessons())

            _any_lesson = next(iter(info_lessons + other_info_lessons))
            times = _any_lesson.begin, _any_lesson.end
            if any((l.begin, l.end) != times for l in info_lessons + other_info_lessons):
                logging.debug(f"DefaultPlanInfo.merge(): Times of lessons in category {category} don't match.")
                return None

            if len(info_lessons) == 0 or len(other_info_lessons) == 0:
                all_lessons += info_lessons
                all_lessons += other_info_lessons
                # if len(other_info_lessons) == 0: breakpoint()
                continue

            info_lessons_by_class_number = info_lessons.group_by_key(lambda l: (l.class_opt.number,))
            other_info_lessons_by_class_number = other_info_lessons.group_by_key(lambda l: (l.class_opt.number,))

            all_class_numbers = (
                set(info_lessons_by_class_number.keys())
                | set(other_info_lessons_by_class_number.keys())
            )

            for class_number in all_class_numbers:
                info_lessons = info_lessons_by_class_number.get(class_number, models.Lessons())
                other_info_lessons = other_info_lessons_by_class_number.get(class_number, models.Lessons())

                if len(info_lessons) == 0 or len(other_info_lessons) == 0:
                    all_lessons += info_lessons
                    all_lessons += other_info_lessons
                    continue

                teachers = set(sum((list(l.teachers) for l in info_lessons if l.teachers is not None), []))
                other_teachers = set(sum((list(l.teachers) for l in other_info_lessons if l.teachers is not None), []))

                rooms = set(sum((list(l.rooms) for l in info_lessons if l.rooms is not None), []))
                other_rooms = set(sum((list(l.rooms) for l in other_info_lessons if l.rooms is not None), []))

                courses = {l.course for l in info_lessons + other_info_lessons if l.course is not None}

                _any_lesson = next(iter(info_lessons + other_info_lessons))
                if (
                    len(other_teachers & teachers) > 0
                    and (len(rooms & other_rooms) > 0 or not rooms or not other_rooms)
                    and len(courses) == 1
                ):
                    all_lessons.append(models.Lesson(
                        periods=_any_lesson.periods,
                        begin=_any_lesson.begin,
                        end=_any_lesson.end,
                        forms=_any_lesson.forms,
                        course=next(iter(courses)),
                        parsed_info=lesson_info.ParsedLessonInfo([]),
                        class_=models.ClassData(None, None, None, class_number),
                        teachers=teachers | other_teachers,
                        rooms=rooms | other_rooms,
                        takes_place=False
                    ))
                else:
                    return None

        return cls(all_lessons, info.week)

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


@dataclasses.dataclass
class DefaultPlanWeek:
    default_plan_info_by_weekday: dict[int, DefaultPlanInfo] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class DefaultPlan:
    week_by_week_number: dict[int, DefaultPlanWeek] = dataclasses.field(default_factory=dict)

    def add_day(self, date: datetime.date, default_plan_info: DefaultPlanInfo) -> bool:
        if default_plan_info.week not in self.week_by_week_number:
            self.week_by_week_number[default_plan_info.week] = DefaultPlanWeek()

        week = self.week_by_week_number[default_plan_info.week]

        if date.weekday() not in week.default_plan_info_by_weekday:
            week.default_plan_info_by_weekday[date.weekday()] = DefaultPlanInfo([], default_plan_info.week)

        merged_info = DefaultPlanInfo.merge(
            week.default_plan_info_by_weekday[date.weekday()],
            default_plan_info
        )

        if merged_info is None:
            return False

        week.default_plan_info_by_weekday[date.weekday()] = merged_info

        return True

    @staticmethod
    def make_plan(lessons: models.Lessons, plan_type: typing.Literal["forms", "teachers", "rooms"]) -> dict:
        """
        Run Lessons.make_plan but first insert a non-scheduled lesson (taking_place=True) for every lesson in lessons.
        """

        lessons.lessons += [dataclasses.replace(lesson, takes_place=True) for lesson in lessons]

        # asserted in group_blocks_and_lesson_info
        lessons.lessons = [dataclasses.replace(l, _origin_plan_type="forms") for l in lessons.lessons]

        return lessons.group_blocks_and_lesson_info("forms").make_plan(plan_type, plan_type=plan_type)

    def export(self):
        return {
            week_number: {
                week_day: {
                    plan_type: self.make_plan(models.Lessons(default_plan_info.unchanged_lessons), plan_type)
                    for plan_type in ("forms", "teachers", "rooms")
                }
                for week_day, default_plan_info in week.default_plan_info_by_weekday.items()
            }
            for week_number, week in self.week_by_week_number.items()
        }
