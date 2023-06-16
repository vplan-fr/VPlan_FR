# coding=utf-8
from __future__ import annotations

import asyncio
import datetime
import logging
import typing
from collections import defaultdict
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from stundenplan24_py import Stundenplan24Client, Stundenplan24Credentials, indiware_mobil, NoPlanForDateError

from .cache import Cache
from .vplan_utils import group_forms
from .models import Lesson, Plan, Teacher, DefaultTimesInfo, Exam
from . import schools


class PlanCrawler:
    """Check for new indiware plans in regular intervals and cache them along with their extracted and parsed
    (meta)data."""

    VERSION = "20"

    def __init__(self, client: Stundenplan24Client, cache: Cache):
        self.client = client
        self.cache = cache
        self.meta_extractor = MetaExtractor(self.cache)

        self._logger = logging.getLogger(f"{self.__class__.__name__}-{client.school_number}")

    async def update_fetch(self):
        self._logger.debug("=> Checking for new plans...")
        plan_files = await self.client.fetch_dates_indiware_mobil()  # requests vpdir.php

        await self.update(plan_files)

    async def update(self, downloadable_plan_files: dict[str, datetime.datetime], no_meta_update: bool = False) -> bool:
        needs_meta_update = False

        for filename, timestamp in downloadable_plan_files.items():
            if filename == "Klassen.xml":
                # this is always the latest day planned
                continue

            date = datetime.datetime.strptime(filename, "PlanKl%Y%m%d.xml").date()

            # check if plan is already cached
            if not self.cache.contains(date, timestamp, "PlanKl.xml"):
                self._logger.info(f" -> Downloading plan for {date}...")

                plan = await self.client.fetch_indiware_mobil(filename)
                try:
                    vplan = await self.client.fetch_substitution_plan(date)
                    self.cache.store_plan_file(date, timestamp, vplan, "VPlanKl.xml")
                except NoPlanForDateError:
                    self._logger.debug(f"   -> No substitution plan available.")

                self.cache.store_plan_file(date, timestamp, plan, "PlanKl.xml")
            else:
                plan = None

            needs_meta_update |= self.update_plans(date, timestamp, plan)

        if needs_meta_update and not no_meta_update:
            self.update_meta()

            self._logger.info("...Done.")
            return True
        else:
            self._logger.debug("...Done.")
            return False

    def migrate_all(self):
        self._logger.info("=> Migrating cache...")

        for day in self.cache.get_days():
            self.cache.update_newest(day)

            for revision in self.cache.get_timestamps(day):
                self.update_plans(day, revision)

    def update_plans(self, day: datetime.date, revision: datetime.datetime, plan: str | None = None) -> bool:
        if self.cache.contains(day, revision, ".processed"):
            if self.cache.get_plan_file(day, revision, ".processed") == self.VERSION:
                return False

            self._logger.info(f" * Migrating plan for {day} to current version...")
        else:
            self._logger.info(f" * Processing plan for {day}...")

        plan = self.cache.get_plan_file(day, revision, "PlanKl.xml") if plan is None else plan
        self.compute_plans(day, revision, plan)

        return True

    async def check_infinite(self, interval: int = 30):
        self.update_meta()
        self.migrate_all()

        while True:
            await self.update_fetch()

            await asyncio.sleep(interval)

    def update_meta(self):
        self._logger.info("=> Updating meta data...")

        data = {
            "free_days": [date.isoformat() for date in self.meta_extractor.free_days()]
        }
        self.cache.store_meta_file(json.dumps(data, default=DefaultTimesInfo.to_dict), "meta.json")
        self.cache.store_meta_file(json.dumps(self.meta_extractor.dates_data()), "dates.json")

        self.update_teachers()
        self.update_forms()
        self.update_rooms()

    def compute_plans(self, date: datetime.date, timestamp: datetime.datetime, plan: str) -> None:
        plan_extractor = PlanExtractor(plan)

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps({
                "rooms": plan_extractor.room_plan(),
                "teachers": plan_extractor.teacher_plan(),
                "forms": plan_extractor.form_plan()}, default=Lesson.to_dict),
            "plans.json"
        )

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps(plan_extractor.plan.exams, default=Exam.to_dict),
            "exams.json"
        )

        all_rooms = set(self.meta_extractor.rooms())
        rooms_data = {
            "used_rooms": plan_extractor.used_rooms_by_lesson(),
            "free_rooms": plan_extractor.free_rooms_by_lesson(all_rooms),
            "free_rooms_by_block": plan_extractor.free_rooms_by_block(all_rooms)
        }

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps(rooms_data, default=list),
            "rooms.json"
        )

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps(plan_extractor.info_data()),
            "info.json"
        )

        self.cache.store_plan_file(date, timestamp, str(self.VERSION), ".processed")

        self.cache.update_newest(date)

    def update_teachers(self):
        try:
            last_update_timestamp = datetime.datetime.fromisoformat(
                json.loads(self.cache.get_meta_file("teachers.json"))["timestamp"]
            )
        except FileNotFoundError:
            last_update_timestamp = datetime.datetime.min

        if datetime.datetime.now() - last_update_timestamp < datetime.timedelta(hours=6):
            self._logger.info("=> Skipping teacher update. Last update was less than 6 hours ago.")
            return

        self._logger.info("=> Updating teachers...")

        if self.client.school_number not in schools.teacher_scrapers:
            self._logger.warning(" * No teacher scraper available for this school.")
            scraped_teachers = {}
        else:
            self._logger.info(" * Scraping teachers...")
            _scraped_teachers = schools.teacher_scrapers[str(self.client.school_number)]()
            scraped_teachers = {teacher.abbreviation: teacher for teacher in _scraped_teachers}

            self._logger.debug(f" -> Found {len(scraped_teachers)} teachers.")

        self._logger.info(" * Merging with extracted data...")

        _extracted_teachers = self.meta_extractor.teachers()
        extracted_teachers = {teacher.abbreviation: teacher for teacher in _extracted_teachers}

        all_abbreviations = set(extracted_teachers.keys()) | set(scraped_teachers.keys())

        merged_teachers = {}
        for abbreviation in all_abbreviations:
            scraped_teacher = scraped_teachers.get(abbreviation, Teacher(abbreviation))
            extracted_teacher = extracted_teachers.get(abbreviation, Teacher(abbreviation))

            merged_teachers[abbreviation] = Teacher.merge(
                scraped_teacher, extracted_teacher
            )

        teachers_data = {
            "teachers": merged_teachers,
            "timestamp": datetime.datetime.now().isoformat()
        }

        self.cache.store_meta_file(
            json.dumps(teachers_data, default=Teacher.to_dict),
            "teachers.json"
        )

    def update_forms(self):
        self._logger.info("=> Updating forms...")

        data = {
            "grouped_forms": group_forms(self.meta_extractor.forms()),
            "forms": self.meta_extractor.forms_data()
        }

        self.cache.store_meta_file(
            json.dumps(data),
            "forms.json"
        )

    def update_rooms(self):
        self._logger.info("=> Updating rooms...")

        all_rooms = self.meta_extractor.rooms()
        parsed_rooms: dict[str, dict] = {}
        try:
            room_parser = schools.room_parsers[str(self.client.school_number)]

            for room in all_rooms:
                try:
                    parsed_rooms[room] = room_parser(room).to_dict()
                except Exception as e:
                    self._logger.error(f" -> Error while parsing room {room!r}: {e}")

        except KeyError:
            self._logger.warning(" * No room parser available for this school.")

            parsed_rooms = {room: None for room in all_rooms}

        data = {
            room: parsed_rooms.get(room) for room in all_rooms
        }

        self.cache.store_meta_file(
            json.dumps(data),
            "rooms.json"
        )


