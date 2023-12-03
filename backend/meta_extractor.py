from __future__ import annotations

import datetime
import logging
import threading
import typing
from xml.etree import ElementTree as ET

from stundenplan24_py import indiware_mobil

from shared.cache import Cache
from .models import DefaultTimesInfo, Plan
from .teacher import Teacher


class DailyMetaExtractor:
    """Extracts meta information for a single day's plan."""

    def __init__(self, plankl_file: str):
        self.form_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ET.fromstring(plankl_file))
        self.plan = Plan.from_form_plan(self.form_plan)

    def teachers(self) -> list[Teacher]:
        excluded_subjects = ["KL", "AnSt", "FÖ", "WB", "GTA", "EU4"]

        out = []
        for lesson in self.plan.lessons:
            for teacher in lesson.teachers or []:
                out.append(Teacher(plan_short=teacher, last_seen=self.form_plan.date))

        for form in self.form_plan.forms:
            for class_ in form.classes.values():
                subjects = set(s for s in class_.subject.split() if s not in excluded_subjects)

                for teacher in class_.teacher.split():
                    if not teacher:
                        continue

                    out.append(Teacher(plan_short=teacher, subjects=subjects, last_seen=self.form_plan.date))

        return out

    def forms(self) -> list[str]:
        return [form.short_name for form in self.form_plan.forms]

    def rooms(self) -> set[str]:
        return set(
            room
            for lesson in self.plan.lessons
            for room in lesson.rooms or []
        )

    def courses(self, form_name: str) -> dict[str, dict]:
        classes: dict[str, dict] = {}

        for form in self.form_plan.forms:
            if form.short_name != form_name:
                continue

            for class_number, class_ in form.classes.items():
                classes[class_number] = {"teacher": class_.teacher, "subject": class_.subject, "group": class_.group}

        return classes

    def default_times(self) -> dict[str, DefaultTimesInfo]:
        return {
            form.short_name: DefaultTimesInfo({
                int(period): time_data for period, time_data in form.periods.items()
            })

            for form in self.form_plan.forms
        }

    def free_days(self) -> list[datetime.date]:
        return self.form_plan.free_days


class MetaExtractor:
    def __init__(self, cache: Cache, num_last_days: int | None = 10, *, logger: logging.Logger):
        self._logger = logger

        self.cache = cache
        self.num_last_days = num_last_days

        self._rooms: set[str] | None = None
        self._daily_extractors: dict[tuple[datetime.date, datetime.datetime], DailyMetaExtractor] = {}
        self._daily_extractors_lock = threading.Lock()
        self._max_cached_extractors = 10

    def iterate_daily_extractors(self) -> typing.Generator[DailyMetaExtractor, None, None]:
        for day in self.cache.get_days()[:self.num_last_days]:
            for timestamp in self.cache.get_timestamps(day):
                self._logger.log(5, f"Yielding DailyMetaExtractor for {day!s} {timestamp!s}.")
                if (day, timestamp) in self._daily_extractors:
                    yield self._daily_extractors[(day, timestamp)]
                else:
                    try:
                        plan_kl = self.cache.get_plan_file(day, timestamp, "PlanKl.xml")
                    except FileNotFoundError:
                        continue

                    try:
                        extractor = DailyMetaExtractor(plan_kl)
                    except ET.ParseError:
                        self._logger.error(f"Failed to parse PlanKl.xml for {day!s} {timestamp!s}.")
                        continue

                    with self._daily_extractors_lock:
                        self._daily_extractors[(day, timestamp)] = extractor
                        while len(self._daily_extractors) > self._max_cached_extractors:
                            self._daily_extractors.pop(next(iter(self._daily_extractors)))

                    yield extractor

    def is_available(self) -> bool:
        try:
            next(self.iterate_daily_extractors())
            return True
        except StopIteration:
            return False

    def rooms(self) -> set[str]:
        if self._rooms is not None:
            return self._rooms

        rooms: set[str] = set()

        for extractor in self.iterate_daily_extractors():
            rooms.update(extractor.rooms())

        self._rooms = rooms
        return rooms

    def teachers(self) -> list[Teacher]:
        return sum((e.teachers() for e in self.iterate_daily_extractors()), [])

    def forms(self) -> list[str]:
        forms: set[str] = set()

        for extractor in self.iterate_daily_extractors():
            forms.update(extractor.forms())
            # takes wayyy to long to iterate all extractors
            if forms:
                break

        return sorted(forms)

    def default_times(self) -> dict[str, DefaultTimesInfo]:
        all_forms = set(self.forms())
        out = {}

        for extractor in self.iterate_daily_extractors():
            out |= extractor.default_times()

            if set(out.keys()) == all_forms:
                break
        else:
            self._logger.warning(f"No default times info for forms {all_forms - set(out.keys())!r}.")

        return out

    def dates_data(self) -> dict[str, list[str]]:
        # noinspection PyTypeChecker
        return {
            day.isoformat(): list(map(datetime.datetime.isoformat, self.cache.get_timestamps(day)))
            for day in self.cache.get_days(reverse=False)
        }

    def courses_data(self, forms: typing.Iterable[str]) -> dict[str, list[str]]:
        for extractor in self.iterate_daily_extractors():
            return {
                form: extractor.courses(form)
                for form in forms
            }

        return {}

    def free_days(self) -> list[datetime.date]:
        for extractor in self.iterate_daily_extractors():
            return extractor.free_days()

        return []

    def forms_data(self, forms: typing.Iterable[str]):
        default_times = self.default_times()
        courses = self.courses_data(forms)

        return {
            form: {
                "default_times": default_times[form].to_dict() if form in default_times else None,
                "class_groups": courses[form],
            }
            for form in courses.keys()
        }

    def invalidate_cache(self):
        self._rooms = None
