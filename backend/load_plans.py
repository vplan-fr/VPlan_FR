# coding=utf-8
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import typing
from collections import defaultdict
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from stundenplan24_py import IndiwareStundenplanerClient, indiware_mobil, NoPlanForDateError, \
    substitution_plan, Hosting, IndiwareMobilClient, SubstitutionPlanClient, UnauthorizedError, PlanClientError

from .cache import Cache
from .vplan_utils import group_forms, parse_absent_element
from .models import Lesson, Plan, Teachers, DefaultTimesInfo, Exam, Teacher, Lessons
from . import schools
from . import lesson_info


class PlanDownloader:
    """Check for new indiware plans in regular intervals store them in cache."""

    def __init__(self, client: IndiwareStundenplanerClient, cache: Cache, *, logger: logging.Logger):
        self._logger = logger

        self.client = client
        self.cache = cache

    async def check_infinite(self, interval: int = 60):
        while True:
            await self.update_fetch()

            await asyncio.sleep(interval)

    async def update_fetch(self) -> set[tuple[datetime.date, datetime.datetime]]:
        self._logger.debug("* Checking for new plans...")

        new = set()

        # not using asyncio.gather because the logs would be confusing
        for indiware_client in self.client.indiware_mobil_clients:
            new |= await self.fetch_indiware_mobil(indiware_client)

        new |= await self.fetch_substitution_plans()

        return new

    async def fetch_indiware_mobil(
            self,
            indiware_client: IndiwareMobilClient
    ) -> set[tuple[datetime.date, datetime.datetime]]:
        try:
            plan_files = await indiware_client.fetch_dates()
        except PlanClientError as e:
            if e.args[1] in (404, 401):
                self._logger.debug(f"-> Insufficient credentials (or invalid URL) to fetch Indiware Mobil endpoint "
                                   f"{indiware_client.endpoint.url!r}")
                return set()
            else:
                raise
        else:
            return await self.download_indiware_mobil(indiware_client, plan_files)

    async def download_indiware_mobil(
            self,
            client: IndiwareMobilClient,
            downloadable_plan_files: dict[str, datetime.datetime]
    ) -> set[tuple[datetime.date, datetime.datetime]]:
        new: set[tuple[datetime.date, datetime.datetime]] = set()

        for filename, real_timestamp in downloadable_plan_files.items():
            if "Plan" not in filename:
                # this is always the latest day planned
                continue

            date = datetime.datetime.strptime(filename[6:], "%Y%m%d.xml").date()
            cache_filename = filename[:6] + ".xml"

            assert cache_filename in {"PlanKl.xml", "PlanRa.xml", "PlanLe.xml"}, f"Invalid filename {cache_filename!r}"

            try:
                timestamp = self.find_corresponding_existing_timestamp(date, real_timestamp)
                self._logger.debug(
                    f" -> Coerced timestamp {real_timestamp.isoformat()} to {timestamp.isoformat()} on date "
                    f"{date.isoformat()}."
                )

            except RuntimeError:
                timestamp = real_timestamp

            if not self.cache.contains(date, timestamp, cache_filename):
                self._logger.info(f" -> Downloading indiware {filename!r}... (date: {date!r})")

                plan = await client.fetch_plan(filename)

                self.cache.store_plan_file(date, timestamp, plan, cache_filename)
                new.add((date, timestamp))
            else:
                self._logger.debug(f" -> Skipping indiware {filename!r}... (date: {date.isoformat()})")

        return new

    async def fetch_substitution_plans(self) -> set[tuple[datetime.date, datetime.datetime]]:
        out = set()
        for substitution_plan_client in self.client.substitution_plan_clients:
            out |= await self.fetch_substitution_plan(substitution_plan_client)

        return out

    async def fetch_substitution_plan(
            self,
            plan_client: SubstitutionPlanClient
    ) -> set[tuple[datetime.date, datetime.datetime]]:
        self._logger.info("* Checking for new substitution plans...")

        try:
            base_plan = await plan_client.fetch_plan()
        except NoPlanForDateError:
            self._logger.debug(f"=> No substitution plan available for {plan_client.base_url!r}.")
            return set()
        except UnauthorizedError:
            self._logger.debug(f"=> Insufficient credentials to fetch substitution plan from "
                               f"{plan_client.base_url!r}.")
            return set()
        free_days = set(substitution_plan.SubstitutionPlan.from_xml(ET.fromstring(base_plan)).free_days)
        out = set()

        def is_date_valid(date: datetime.date):
            return date not in free_days and date.weekday() not in (5, 6)

        def valid_date_iterator(start: datetime.date, step: int = 1):
            while True:
                while not is_date_valid(start):
                    start += datetime.timedelta(days=step)

                yield start

                start += datetime.timedelta(days=step)

        for plan_date in valid_date_iterator(datetime.date.today(), step=-1):
            try:
                out |= await self.download_substitution_plan(plan_client, plan_date)
            except NoPlanForDateError:
                self._logger.debug(f"=> Stopping substitution plan download at date {plan_date.isoformat()}.")
                break

        for plan_date in valid_date_iterator(datetime.date.today() + datetime.timedelta(days=1), step=1):
            try:
                out |= await self.download_substitution_plan(plan_client, plan_date)
            except NoPlanForDateError:
                self._logger.debug(f"=> Stopping substitution plan download at date {plan_date.isoformat()}.")
                break

        return out

    def find_corresponding_existing_timestamp(
            self,
            date: datetime.date,
            timestamp: datetime.datetime
    ) -> datetime.datetime:
        timestamp = timestamp + datetime.timedelta(minutes=5)

        for other_timestamp in self.cache.get_timestamps(date):
            if other_timestamp <= timestamp:
                return other_timestamp

            if abs(other_timestamp - timestamp) > datetime.timedelta(minutes=5):
                break

        raise RuntimeError(
            f"Could not find a corresponding existing timestamp. "
            f"Date: {date.isoformat()} Timestamp: {timestamp.isoformat()}."
        )

    async def download_substitution_plan(
            self,
            plan_client: SubstitutionPlanClient,
            date: datetime.date
    ) -> set[tuple[datetime.date, datetime.datetime]]:
        plan_str = await plan_client.fetch_plan(date)
        plan = substitution_plan.SubstitutionPlan.from_xml(ET.fromstring(plan_str))

        timestamp = self.find_corresponding_existing_timestamp(date, plan.timestamp)

        cache_filename = plan.filename[:7] + ".xml"
        assert cache_filename in {"VplanKl.xml", "VplanLe.xml"}, f"Invalid cache filename {cache_filename!r}."

        if self.cache.contains(date, timestamp, cache_filename):
            self._logger.debug(f"=> Substitution plan was already cached with timestamp {timestamp.isoformat()}.")
            return set()
        else:
            self.cache.store_plan_file(date, timestamp, plan_str, cache_filename)
            self._logger.info(f"=> Downloaded substitution plan for date {date.isoformat()}.")
            return {(date, timestamp)}


