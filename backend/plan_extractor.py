from __future__ import annotations

import datetime
import logging
import typing
from collections import defaultdict
from xml.etree import ElementTree as ET

from stundenplan24_py import indiware_mobil, substitution_plan

from . import lesson_info, default_plan, blocks
from .lesson_info import process_additional_info
from .teacher import Teacher, Teachers
from .models import Lesson, Lessons, Plan
from .vplan_utils import parse_absent_element, ParsedForm, week_to_letter


class PlanExtractor:
    _logger: logging.Logger
    plan: Plan
    teachers: Teachers
    block_config: blocks.BlockConfiguration

    def fill_in_lesson_times(self):
        forms: dict[str, indiware_mobil.Form] = {form.short_name: form for form in self.plan.indiware_plan.forms}

        for lesson in self.plan.lessons:
            if not lesson.forms:
                continue

            try:
                lesson_form = forms[list(lesson._origin_plan_value)[0]]
            except KeyError:
                self._logger.warning(f" -> Lesson has unknown form: {lesson.forms!r}")
                continue

            if lesson.begin is None:
                lesson.begin = lesson_form.periods.get(sorted(lesson.periods)[0], (None, None))[0]

            if lesson.end is None:
                lesson.end = lesson_form.periods.get(sorted(lesson.periods)[-1], (None, None))[1]

    def used_rooms_by_period(self) -> dict[int, set[str]]:
        out: dict[int, set[str]] = defaultdict(set)

        for lesson in self.plan.lessons:
            assert len(lesson.periods) == 1
            if not lesson.takes_place or not lesson.rooms:
                continue
            out[list(lesson.periods)[0]].update(lesson.rooms)

        return out

    def free_rooms_by_period(self, all_rooms: set[str]) -> dict[int, set[str]]:
        return {
            period: all_rooms - used_rooms
            for period, used_rooms in self.used_rooms_by_period().items()
        }

    def rooms_by_block(self, free_or_used_rooms_by_period: dict[int, set[str]]) -> dict[int, set[str]]:
        out: dict[int, set[str]] = {}

        for period, rooms in free_or_used_rooms_by_period.items():
            block = self.block_config.get_block_of_period(period)

            if block not in out:
                out[block] = set(rooms)
            else:
                out[block].intersection_update(rooms)

        return out

    def info_data(self, parsed_forms: list[ParsedForm]) -> dict[str, typing.Any]:
        return {
            "additional_info": self.plan.additional_info,
            "processed_additional_info": [
                [i.serialize() for i in line]
                for line in process_additional_info(
                    self.plan.additional_info, parsed_forms,
                    self.teachers,
                    self.plan.indiware_plan.date
                )
            ],
            "timestamp": self.plan.indiware_plan.timestamp.isoformat() if self.plan.indiware_plan.timestamp else None,
            "week": week_to_letter(self.plan.indiware_plan.week),
            "week_number": self.plan.indiware_plan.week,
        }


class StudentsPlanExtractor(PlanExtractor):
    def __init__(self, plan_kl: str, vplan_kl: str | None, teachers: Teachers, block_config: blocks.BlockConfiguration,
                 *, logger: logging.Logger):
        self._logger = logger
        self.teachers = teachers
        self.block_config = block_config

        form_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ET.fromstring(plan_kl))
        self.plan = Plan.from_form_plan(form_plan)

        self._extract_teachers()

        if vplan_kl is None:
            self.substitution_plan = None
        else:
            self.substitution_plan = substitution_plan.SubstitutionPlan.from_xml(ET.fromstring(vplan_kl))
            self.add_lessons_for_unavailable_from_subst_plan()

        self.fill_in_lesson_times()

        self.form_plan_extractor = SubPlanExtractor(
            forms_plan=self.plan,
            plan_type="forms",
            teachers=self.teachers,
            block_config=self.block_config,
            logger=self._logger
        )
        self.room_plan_extractor = SubPlanExtractor(
            forms_plan=self.plan,
            plan_type="rooms",
            teachers=self.teachers,
            block_config=self.block_config,
            logger=self._logger
        )
        self.teacher_plan_extractor = SubPlanExtractor(
            forms_plan=self.plan,
            plan_type="teachers",
            teachers=self.teachers,
            block_config=self.block_config,
            logger=self._logger
        )

    def _extract_teachers(self):
        all_classes = self.plan.get_all_classes()

        for lesson in self.plan.lessons:
            self.teachers.add_teachers(
                *lesson_info.extract_teachers(lesson, all_classes, logger=self._logger)
            )

    def add_lessons_for_unavailable_from_subst_plan(self):
        for teacher_str in self.substitution_plan.absent_teachers:
            teacher_name, periods = parse_absent_element(teacher_str)

            try:
                teacher_abbreviation = self.teachers.query_plan_teacher(teacher_name).plan_short
            except LookupError:
                self._logger.warning(f" --> Unknown teacher: {teacher_name!r}.")
                continue

            for period in periods or range(1, 11):
                info = f"{teacher_name}{' den ganzen Tag' if not periods else ''} abwesend laut Vertretungsplan"
                lesson = Lesson.create_internal(self.plan.indiware_plan.date)
                lesson.periods = {period}
                lesson.teachers = {teacher_abbreviation}
                lesson.info = info
                lesson.parsed_info = lesson_info.create_literal_parsed_info(info)
                self.plan.lessons.lessons.append(lesson)

        for room_str in self.substitution_plan.absent_rooms:
            room, periods = parse_absent_element(room_str)

            for period in periods or range(1, 11):
                info = f"Raum {room}{' den ganzen Tag' if not periods else ''} nicht verfügbar laut Vertretungsplan"
                lesson = Lesson.create_internal(self.plan.indiware_plan.date)
                lesson.periods = {period}
                lesson.rooms = {room_str}
                lesson.course = "Belegt"
                lesson.info = info
                lesson.parsed_info = lesson_info.create_literal_parsed_info(info)
                self.plan.lessons.lessons.append(lesson)

        for form_str in self.substitution_plan.absent_forms:
            form, periods = parse_absent_element(form_str)

            for period in periods or range(1, 11):
                info = f"Klasse {form}{' den ganzen Tag' if not periods else ''} abwesend laut Vertretungsplan"
                lesson = Lesson.create_internal(self.plan.indiware_plan.date)
                lesson.periods = {period}
                lesson.forms = {form}
                lesson.info = info
                lesson.parsed_info = lesson_info.create_literal_parsed_info(info)

                self.plan.lessons.lessons.append(lesson)

    def default_plan(self) -> default_plan.DefaultPlanInfo:
        return default_plan.DefaultPlanInfo.from_lessons(self.plan.lessons, self.plan.indiware_plan.week)


