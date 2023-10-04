from __future__ import annotations

import copy
import dataclasses
import datetime
import typing
from collections import defaultdict

import stundenplan24_py
from stundenplan24_py import indiware_mobil

from .lesson_info import ParsedLessonInfo, LessonInfoParagraph, LessonInfoMessage
from . import vplan_utils, lesson_info


@dataclasses.dataclass
class Lesson:
    periods: set[int]
    begin: datetime.time | None
    end: datetime.time | None

    forms: set[str]
    teachers: set[str] | None
    rooms: set[str] | None
    course: str | None  # class group if available else subject

    parsed_info: ParsedLessonInfo

    # taken directly from plan xml
    class_: ClassData | None

    subject_changed: bool
    teacher_changed: bool
    room_changed: bool
    forms_changed: bool

    takes_place: bool | None = None  # whether this lesson in its current form takes place

    is_internal: bool = False
    _lesson_date: datetime.date = None

    _origin_plan_type: typing.Literal["forms", "teachers", "rooms"] = None
    _origin_plan_lesson_id: int = None
    _is_scheduled: bool | None = None
    _grouped_form_plan_current_course: str = None
    _grouped_form_plan_current_teachers: set[str] = None
    _grouped_form_plan_current_rooms: set[str] = None
    _grouped_form_plan_current_forms: set[str] = None
    _grouped_form_plan_scheduled_course: str = None
    _grouped_form_plan_scheduled_teachers: set[str] = None
    _grouped_form_plan_scheduled_rooms: set[str] = None
    _grouped_form_plan_scheduled_forms: set[str] = None

    @property
    def _origin_plan_value(self) -> set[str]:
        return getattr(self, self._origin_plan_type)

    @property
    def class_opt(self):
        if self.class_ is None:
            # noinspection PyTypeChecker
            return ClassData(None, None, None, None)
        else:
            return self.class_

    @classmethod
    def create_internal(cls, date: datetime.date, plan_type: typing.Literal["forms", "teachers", "rooms"] = "forms"):
        return cls(
            periods=set(),
            forms=set(),
            teachers=None,
            rooms=None,
            course=None,
            parsed_info=ParsedLessonInfo([]),
            class_=None,
            subject_changed=False,
            teacher_changed=False,
            room_changed=False,
            forms_changed=False,
            begin=None,
            end=None,
            takes_place=True,
            is_internal=True,
            _lesson_date=date,
            _origin_plan_type=plan_type,
        )

    def serialize(self) -> dict:
        assert len(self.parsed_info.paragraphs) == 0
        return {
            "periods": sorted(self.periods),
            "begin": self.begin.strftime("%H:%M") if self.begin else None,
            "end": self.end.strftime("%H:%M") if self.end else None,
            "forms": sorted(self.forms),
            "teachers": sorted(self.teachers) if self.teachers is not None else None,
            "rooms": sorted(self.rooms) if self.rooms is not None else None,
            "course": self.course,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "forms_changed": self.forms_changed,
            "takes_place": self.takes_place,
            "is_internal": self.is_internal,
            "_origin_plan_lesson_id": self._origin_plan_lesson_id,
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            periods=set(data["periods"]),
            begin=datetime.datetime.strptime(data["begin"], "%H:%M").time() if data["begin"] else None,
            end=datetime.datetime.strptime(data["end"], "%H:%M").time() if data["end"] else None,
            forms=set(data["forms"]) if data["forms"] is not None else None,
            teachers=set(data["teachers"]) if data["teachers"] is not None else None,
            rooms=set(data["rooms"]) if data["rooms"] is not None else None,
            course=data["course"],
            parsed_info=ParsedLessonInfo([]),
            class_=None,
            subject_changed=data["subject_changed"],
            teacher_changed=data["teacher_changed"],
            room_changed=data["room_changed"],
            forms_changed=data["forms_changed"],
            takes_place=data["takes_place"],
            is_internal=data["is_internal"],
            _origin_plan_lesson_id=data["_origin_plan_lesson_id"],
        )


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
    is_unplanned: bool  # True iff lesson is inserted

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
            "is_unplanned": self.is_unplanned,
            "info": self.parsed_info.serialize(self._lesson_date),
            "begin": self.begin.strftime("%H:%M") if self.begin else None,
            "takes_place": self.takes_place,
            "end": self.end.strftime("%H:%M") if self.end else None,
        }

    @classmethod
    def create(cls, taking_place_lesson: Lesson | None, not_taking_place_lesson: Lesson | None,
               plan_type: typing.Literal["forms", "teachers", "rooms"],
               plan_value: set[str]) -> PlanLesson:
        assert not (taking_place_lesson is None is not_taking_place_lesson)

        if taking_place_lesson is None:
            _current_lesson = Lesson(
                periods=not_taking_place_lesson.periods,
                begin=not_taking_place_lesson.begin,
                end=not_taking_place_lesson.end,
                forms=set(),
                teachers=set(),
                rooms=set(),
                course=None,
                parsed_info=None,
                class_=None,
                subject_changed=True,
                teacher_changed=True,
                room_changed=True,
                forms_changed=True,
                takes_place=False,
                _lesson_date=not_taking_place_lesson._lesson_date,
                _origin_plan_type=not_taking_place_lesson._origin_plan_type,
            )
        else:
            _current_lesson = taking_place_lesson

        if not_taking_place_lesson is None:
            _scheduled_lesson = Lesson(
                periods=taking_place_lesson.periods,
                begin=taking_place_lesson.begin,
                end=taking_place_lesson.end,
                forms=set(),
                teachers=set(),
                rooms=set(),
                course=None,
                parsed_info=None,
                class_=None,
                subject_changed=False,
                teacher_changed=False,
                room_changed=False,
                forms_changed=False,
                takes_place=False,
                _lesson_date=taking_place_lesson._lesson_date,
                _origin_plan_type=taking_place_lesson._origin_plan_type,
            )
        else:
            _scheduled_lesson = not_taking_place_lesson

        paragraphs = []

        other_info_value_type = (
            lesson_info.AbstractParsedLessonInfoMessageWithCourseInfo.get_other_info_type_of_plan_type(plan_type)
        )

        # add lesson info
        if _current_lesson._origin_plan_type != plan_type:
            scheduled_other_info_value = getattr(_scheduled_lesson, other_info_value_type)

            if (
                not _current_lesson.takes_place
                and scheduled_other_info_value is not None
                and not (_scheduled_lesson.course is None is _current_lesson.course)
            ):
                paragraphs.append(
                    LessonInfoParagraph([LessonInfoMessage(lesson_info.Cancelled(
                        course=_scheduled_lesson.course or _current_lesson.course,
                        plan_type=plan_type,
                        plan_value=plan_value,
                        other_info_value=scheduled_other_info_value,
                        periods=_scheduled_lesson.periods,
                    ), -1), ], -1)
                )

            current_other_info_value = getattr(_current_lesson, other_info_value_type)
            other_info_value_changed = {
                "forms": True,
                "teachers": _current_lesson.teacher_changed,
                "rooms": _current_lesson.room_changed,
            }[other_info_value_type]
            if (
                _scheduled_lesson.course is not None is not _current_lesson.course and
                _scheduled_lesson.teachers is not None is not _current_lesson.teachers and
                # either course or relevant other info value is different
                ((_current_lesson.course != _scheduled_lesson.course and _current_lesson.subject_changed) or
                 (current_other_info_value != scheduled_other_info_value and other_info_value_changed))
            ):
                paragraphs.append(
                    LessonInfoParagraph([LessonInfoMessage(lesson_info.InsteadOfCourse(
                        course=_scheduled_lesson.course,
                        plan_type=plan_type,
                        plan_value=plan_value,
                        other_info_value=scheduled_other_info_value,
                        periods=_scheduled_lesson.periods,
                    ), -1), ], -1)
                )

        plan_lesson = PlanLesson(
            periods=set(_current_lesson.periods),
            begin=_current_lesson.begin,
            end=_current_lesson.end,
            scheduled_forms=_scheduled_lesson.forms,
            scheduled_teachers=_scheduled_lesson.teachers,
            scheduled_rooms=_scheduled_lesson.rooms,
            scheduled_course=_scheduled_lesson.course,
            current_forms=_current_lesson.forms,
            current_teachers=_current_lesson.teachers,
            current_rooms=_current_lesson.rooms,
            current_course=_current_lesson.course,
            class_number=_current_lesson.class_opt.number or _scheduled_lesson.class_opt.number,
            subject_changed=(
                _current_lesson.subject_changed
                if _current_lesson._origin_plan_type == plan_type
                else (_current_lesson.course != _scheduled_lesson.course)
            ),
            teacher_changed=_current_lesson.teacher_changed,
            room_changed=_current_lesson.room_changed,
            forms_changed=(_current_lesson.forms != _scheduled_lesson.forms) if _scheduled_lesson is not None else True,
            parsed_info=(_current_lesson.parsed_info or _scheduled_lesson.parsed_info) + ParsedLessonInfo(paragraphs),
            takes_place=_current_lesson.takes_place,
            is_internal=_current_lesson.is_internal,
            is_unplanned=_current_lesson.takes_place and not_taking_place_lesson is None,  # TODO
            _lesson_date=_current_lesson._lesson_date
        )

        return plan_lesson