class PlanProcessor:
    VERSION = "32"

    def __init__(self, cache: Cache, school_number: str, *, logger: logging.Logger):
        self._logger = logger

        self.cache = cache
        self.school_number = school_number
        self.meta_extractor = MetaExtractor(self.cache, logger=self._logger)
        self.teachers = Teachers()

        self.load_teachers()

    def load_teachers(self):
        self._logger.info("* Loading cached teachers...")
        try:
            data = json.loads(self.cache.get_meta_file("teachers.json"))
        except FileNotFoundError:
            self._logger.warning("=> Could not load any cached teachers.")
            return

        self.teachers = Teachers.from_dict(data)

        self._logger.info(f"=> Loaded {len(self.teachers.teachers)} cached teachers.")

    def migrate_all(self):
        self._logger.info("* Migrating cache...")

        for day in self.cache.get_days():
            self.cache.update_newest(day)

            for revision in self.cache.get_timestamps(day):
                self.update_plans(day, revision)

    def update_plans(self, day: datetime.date, timestamp: datetime.datetime) -> bool:
        if self.cache.contains(day, timestamp, ".processed"):
            if self.cache.get_plan_file(day, timestamp, ".processed") == self.VERSION:
                return False

            self._logger.info(f"=> Migrating plan for {day} to current version...")
        else:
            self._logger.info(f"=> Processing plan for {day}...")

        self.compute_plans(day, timestamp)

        return True

    def compute_plans(self, date: datetime.date, timestamp: datetime.datetime) -> None:
        plan_kl = self.cache.get_plan_file(date, timestamp, "PlanKl.xml")
        vplan_kl = self.cache.get_plan_file(date, timestamp, "VPlanKl.xml")
        plan_extractor = PlanExtractor(plan_kl, vplan_kl, self.teachers.abbreviation_by_surname(), logger=self._logger)

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps({
                "rooms": plan_extractor.room_plan(),
                "teachers": plan_extractor.teacher_plan(),
                "forms": plan_extractor.form_plan()
            }, default=Lessons.serialize),
            "plans.json"
        )

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps(plan_extractor.plan.exams, default=Exam.to_dict),
            "exams.json"
        )

        all_rooms = self.meta_extractor.rooms()
        rooms_data = {
            "used_rooms_by_period": plan_extractor.used_rooms_by_period(),
            "free_rooms_by_period": plan_extractor.free_rooms_by_period(all_rooms),
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

    def update_meta(self):
        self._logger.info("* Updating meta data...")

        if not self.cache.get_days():
            self._logger.error("=> No plans cached yet.")
            return

        data = {
            "free_days": [date.isoformat() for date in self.meta_extractor.free_days()]
        }
        self.cache.store_meta_file(json.dumps(data, default=DefaultTimesInfo.to_dict), "meta.json")
        self.cache.store_meta_file(json.dumps(self.meta_extractor.dates_data()), "dates.json")

        self.update_teachers()
        self.update_forms()
        self.update_rooms()

    def update_teachers(self):
        if datetime.datetime.now() - self.teachers.timestamp < datetime.timedelta(hours=6):
            self._logger.info("* Skipping teacher update. Last update was less than 6 hours ago.")
            return

        self._logger.info("* Updating teachers...")

        if self.school_number not in schools.teacher_scrapers:
            self._logger.warning("=> No teacher scraper available for this school.")
            scraped_teachers = {}
        else:
            self._logger.info("=> Scraping teachers...")
            _scraped_teachers = schools.teacher_scrapers[str(self.school_number)]()
            scraped_teachers = {teacher.abbreviation: teacher for teacher in _scraped_teachers}

            self._logger.debug(f" -> Found {len(scraped_teachers)} teachers.")

        self._logger.info("=> Merging with extracted data...")

        _extracted_teachers = self.meta_extractor.teachers()
        extracted_teachers = {teacher.abbreviation: teacher for teacher in _extracted_teachers}

        all_abbreviations = set(extracted_teachers.keys()) | set(scraped_teachers.keys())

        merged_teachers = []
        for abbreviation in all_abbreviations:
            scraped_teacher = scraped_teachers.get(abbreviation, Teacher(abbreviation))
            extracted_teacher = extracted_teachers.get(abbreviation, Teacher(abbreviation))

            merged_teachers.append(
                Teacher.merge(scraped_teacher, extracted_teacher)
            )

        self.teachers = Teachers(
            teachers=merged_teachers,
            timestamp=datetime.datetime.now()
        )

        self.cache.store_meta_file(
            json.dumps(self.teachers.to_dict()),
            "teachers.json"
        )

    def update_forms(self):
        self._logger.info("* Updating forms...")

        data = {
            "grouped_forms": group_forms(self.meta_extractor.forms()),
            "forms": self.meta_extractor.forms_data()
        }

        self.cache.store_meta_file(
            json.dumps(data),
            "forms.json"
        )

    def update_rooms(self):
        self._logger.info("* Updating rooms...")

        all_rooms = self.meta_extractor.rooms()
        parsed_rooms: dict[str, dict] = {}
        try:
            room_parser = schools.room_parsers[str(self.school_number)]

            for room in all_rooms:
                try:
                    parsed_rooms[room] = room_parser(room).to_dict()
                except Exception as e:
                    self._logger.error(f" -> Error while parsing room {room!r}: {e}")

        except KeyError:
            self._logger.debug("=> No room parser available for this school.")

            parsed_rooms = {room: None for room in all_rooms}

        data = {
            room: parsed_rooms.get(room) for room in all_rooms
        }

        self.cache.store_meta_file(
            json.dumps(data),
            "rooms.json"
        )


class PlanCrawler:
    def __init__(self, plan_downloader: PlanDownloader, plan_processor: PlanProcessor):
        self.plan_downloader = plan_downloader
        self.plan_processor = plan_processor

    async def check_infinite(self, interval: int = 60):
        self.plan_processor.update_meta()
        self.plan_processor.update_rooms()
        self.plan_processor.update_teachers()
        self.plan_processor.update_rooms()
        self.plan_processor.migrate_all()

        while True:
            new_timestamps = await self.plan_downloader.update_fetch()

            if new_timestamps:
                self.plan_processor.meta_extractor.invalidate_cache()

            for date, timestamp in new_timestamps:
                self.plan_processor.update_plans(date, timestamp)

            if new_timestamps:
                self.plan_processor.update_meta()
                self.plan_processor.update_rooms()
                self.plan_processor.update_teachers()
                self.plan_processor.update_rooms()

            await asyncio.sleep(interval)


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
                        self._logger.warning(
                            f"Timestamp {timestamp.isoformat()} for day {day.isoformat()} has no PlanKl.xml file."
                        )
                        continue

                    extractor = DailyMetaExtractor(plan_kl)
                    self._daily_extractors[(day, timestamp)] = extractor
                    yield extractor

    def rooms(self) -> set[str]:
        if self._rooms is not None:
            return self._rooms

        rooms: set[str] = set()

        for extractor in self.iterate_daily_extractors():
            rooms.update(extractor.rooms())

        self._rooms = rooms
        return rooms

    def teachers(self) -> list[Teacher]:
        teachers: dict[str, list[str]] = defaultdict(list)

        for extractor in self.iterate_daily_extractors():
            for _teacher, subjects in extractor.teachers().items():
                for teacher in _teacher.split(" "):
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

    def free_days(self) -> list[datetime.date]:
        for extractor in self.iterate_daily_extractors():
            return extractor.free_days()

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


class PlanExtractor:
    def __init__(self, plan_kl: str, vplan_kl: str | None, teacher_abbreviation_by_surname: dict[str, str], *,
                 logger: logging.Logger):
        self._logger = logger

        form_plan = indiware_mobil.FormPlan.from_xml(ET.fromstring(plan_kl))
        self.plan = Plan.from_form_plan(form_plan, teacher_abbreviation_by_surname)

        if vplan_kl is None:
            self.substitution_plan = None
        else:
            self.substitution_plan = substitution_plan.SubstitutionPlan.from_xml(ET.fromstring(vplan_kl))
            self.add_lessons_for_unavailable_from_subst_plan(teacher_abbreviation_by_surname)

        self.fill_in_lesson_times()

        self.lessons_grouped = self.plan.lessons.blocks_grouped()

        self.extrapolate_lesson_times()

    def fill_in_lesson_times(self):
        forms: dict[str, indiware_mobil.Form] = {form.short_name: form for form in self.plan.form_plan.forms}

        for lesson in self.plan.lessons:
            if not lesson.forms:
                continue

            try:
                lesson_form = forms[list(lesson.forms)[0]]
            except KeyError:
                self._logger.warning(f" -> Lesson has unknown form: {lesson.forms!r}")
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
                        f"Period: {lesson.periods!r}, subject: {lesson.current_subject!r}, form: {lesson.forms!r}, "
                        f"duration: {block_duration.seconds / 60:.2f} min."
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
                lesson = Lesson(
                    forms=set(),
                    current_subject=None,
                    current_teachers={teacher_abbreviation},
                    class_subject=None,
                    class_group=None,
                    class_teachers=None,
                    class_number=None,
                    rooms=set(),
                    periods={period},
                    info=info,
                    parsed_info=lesson_info.create_literal_parsed_info(info),
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    begin=None,
                    end=None,
                    is_internal=True
                )
                self.plan.lessons.lessons.append(lesson)

        for room_str in self.substitution_plan.absent_rooms:
            room, periods = parse_absent_element(room_str)

            for period in periods or range(1, 11):
                info = f"Raum {room}{' den ganzen Tag' if not periods else ''} nicht verfügbar laut Vertretungsplan"
                lesson = Lesson(
                    forms=set(),
                    current_subject="Belegt",
                    current_teachers=None,
                    class_subject=None,
                    class_group=None,
                    class_teachers=None,
                    class_number=None,
                    rooms={room},
                    periods={period},
                    info=info,
                    parsed_info=lesson_info.create_literal_parsed_info(info),
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    begin=None,
                    end=None,
                    is_internal=True
                )
                self.plan.lessons.lessons.append(lesson)

        for form_str in self.substitution_plan.absent_forms:
            form, periods = parse_absent_element(form_str)

            for period in periods or range(1, 11):
                info = f"Klasse {form}{' den ganzen Tag' if not periods else ''} abwesend laut Vertretungsplan"
                lesson = Lesson(
                    forms={form},
                    current_subject=None,
                    current_teachers=None,
                    class_subject=None,
                    class_group=None,
                    class_teachers=None,
                    class_number=None,
                    rooms=set(),
                    periods={period},
                    info=info,
                    parsed_info=lesson_info.create_literal_parsed_info(info),
                    subject_changed=False,
                    teacher_changed=False,
                    room_changed=False,
                    begin=None,
                    end=None,
                    is_internal=True
                )
                self.plan.lessons.lessons.append(lesson)

    def room_plan(self):
        return self.lessons_grouped.group_by("rooms")

    def teacher_plan(self):
        return self.lessons_grouped.filter(lambda l: not l.is_internal).group_by("class_teachers", "current_teachers")

    def form_plan(self):
        return self.lessons_grouped.filter(lambda l: not l.is_internal).group_by("forms")

    def used_rooms_by_period(self) -> dict[int, set[str]]:
        out: dict[int, set[str]] = defaultdict(set)

        for lesson in self.plan.lessons:
            assert len(lesson.periods) == 1
            out[list(lesson.periods)[0]].update(lesson.rooms)

        return out

    def free_rooms_by_period(self, all_rooms: set[str]) -> dict[int, set[str]]:
        return {
            period: list(all_rooms - used_rooms)
            for period, used_rooms in self.used_rooms_by_period().items()
        }

    def free_rooms_by_block(self, all_rooms: set[str]) -> dict[int, set[str]]:
        out: dict[int, set[str]] = {}

        for period, free_rooms in self.free_rooms_by_period(all_rooms).items():
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
    # parse credentials
    with open("creds.json", "r", encoding="utf-8") as f:
        _creds = json.load(f)

    clients = {}

    for school_name, data in _creds.items():
        specifier = data['school_number'] if 'school_number' in data else school_name
        logger = logging.getLogger(specifier)
        cache = Cache(Path(f".cache/{specifier}").absolute())

        hosting = Hosting.deserialize(data["hosting"])
        client = IndiwareStundenplanerClient(hosting)

        plan_downloader = PlanDownloader(client, cache, logger=logger)
        plan_processor = PlanProcessor(cache, specifier, logger=logger)

        # create crawler
        p = PlanCrawler(plan_downloader, plan_processor)

        clients |= {school_name: p}

    return clients


async def main():
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--only-download", "--d", action="store_true",
                                 help="Only download the plans, do not parse it.")
    argument_parser.add_argument("-loglevel", "-l", default="INFO",
                                 help="Set the log level.")

    args = argument_parser.parse_args()

    logging.basicConfig(level=args.loglevel, format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    clients = await get_clients()

    if not args.only_download:
        await asyncio.gather(
            *[client.check_infinite() for client in clients.values()]
        )
    else:
        await asyncio.gather(
            *[client.plan_downloader.check_infinite() for client in clients.values()]
        )


if __name__ == "__main__":
    asyncio.run(main())
