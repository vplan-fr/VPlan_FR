from __future__ import annotations

import datetime
import logging
import typing
from collections import defaultdict
from xml.etree import ElementTree as ET

from stundenplan24_py import indiware_mobil, substitution_plan

from . import lesson_info
from .models import Plan, Lesson, Teacher, Teachers
from .vplan_utils import parse_absent_element


class PlanExtractor:
    def __init__(self, plan_kl: str, vplan_kl: str | None, teacher_abbreviation_by_surname: dict[str, str], *,
                 logger: logging.Logger):
        self._logger = logger

        form_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ET.fromstring(plan_kl))
        self.plan = Plan.from_form_plan(form_plan)

        self.extracted_teachers = self._extract_teachers()

        teacher_abbreviation_by_surname = (
                teacher_abbreviation_by_surname.copy()
                | Teachers(list(self.extracted_teachers.values())).abbreviation_by_surname()
        )

        if vplan_kl is None:
            self.substitution_plan = None
        else:
            self.substitution_plan = substitution_plan.SubstitutionPlan.from_xml(ET.fromstring(vplan_kl))
            self.add_lessons_for_unavailable_from_subst_plan(teacher_abbreviation_by_surname)

        self.fill_in_lesson_times()

        self.lessons_grouped = self.plan.lessons.blocks_grouped()

        self.extrapolate_lesson_times()

        self.resolve_teachers_in_lesson_info(teacher_abbreviation_by_surname)

    def fill_in_lesson_times(self):
        forms: dict[str, indiware_mobil.Form] = {form.short_name: form for form in self.plan.form_plan.forms}

        for lesson in self.plan.lessons:
            if not lesson.scheduled_forms:
                continue

            try:
                lesson_form = forms[list(lesson.scheduled_forms)[0]]
            except KeyError:
                self._logger.warning(f" -> Lesson has unknown form: {lesson.scheduled_forms!r}")
                continue

            if lesson.begin is None:
                lesson.begin = lesson_form.periods.get(sorted(lesson.periods)[0], (None, None))[0]

            if lesson.end is None:
                lesson.end = lesson_form.periods.get(sorted(lesson.periods)[-1], (None, None))[1]

    def extrapolate_lesson_times(self):
        # very sketchy
        for lesson in self.lessons_grouped:
            if lesson.begin is None:
                # can't do anything about that
                continue

            if lesson.end is None:
                prev_block = [
                    l for l in self.lessons_grouped
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

                    self._logger.debug(
                        f" -> Extrapolated end time for a lesson. "
                        f"Period: {lesson.periods!r}, subject: {lesson.current_class!r}, "
                        f"form: {lesson.scheduled_forms!r}, duration: {block_duration.seconds / 60:.2f} min."
                    )
                else:
                    pass
                    # self._logger.debug(f" -> Could not extrapolate end time for a lesson, no previous block found.")

    def add_lessons_for_unavailable_from_subst_plan(self, teacher_abbreviation_by_surname: dict[str, str]):
        for teacher_str in self.substitution_plan.absent_teachers:
            teacher_name, periods = parse_absent_element(teacher_str)

            try:
                teacher_abbreviation = teacher_abbreviation_by_surname[teacher_name]
            except KeyError:
                self._logger.warning(f"Could not resolve teacher abbreviation for {teacher_name!r}.")
                if " " not in teacher_name:
                    teacher_abbreviation = teacher_name
                else:
                    continue

            for period in periods or range(1, 11):
                info = f"{teacher_name}{' den ganzen Tag' if not periods else ''} abwesend laut Vertretungsplan"
                lesson = Lesson.create_internal()
                lesson.periods = {period}
                lesson.current_teachers = {teacher_abbreviation}
                lesson.info = info
                lesson.parsed_info = lesson_info.create_literal_parsed_info(info)
                self.plan.lessons.lessons.append(lesson)

        for room_str in self.substitution_plan.absent_rooms:
            room, periods = parse_absent_element(room_str)

            for period in periods or range(1, 11):
                info = f"Raum {room}{' den ganzen Tag' if not periods else ''} nicht verfügbar laut Vertretungsplan"
                lesson = Lesson.create_internal()
                lesson.periods = {period}
                lesson.current_rooms = {room_str}
                lesson.current_class = "Belegt"
                lesson.info = info
                lesson.parsed_info = lesson_info.create_literal_parsed_info(info)
                self.plan.lessons.lessons.append(lesson)

        for form_str in self.substitution_plan.absent_forms:
            form, periods = parse_absent_element(form_str)

            for period in periods or range(1, 11):
                info = f"Klasse {form}{' den ganzen Tag' if not periods else ''} abwesend laut Vertretungsplan"
                lesson = Lesson.create_internal()
                lesson.periods = {period}
                lesson.current_forms = {form}
                lesson.info = info
                lesson.parsed_info = lesson_info.create_literal_parsed_info(info)

                self.plan.lessons.lessons.append(lesson)

    def room_plan(self):
        return self.lessons_grouped.make_plan(("current_rooms", "scheduled_rooms"), "rooms")

    def teacher_plan(self):
        return self.lessons_grouped.filter(lambda l: not l.is_internal).make_plan(
            ("class_teachers", "scheduled_teachers", "current_teachers"), "teachers"
        )

    def form_plan(self):
        return self.lessons_grouped.filter(lambda l: not l.is_internal).make_plan(
            ("current_forms", "scheduled_forms"), "forms"
        )

    def used_rooms_by_period(self) -> dict[int, set[str]]:
        out: dict[int, set[str]] = defaultdict(set)

        for lesson in self.plan.lessons:
            assert len(lesson.periods) == 1
            out[list(lesson.periods)[0]].update(lesson.current_rooms)

        return out

    def free_rooms_by_period(self, all_rooms: set[str]) -> dict[int, set[str]]:
        return {
            period: all_rooms - used_rooms
            for period, used_rooms in self.used_rooms_by_period().items()
        }

    def free_rooms_by_block(self, all_rooms: set[str]) -> dict[int, set[str]]:
        out: dict[int, set[str]] = {}

        for period, free_rooms in self.free_rooms_by_period(all_rooms).items():
            block = (period + 1) // 2

            if block not in out:
                out[block] = set(free_rooms)
            else:
                out[block].intersection_update(free_rooms)

        return out

    def info_data(self) -> dict[str, typing.Any]:
        return {
            "additional_info": self.plan.additional_info,
            "timestamp": self.plan.form_plan.timestamp.isoformat(),
            "week": self.plan.week_letter()
        }

    def _extract_teachers(self) -> dict[str, Teacher]:
        all_classes = self.plan.get_all_classes()
        out: dict[str, Teacher] = {}

        for lesson in self.plan.lessons:
            out |= lesson_info.extract_teachers(lesson, all_classes, logger=self._logger)

        return out

    def resolve_teachers_in_lesson_info(self, teacher_abbreviation_by_surname: dict[str, str]):
        for lesson in self.lessons_grouped:
            lesson.parsed_info.resolve_teachers(teacher_abbreviation_by_surname)