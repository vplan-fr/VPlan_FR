from __future__ import annotations

import datetime
import logging
import typing
from collections import defaultdict
from xml.etree import ElementTree as ET

from stundenplan24_py import indiware_mobil

from .cache import Cache
from .models import DefaultTimesInfo
from .teacher import Teacher


class DailyMetaExtractor:
    """Extracts meta information for a single day's plan."""

    def __init__(self, plankl_file: str):
        self.form_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ET.fromstring(plankl_file))

    def teachers(self) -> list[Teacher]:
        excluded_subjects = ["KL", "AnSt", "FÖ", "WB", "GTA", "EU4"]

        out = []
        for form in self.form_plan.forms:
            for lesson in form.lessons:
                for teacher in (lesson.teacher() or "").split():
                    if not teacher:
                        continue
                    out.append(Teacher(plan_short=teacher, last_seen=self.form_plan.date))

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
            for form in self.form_plan.forms
            for lesson in form.lessons if lesson.room()
            for room in lesson.room().split()
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
    def __init__(self, cache: Cache, num_last_days: int = 10, *, logger: logging.Logger):
        self._logger = logger

        self.cache = cache
        self.num_last_days = num_last_days

        self._rooms: set[str] | None = None
        self._daily_extractors: dict[tuple[datetime.date, datetime.datetime], DailyMetaExtractor] = {}

    def iterate_daily_extractors(self) -> typing.Generator[DailyMetaExtractor, None, None]:
        for day in self.cache.get_days()[:self.num_last_days]:
            for timestamp in self.cache.get_timestamps(day):
                if (day, timestamp) in self._daily_extractors:
                    yield self._daily_extractors[(day, timestamp)]
                else:
                    try:
                        plan_kl = self.cache.get_plan_file(day, timestamp, "PlanKl.xml")
                    except FileNotFoundError:
                        continue

                    extractor = DailyMetaExtractor(plan_kl)
                    self._daily_extractors[(day, timestamp)] = extractor
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

    def courses_data(self) -> dict[str, list[str]]:
        for extractor in self.iterate_daily_extractors():
            return {
                form: extractor.courses(form)
                for form in self.forms()
            }

        return {}

    def free_days(self) -> list[datetime.date]:
        for extractor in self.iterate_daily_extractors():
            return extractor.free_days()

        return []

    def forms_data(self):
        default_times = self.default_times()
        courses = self.courses_data()

        return {
            form: {
                "default_times": default_times[form].to_dict() if form in default_times else None,
                "class_groups": courses[form],
            }
            for form in courses.keys()
        }

    def invalidate_cache(self):
        self._rooms = None