class DailyMetaExtractor:
    """Extracts meta information for a single day's plan."""

    def __init__(self, plankl_file: str):
        self.form_plan = indiware_mobil.FormPlan.from_xml(ET.fromstring(plankl_file))

    def teachers(self) -> dict[str, list[str]]:
        excluded_subjects = ["KL", "AnSt", "FÖ", "WB", "GTA"]

        all_teachers = set()
        for form in self.form_plan.forms:
            for lesson in form.lessons:
                if lesson.teacher():
                    all_teachers.add(lesson.teacher())

        teachers = defaultdict(list, {teacher: [] for teacher in all_teachers})
        for form in self.form_plan.forms:
            for class_ in form.classes.values():
                if class_.teacher and class_.subject not in excluded_subjects:
                    teachers[class_.teacher].append(class_.subject)

        return teachers

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
    # TODO: implement memory cache of rooms, teachers, etc.

    def __init__(self, cache: Cache, num_last_days: int = 10):
        self.cache = cache
        self.num_last_days = num_last_days

    def iterate_daily_extractors(self) -> typing.Generator[DailyMetaExtractor, None, None]:
        for day in self.cache.get_days()[:self.num_last_days]:
            for timestamp in self.cache.get_timestamps(day):
                yield DailyMetaExtractor(self.cache.get_plan_file(day, timestamp, "PlanKl.xml"))

    def rooms(self):
        rooms: set[str] = set()

        for extractor in self.iterate_daily_extractors():
            rooms.update(extractor.rooms())

        return sorted(rooms)

    def teachers(self) -> list[Teacher]:
        teachers: dict[str, list[str]] = defaultdict(list)

        for extractor in self.iterate_daily_extractors():
            for teacher, subjects in extractor.teachers().items():
                teachers[teacher].extend(subjects)

        for teacher, subjects in teachers.items():
            teachers[teacher] = sorted(set(subjects))

        return [
            Teacher(abbreviation, None, None, None, subjects=subjects)
            for abbreviation, subjects in teachers.items()
        ]

    def forms(self) -> list[str]:
        forms: set[str] = set()

        for extractor in self.iterate_daily_extractors():
            forms.update(extractor.forms())

        return sorted(forms)

    def default_times(self) -> dict[str, DefaultTimesInfo]:
        for extractor in self.iterate_daily_extractors():
            default_times = extractor.default_times()
            if default_times:
                return default_times

        return {}

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

    def free_days(self) -> list[datetime.date]:
        for extractor in self.iterate_daily_extractors():
            return extractor.free_days()

    def forms_data(self):
        default_times = self.default_times()
        courses = self.courses_data()

        return {
            form: {
                "default_times": default_times[form].to_dict(),
                "class_groups": courses[form],
            }
            for form in courses.keys()
        }


