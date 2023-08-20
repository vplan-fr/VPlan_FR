from __future__ import annotations

import datetime
import json
import logging

from . import schools
from .cache import Cache
from .plan_extractor import PlanExtractor
from .meta_extractor import MetaExtractor
from .models import Teachers, Lessons, Exam, DefaultTimesInfo, Teacher
from .vplan_utils import group_forms


class PlanProcessor:
    VERSION = "34"

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
        if not self.cache.plan_file_exists(day, timestamp, ".complete"):
            self._logger.info(f"=> Skipping plan for {day!s} because it was not completed yet. ({timestamp!s}).")
            return False

        if self.cache.plan_file_exists(day, timestamp, ".processed"):
            if (cur_ver := self.cache.get_plan_file(day, timestamp, ".processed")) == self.VERSION:
                return False

            self._logger.info(f"=> Migrating plan for {day!s} to current version... ({cur_ver!r} -> {self.VERSION!r})")
        else:
            self._logger.info(f"=> Processing plan for {day!s}...")

        self.compute_plans(day, timestamp)

        return True

    def compute_plans(self, date: datetime.date, timestamp: datetime.datetime):
        try:
            plan_kl = self.cache.get_plan_file(date, timestamp, "PlanKl.xml")
        except FileNotFoundError:
            self._logger.warning(f"=> Could not find Indiware form plan for date {date!s} and timestamp {timestamp!s}.")
        else:
            try:
                vplan_kl = self.cache.get_plan_file(date, timestamp, "VPlanKl.xml")
            except FileNotFoundError:
                vplan_kl = None
            plan_extractor = PlanExtractor(plan_kl, vplan_kl, self.teachers.abbreviation_by_surname(),
                                           logger=self._logger)

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
                json.dumps(plan_extractor.plan.exams, default=Exam.serialize),
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

            self.cache.update_newest(date)

        self.cache.store_plan_file(date, timestamp, str(self.VERSION), ".processed")

    def update_meta(self):
        self._logger.info("* Updating meta data...")

        if not self.meta_extractor.is_available():
            self._logger.info("=> No plans cached yet.")
            return

        data = {
            "free_days": [date.isoformat() for date in self.meta_extractor.free_days()]
        }
        self.cache.store_meta_file(json.dumps(data), "meta.json")
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

    def update_all(self):
        self.update_meta()
        self.migrate_all()