@dataclasses.dataclass
class Lessons:
    lessons: list[Lesson]

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

        return {attribute: Lessons(sorted(lessons, key=lambda x: list(x.periods)[0]))
                for attribute, lessons in grouped.items()}

    @staticmethod
    def _to_plan_lessons(lessons: list[Lesson], plan_type: typing.Literal["forms", "teachers", "rooms"],
                         plan_value: set[str]) -> list[PlanLesson]:
        # select all lessons that take place
        # first, pair them with not taking place lessons by _origin_plan_lesson_id (assert <= one per TPL)
        # then pair scheduled lessons by looking at *_changed attrs
        #
        # remaining not-taking place lessons:
        #   group by ~~_origin_plan_lesson_id/class_opt.number/~~ (course,teachers,forms,rooms)
        #   if only one:
        #       select all taking place lessons that have no not TPLs
        #           if only one:
        #   render as cancelled
        out = []

        not_taking_place_lessons = [lesson for lesson in lessons if not lesson.takes_place]

        lessons.sort(key=lambda l: (
            l.subject_changed,
            l.room_changed,
            l.teacher_changed,
            l.forms_changed,
            not l.takes_place,
            l.course if l.course else "",
        ))

        for taking_place_lesson in lessons:
            if not taking_place_lesson.takes_place:
                continue

            for not_taking_place_lesson in not_taking_place_lessons:
                if taking_place_lesson._origin_plan_lesson_id == not_taking_place_lesson._origin_plan_lesson_id:
                    out.append(
                        PlanLesson.create(taking_place_lesson, not_taking_place_lesson, plan_type, plan_value)
                    )
                    not_taking_place_lessons.remove(not_taking_place_lesson)
                    break
            else:
                for not_taking_place_lesson in not_taking_place_lessons:
                    # @formatter:off
                    is_match = (
                        (taking_place_lesson.course != not_taking_place_lesson.course) in ((True, False) if taking_place_lesson._origin_plan_type != plan_type and taking_place_lesson.subject_changed else (taking_place_lesson.subject_changed,))
                        and (True if taking_place_lesson._origin_plan_type != plan_type and taking_place_lesson.teacher_changed else (not taking_place_lesson.teachers.issuperset(not_taking_place_lesson.teachers or set())) == taking_place_lesson.teacher_changed)
                        and (True if taking_place_lesson._origin_plan_type != plan_type and taking_place_lesson.room_changed else (not taking_place_lesson.rooms.issuperset(not_taking_place_lesson.rooms or set())) == taking_place_lesson.room_changed)
                        and (True if taking_place_lesson._origin_plan_type != plan_type and taking_place_lesson.forms_changed else (not taking_place_lesson.forms.issuperset(not_taking_place_lesson.forms or set())) == taking_place_lesson.forms_changed)
                    )
                    # @formatter:on

                    if is_match:
                        out.append(
                            PlanLesson.create(taking_place_lesson, not_taking_place_lesson, plan_type, plan_value)
                        )
                        not_taking_place_lessons.remove(not_taking_place_lesson)
                        break
                else:
                    if len(not_taking_place_lessons) == 1:
                        out.append(
                            PlanLesson.create(taking_place_lesson, not_taking_place_lessons[0], plan_type, plan_value)
                        )
                        not_taking_place_lessons.pop()
                    else:
                        out.append(
                            PlanLesson.create(taking_place_lesson, None, plan_type, plan_value)
                        )

        for not_taking_place_lesson in not_taking_place_lessons:
            out.append(
                PlanLesson.create(None, not_taking_place_lesson, plan_type, plan_value)
            )

        return out

    def to_plan_lessons(self, plan_type: typing.Literal["forms", "teachers", "rooms"], plan_value: set[str]
                        ) -> list[PlanLesson]:

        lessons_by_periods: dict[frozenset[int], list[Lesson]] = defaultdict(list)
        for lesson in self:
            lessons_by_periods[frozenset(lesson.periods)].append(lesson)

        out: list[PlanLesson] = []

        for periods, lessons in lessons_by_periods.items():
            out += self._to_plan_lessons(lessons, plan_type, plan_value)

        return out

    def make_plan(self, *group_attrs: str, plan_type: typing.Literal["forms", "teachers", "rooms"]
                  ) -> dict[str, list[PlanLesson]]:
        grouped_lessons = self.group_by(*group_attrs)

        return {
            group: sorted(lessons.to_plan_lessons(plan_type, {group}), key=lambda l: (min(l.periods), -len(l.periods)))
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
                if isinstance(parsed1, (lesson_info.MovedFrom, lesson_info.MovedTo)):
                    parsed2: lesson_info.MovedFrom | lesson_info.MovedTo

                    if parsed1.is_groupable(parsed2):
                        new_message = copy.deepcopy(message1)
                        # noinspection PyTypeHints
                        new_message.parsed: lesson_info.MovedFrom | lesson_info.MovedTo
                        new_message.parsed.periods |= parsed2.periods
                        new_message.parsed.original_messages += parsed2.original_messages
                        new_message.parsed.plan_value |= parsed2.plan_value
                        new_paragraph.append(new_message)
                    else:
                        return None

                # periods not groupable, so, to group, info string must be the same
                # TODO: Refactor this, ParsedLessonInfo.original_messages is not reliable/a set
                elif message1.parsed.original_messages == message2.parsed.original_messages:
                    new_paragraph.append(message1)

                else:
                    return None

            new_info.append(LessonInfoParagraph(new_paragraph, paragraph1.index))

        out = ParsedLessonInfo(new_info)
        out.sort_original()
        return out

    def group_blocks_and_lesson_info(self, origin_plan_type: typing.Literal["forms", "teachers", "rooms"]) -> Lessons:
        assert all(len(x.periods) <= 1 for x in self.lessons), \
            "Lessons must be ungrouped. (Must only have one period.)"

        if origin_plan_type == "forms":
            sort_key = lambda x: (
                x.takes_place,
                x.course or x.class_opt.group or "",
                tuple(x.rooms or set()),
                tuple(x.teachers or set()),
                x.parsed_info.lesson_group_sort_key(),

                tuple(x.forms or set()),
                tuple(x.periods or set()),
            )
        elif origin_plan_type == "teachers":
            sort_key = lambda x: (
                x.takes_place,
                x.course or "",
                tuple(x.rooms or set()),
                tuple(x.forms or set()),
                x.parsed_info.lesson_group_sort_key(),

                tuple(x.teachers or set()),
                tuple(x.periods or set()),
            )
        elif origin_plan_type == "rooms":
            sort_key = lambda x: (
                x.takes_place,
                x.course or "",
                tuple(x.teachers or set()),
                tuple(x.forms or set()),
                x.parsed_info.lesson_group_sort_key(),

                tuple(x.rooms or set()),
                x.periods or set(),
            )
        else:
            raise NotImplementedError

        sorted_lessons = sorted(self.lessons, key=sort_key)

        grouped: list[Lesson] = []

        for lesson in sorted_lessons:
            assert lesson._origin_plan_type == origin_plan_type

            for previous_lesson in grouped[-1:-4:-1]:
                can_get_grouped = (
                    lesson.course == previous_lesson.course
                    and lesson.takes_place == previous_lesson.takes_place
                )

                for remaining_plan_value in {"forms", "teachers", "rooms"} - {origin_plan_type}:
                    can_get_grouped &= (
                        getattr(lesson, remaining_plan_value) == getattr(previous_lesson, remaining_plan_value)
                    )

                grouped_additional_info = self._group_lesson_info(lesson.parsed_info, previous_lesson.parsed_info)

                can_get_grouped &= grouped_additional_info is not None

                # block must be the same
                previous_lesson_block = (next(iter(previous_lesson.periods)) + 1) // 2
                current_lesson_block = (next(iter(lesson.periods)) + 1) // 2
                can_get_grouped &= previous_lesson_block == current_lesson_block

                if can_get_grouped:
                    if origin_plan_type == "forms":
                        previous_lesson.forms |= lesson.forms
                    elif origin_plan_type == "teachers":
                        previous_lesson.teachers |= lesson.teachers
                    elif origin_plan_type == "rooms":
                        previous_lesson.rooms |= lesson.rooms
                    else:
                        raise NotImplementedError
                    previous_lesson.parsed_info = grouped_additional_info
                    previous_lesson.periods |= lesson.periods
                    previous_lesson.begin = min(filter(lambda x: x, (previous_lesson.begin, lesson.begin)),
                                                default=None)
                    previous_lesson.end = max(filter(lambda x: x, (previous_lesson.end, lesson.end)), default=None)
                    previous_lesson._is_scheduled = (
                        None if previous_lesson._is_scheduled != lesson._is_scheduled else previous_lesson._is_scheduled
                    )
                    break
            else:
                grouped.append(copy.deepcopy(lesson))

        return Lessons(sorted(grouped, key=lambda x: x.periods))

    def filter(self, function: typing.Callable[[Lesson], bool]) -> Lessons:
        return Lessons(list(filter(function, self.lessons)))

    def filter_plan_type_messages(self, plan_type: typing.Literal["forms", "rooms", "teachers"]) -> Lessons:
        return Lessons([
            dataclasses.replace(lesson, parsed_info=lesson.parsed_info.filter_messages(
                lambda m: m.parsed.plan_type is None or m.parsed.plan_type == plan_type
            )) for lesson in self.lessons
        ])

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
        _id = 0
        for form in form_plan.forms:
            for lesson in form.lessons:
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
                    rooms={r for r in lesson.room().split(" ") if r} if lesson.room() else set(),
                    course=lesson.subject(),

                    # see below
                    parsed_info=None,

                    class_=class_data,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=lesson.teacher.was_changed,
                    room_changed=lesson.room.was_changed,
                    forms_changed=False,
                    _lesson_date=form_plan.date
                )
                current_lesson._is_scheduled = False
                current_lesson.parsed_info = ParsedLessonInfo.from_str(
                    lesson.information, current_lesson, "forms"
                ) if lesson.information is not None else ParsedLessonInfo([])

                for paragraph in current_lesson.parsed_info.paragraphs:
                    for moved_to_message in paragraph.messages:
                        if isinstance(moved_to_message.parsed, (lesson_info.MovedTo, lesson_info.MovedFrom)):
                            # if lessons are moved, class data no longer represents the scheduled lesson
                            class_data = None
                            current_lesson.class_ = None

                scheduled_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms={form.short_name},
                    teachers=(
                        (current_lesson.teachers if not current_lesson.teacher_changed else None)
                        or ({class_data.teacher} if class_data is not None else None)
                    ),
                    rooms=current_lesson.rooms if not current_lesson.room_changed else None,
                    course=(
                        lesson.course2
                        or (current_lesson.course if not current_lesson.subject_changed else None)
                        or (class_data.group if class_data is not None else None)
                        or (class_data.subject if class_data is not None else None)
                    ),
                    parsed_info=current_lesson.parsed_info,

                    class_=class_data,
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    forms_changed=False,
                    takes_place=False,
                    _lesson_date=form_plan.date,
                )
                scheduled_lesson._is_scheduled = True

                if current_lesson.course == "---" and current_lesson.subject_changed:
                    # Indiware Stundenplaner's way of telling us that the lesson is cancelled
                    current_lesson.course = scheduled_lesson.course
                    current_lesson.teachers = scheduled_lesson.teachers
                    current_lesson.rooms = scheduled_lesson.rooms
                    current_lesson.subject_changed = False
                    current_lesson.teacher_changed = False
                    current_lesson.room_changed = False

                    current_lesson.takes_place = False
                else:
                    current_lesson.takes_place = True

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

                    l._origin_plan_type = "forms"
                    l._origin_plan_lesson_id = _id

                lessons.append(scheduled_lesson)
                lessons.append(current_lesson)

                _id += 1

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

    @classmethod
    def from_teacher_plan(cls, teacher_plan: indiware_mobil.IndiwareMobilPlan) -> Plan:
        lessons: list[Lesson] = []
        _id = 0
        for teacher in teacher_plan.forms:
            for lesson in teacher.lessons:
                current_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms=set(lesson.teacher().split(",")) if lesson.teacher() else set(),
                    teachers={teacher.short_name},
                    # TODO: Some schools use rooms with spaces
                    rooms={r for r in lesson.room().split(" ") if r} if lesson.room() else set(),
                    course=lesson.subject(),

                    # see below
                    parsed_info=None,

                    class_=None,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=False,
                    room_changed=lesson.room.was_changed,
                    forms_changed=lesson.teacher.was_changed,
                    _lesson_date=teacher_plan.date
                )
                current_lesson._is_scheduled = False
                current_lesson.parsed_info = ParsedLessonInfo.from_str(
                    lesson.information, current_lesson, "teachers"
                ) if lesson.information is not None else ParsedLessonInfo([])

                scheduled_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms=current_lesson.forms if not current_lesson.forms_changed else None,
                    teachers=current_lesson.teachers,
                    rooms=current_lesson.rooms if not current_lesson.room_changed else None,
                    course=(
                        lesson.course2
                        or (current_lesson.course if not current_lesson.subject_changed else None)
                    ),
                    parsed_info=current_lesson.parsed_info,

                    class_=None,
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    forms_changed=False,
                    takes_place=False,
                    _lesson_date=teacher_plan.date,
                )
                scheduled_lesson._is_scheduled = True

                if current_lesson.course == "---" and current_lesson.subject_changed:
                    # Indiware Stundenplaner's way of telling us that the lesson is cancelled
                    current_lesson.course = scheduled_lesson.course
                    current_lesson.forms = scheduled_lesson.forms
                    current_lesson.rooms = scheduled_lesson.rooms
                    current_lesson.subject_changed = False
                    current_lesson.forms_changed = False
                    current_lesson.room_changed = False

                    current_lesson.takes_place = False
                else:
                    current_lesson.takes_place = True

                for l in current_lesson, scheduled_lesson:
                    l._origin_plan_type = "teachers"
                    l._origin_plan_lesson_id = _id

                lessons.append(scheduled_lesson)
                lessons.append(current_lesson)

                _id += 1

            for break_supervision in teacher.break_supervisions:
                # TODO
                pass

        return cls(
            lessons=Lessons(lessons),
            additional_info=teacher_plan.additional_info,

            indiware_plan=teacher_plan,
            exams={}
        )

    @classmethod
    def from_room_plan(cls, room_plan: indiware_mobil.IndiwareMobilPlan) -> Plan:
        lessons: list[Lesson] = []
        _id = 0
        for room in room_plan.forms:
            for lesson in room.lessons:
                current_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms=set(lesson.room().split(",")) if lesson.room() else set(),
                    teachers=set(lesson.teacher().split()) if lesson.teacher() else set(),
                    rooms={room.short_name},
                    course=lesson.subject(),

                    # see below
                    parsed_info=None,

                    class_=None,
                    subject_changed=lesson.subject.was_changed,
                    teacher_changed=lesson.teacher.was_changed,
                    room_changed=False,
                    forms_changed=lesson.room.was_changed,
                    _lesson_date=room_plan.date
                )
                current_lesson._is_scheduled = False
                current_lesson.parsed_info = ParsedLessonInfo.from_str(
                    lesson.information, current_lesson, "rooms"
                ) if lesson.information is not None else ParsedLessonInfo([])

                scheduled_lesson = Lesson(
                    periods={lesson.period} if lesson.period is not None else set(),
                    begin=lesson.start,
                    end=lesson.end,

                    forms=current_lesson.forms if not current_lesson.forms_changed else None,
                    teachers=current_lesson.teachers if not current_lesson.teacher_changed else None,
                    rooms=current_lesson.rooms,
                    course=(
                        lesson.course2
                        or (current_lesson.course if not current_lesson.subject_changed else None)
                    ),
                    parsed_info=current_lesson.parsed_info,

                    class_=None,
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    forms_changed=False,
                    takes_place=False,
                    _lesson_date=room_plan.date,
                )
                scheduled_lesson._is_scheduled = True

                if current_lesson.course == "---" and current_lesson.subject_changed:
                    # Indiware Stundenplaner's way of telling us that the lesson is cancelled
                    current_lesson.course = scheduled_lesson.course
                    current_lesson.forms = scheduled_lesson.forms
                    current_lesson.teachers = scheduled_lesson.teachers
                    current_lesson.subject_changed = False
                    current_lesson.forms_changed = False
                    current_lesson.teacher_changed = False

                    current_lesson.takes_place = False
                else:
                    current_lesson.takes_place = True

                for l in current_lesson, scheduled_lesson:
                    l._origin_plan_type = "rooms"
                    l._origin_plan_lesson_id = _id

                lessons.append(scheduled_lesson)
                lessons.append(current_lesson)

                _id += 1

        return cls(
            lessons=Lessons(lessons),
            additional_info=room_plan.additional_info,

            indiware_plan=room_plan,
            exams={}
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