class SubPlanExtractor:
    def __init__(self, forms_plan: Plan, plan_type: typing.Literal["forms", "rooms", "teachers"],
                 teachers: Teachers, block_config: blocks.BlockConfiguration, *, logger: logging.Logger):
        self._logger = logger
        self.plan_type = plan_type
        self.forms_lessons_grouped = (
            forms_plan.lessons
            .filter_plan_type_messages(plan_type)
            .group_blocks_and_lesson_info(origin_plan_type="forms", block_config=block_config)
        )

        if self.plan_type in ("teachers", ):
            self.forms_lessons_grouped = self.forms_lessons_grouped.filter(lambda l: not l.is_internal)

        for lesson in self.forms_lessons_grouped:
            lesson.parsed_info.resolve_teachers(teachers)

        self.extrapolate_lesson_times(self.forms_lessons_grouped)

    @staticmethod
    def extrapolate_lesson_times(lessons: Lessons):
        # very sketchy
        for lesson in lessons:
            if lesson.begin is None:
                # can't do anything about that
                continue

            if lesson.end is None:
                prev_block = [
                    l for l in lessons
                    if (sorted(lesson.periods)[0] - sorted(l.periods)[-1] == 1
                        and len(l.periods) == len(lesson.periods)
                        and l.end is not None is not l.begin)
                ]

                if prev_block:
                    block_duration = (
                        datetime.datetime.combine(datetime.datetime.min, prev_block[-1].end)
                        - datetime.datetime.combine(datetime.datetime.min, prev_block[-1].begin)
                    )
                    lesson.end = (
                        datetime.datetime.combine(datetime.datetime.min, lesson.begin) + block_duration
                    ).time()

    def plan(self):
        return self.forms_lessons_grouped.make_plan(self.plan_type, plan_type=self.plan_type)

    def grouped_form_plans(self) -> dict[str, dict[str, list]]:
        return {
            "forms": self.forms_lessons_grouped.make_plan("_grouped_form_plan_current_forms",
                                                          "_grouped_form_plan_scheduled_forms", plan_type="forms"),
            "rooms": self.forms_lessons_grouped.make_plan("_grouped_form_plan_current_rooms",
                                                          "_grouped_form_plan_scheduled_rooms", plan_type="forms"),
            "teachers": self.forms_lessons_grouped.make_plan("_grouped_form_plan_current_teachers",
                                                             "_grouped_form_plan_scheduled_teachers", plan_type="forms")
        }


class TeachersPlanExtractor:
    def __init__(self, plan_le: str, plan_ra: str | None, teachers: Teachers, block_config: blocks.BlockConfiguration,
                 *, logger: logging.Logger):
        self._logger = logger

        teacher_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ET.fromstring(plan_le))
        self.teacher_plan_extractor = PlanExtractor()
        self.teacher_plan_extractor.plan = Plan.from_teacher_plan(teacher_plan)
        self.teacher_plan_extractor.teachers = teachers
        self.teacher_plan_extractor.block_config = block_config
        self.teacher_plan_extractor._logger = logger
        self.teacher_plan_extractor.fill_in_lesson_times()

        if plan_ra is not None:
            room_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ET.fromstring(plan_ra))
            self.room_plan_extractor = PlanExtractor()
            self.room_plan_extractor.plan = Plan.from_room_plan(room_plan)
            self.room_plan_extractor.teachers = teachers
            self.room_plan_extractor.block_config = block_config
            self.room_plan_extractor._logger = logger
            self.room_plan_extractor.fill_in_lesson_times()

    def teacher_plan(self):
        lessons_grouped = self.teacher_plan_extractor.plan.lessons.group_blocks_and_lesson_info(
            origin_plan_type="teachers", block_config=self.teacher_plan_extractor.block_config
        )
        SubPlanExtractor.extrapolate_lesson_times(lessons_grouped)
        return lessons_grouped.make_plan("teachers", plan_type="teachers")

    def room_plan(self):
        if not hasattr(self, "room_plan_extractor"):
            return {}
        else:
            lessons_grouped = self.room_plan_extractor.plan.lessons.group_blocks_and_lesson_info(
                origin_plan_type="rooms", block_config=self.room_plan_extractor.block_config
            )
            SubPlanExtractor.extrapolate_lesson_times(lessons_grouped)
            return lessons_grouped.make_plan("rooms", plan_type="rooms")