class PlanExtractor:
    def __init__(self, plan_kl: str):
        self._logger = logging.getLogger(self.__class__.__name__)

        form_plan = indiware_mobil.FormPlan.from_xml(ET.fromstring(plan_kl))
        self.plan = Plan.from_form_plan(form_plan)
        self.lessons_grouped = self.plan.lessons.blocks_grouped()

        # extrapolate lesson times (sketchy)
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
                        f"Period: {lesson.periods!r}, subject: {lesson.current_subject!r}, form: {lesson.forms!r}, "
                        f"duration: {block_duration.seconds/60:.2f} min."
                    )
                else:
                    pass
                    # self._logger.debug(f" -> Could not extrapolate end time for a lesson, no previous block found.")

    def room_plan(self):
        return self.lessons_grouped.group_by("rooms")

    def teacher_plan(self):
        return self.lessons_grouped.group_by("class_teacher", "current_teacher")

    def form_plan(self):
        return self.lessons_grouped.group_by("forms")

    # def next_day(self, forward=True):
    #     year, month, day = int(self.date[:4]), int(self.date[4:6]), int(self.date[6:])
    #     d = datetime(year, month, day)
    #     delta = 1 if forward else -1
    #     d += timedelta(days=delta)
    #     while d.strftime("%Y%m%d") in self.freie_tage or d.weekday() > 4:
    #         d += timedelta(days=delta)
    #     return d.strftime("%Y%m%d")

    def used_rooms_by_lesson(self) -> dict[int, set[str]]:
        out: dict[int, set[str]] = defaultdict(set)

        for lesson in self.plan.lessons:
            assert len(lesson.periods) == 1
            out[list(lesson.periods)[0]].update(lesson.rooms)

        return out

    def free_rooms_by_lesson(self, all_rooms: set[str]) -> dict[int, set[str]]:
        return {
            period: list(all_rooms - used_rooms)
            for period, used_rooms in self.used_rooms_by_lesson().items()
        }

    def free_rooms_by_block(self, all_rooms: set[str]) -> dict[int, set[str]]:
        out: dict[int, set[str]] = {}

        for period, free_rooms in self.free_rooms_by_lesson(all_rooms).items():
            block = period // 2

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


async def get_clients() -> dict[str, PlanCrawler]:
    logging.basicConfig(level=logging.DEBUG)

    # parse credentials
    with open("creds.json", "r", encoding="utf-8") as f:
        _creds = json.load(f)

    clients = {}

    for school_number, creds_data in _creds.items():
        creds = Stundenplan24Credentials(
            creds_data["username"],
            creds_data["password"]
        )

        # create client
        client = Stundenplan24Client(
            school_number=creds_data["school_number"],
            credentials=creds,
            base_url=creds_data["api_server"]
        )

        cache = Cache(Path(f".cache/{school_number}").absolute())

        # create crawler
        p = PlanCrawler(client, cache)

        clients |= {school_number: p}

    return clients


async def main():
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)8s] %(name)s: %(message)s")

    clients = await get_clients()

    await asyncio.gather(
        *[client.check_infinite() for client in clients.values()]
    )


if __name__ == "__main__":
    asyncio.run(main())
