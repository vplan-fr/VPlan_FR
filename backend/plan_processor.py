from __future__ import annotations

import datetime
import json
import logging

from . import schools
from .cache import Cache
from .meta_extractor import MetaExtractor
from .teacher import Teacher, Teachers
from .models import PlanLesson, Exam
from .vplan_utils import group_forms, ParsedForm
from .stats import LessonsStatistics
from .plan_extractor import StudentsPlanExtractor, TeachersPlanExtractor


class PlanProcessor:
    VERSION = "89"

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

        self.teachers = Teachers.deserialize(data)

        self._logger.info(f"=> Loaded {len(self.teachers.teachers)} cached teachers.")

    def migrate_all(self):
        self._logger.info("* Migrating cache...")

        for day in self.cache.get_days():
            self.cache.update_newest(day)

            for revision in self.cache.get_timestamps(day):
                self.update_plans(day, revision)

    def update_plans(self, day: datetime.date, timestamp: datetime.datetime) -> bool:
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
            plan_kl = self.cache.get_plan_file(date, timestamp, "PlanKl.xml", newest_before=True)
        except FileNotFoundError:
            self._logger.warning(f"=> Could not find Indiware form plan for date {date!s} and timestamp {timestamp!s}.")
        else:
            try:
                vplan_kl = self.cache.get_plan_file(date, timestamp, "VplanKl.xml", newest_before=True)
            except FileNotFoundError:
                vplan_kl = None

            students_plan_extractor = StudentsPlanExtractor(
                plan_kl, vplan_kl, self.teachers.abbreviation_by_surname(), logger=self._logger
            )

            self.cache.store_plan_file(
                date, timestamp,
                json.dumps({
                    "forms": (form_plan := students_plan_extractor.form_plan_extractor.plan()),
                    "teachers": students_plan_extractor.teacher_plan_extractor.plan(),
                    "rooms": (room_plan := students_plan_extractor.room_plan_extractor.plan()),
                }, default=PlanLesson.serialize),
                "plans.json"
            )
            self.cache.store_plan_file(
                date, timestamp,
                json.dumps(students_plan_extractor.form_plan_extractor.grouped_form_plans(),
                           default=PlanLesson.serialize),
                "grouped_form_plans.json"
            )

            # from .models import Lessons
            # self.cache.store_plan_file(
            #     date, timestamp,
            #     json.dumps({
            #         "rooms": students_plan_extractor.room_plan_extractor.forms_lessons_grouped.group_by("rooms"),
            #         "teachers": students_plan_extractor.teacher_plan_extractor.forms_lessons_grouped.group_by("teachers"),
            #         "forms": students_plan_extractor.form_plan_extractor.forms_lessons_grouped.group_by("forms")
            #     }, default=Lessons.serialize),
            #     "_plans_raw.json"
            # )

            self.cache.store_plan_file(
                date, timestamp,
                json.dumps({
                    "all_lessons": LessonsStatistics.from_lessons(students_plan_extractor.plan.lessons).serialize()
                }),
                "statistics.json"
            )

            self.cache.store_plan_file(
                date, timestamp,
                json.dumps(students_plan_extractor.plan.exams, default=Exam.serialize),
                "exams.json"
            )

            all_rooms = self.meta_extractor.rooms()
            rooms_data = {
                "used_rooms_by_period": (used_rooms := students_plan_extractor.used_rooms_by_period()),
                "free_rooms_by_period": (free_rooms := students_plan_extractor.free_rooms_by_period(all_rooms)),
                "used_rooms_by_block": students_plan_extractor.rooms_by_block(used_rooms),
                "free_rooms_by_block": students_plan_extractor.rooms_by_block(free_rooms)
            }

            self.cache.store_plan_file(
                date, timestamp,
                json.dumps(rooms_data, default=list),
                "rooms.json"
            )

            all_forms = self.meta_extractor.forms()
            all_forms_parsed = [ParsedForm.from_str(f) for f in all_forms]
            students_plan_extractor.teacher_abbreviation_by_surname |= (
                {-i: t.abbreviation for i, t in enumerate(self.meta_extractor.teachers())} |
                self.teachers.abbreviation_by_surname()
            )
            self.cache.store_plan_file(
                date, timestamp,
                json.dumps(students_plan_extractor.info_data(all_forms_parsed)),
                "info.json"
            )

            try:
                plan_le = self.cache.get_plan_file(date, timestamp, "PlanLe.xml", newest_before=True)
            except FileNotFoundError:
                pass
            else:
                try:
                    plan_ra = self.cache.get_plan_file(date, timestamp, "PlanRa.xml", newest_before=True)
                except FileNotFoundError:
                    plan_ra = None

                teachers_plan_extractor = TeachersPlanExtractor(
                    plan_le, plan_ra, self.teachers.abbreviation_by_surname(), logger=self._logger
                )

                teachers_plans = {
                    "teachers": teachers_plan_extractor.teacher_plan(),
                    "forms": form_plan,
                    "rooms": teachers_plan_extractor.room_plan(),
                }

                self.cache.store_plan_file(
                    date, timestamp,
                    json.dumps(teachers_plans, default=PlanLesson.serialize),
                    "plans.teachers.json"
                )

                self.cache.store_plan_file(
                    date, timestamp,
                    json.dumps(teachers_plan_extractor.teacher_plan_extractor.info_data(all_forms_parsed)),
                    "info.teachers.json"
                )

                teachers_rooms_data = {
                    "used_rooms_by_period": (
                        used_rooms := teachers_plan_extractor.teacher_plan_extractor.used_rooms_by_period()
                    ),
                    "free_rooms_by_period": (
                        free_rooms := teachers_plan_extractor.teacher_plan_extractor.free_rooms_by_period(all_rooms)
                    ),
                    "used_rooms_by_block": teachers_plan_extractor.teacher_plan_extractor.rooms_by_block(used_rooms),
                    "free_rooms_by_block": teachers_plan_extractor.teacher_plan_extractor.rooms_by_block(free_rooms)
                }

                self.cache.store_plan_file(
                    date, timestamp,
                    json.dumps(teachers_rooms_data, default=list),
                    "rooms.teachers.json"
                )

            self.add_teachers(students_plan_extractor.extracted_teachers)
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

        self.scrape_teachers()
        self.update_forms()
        self.update_rooms()

    def scrape_teachers(self):
        if datetime.datetime.now() - self.teachers.scrape_timestamp < datetime.timedelta(hours=6):
            self._logger.info("* Skipping teacher scrape. Last update was less than 6 hours ago.")
            return

        self._logger.info("* Scraping teachers...")

        if self.school_number not in schools.teacher_scrapers:
            self._logger.debug("=> No teacher scraper available for this school.")
            scraped_teachers = {}
        else:
            self._logger.info("=> Scraping teachers...")
            try:
                _scraped_teachers = schools.teacher_scrapers[str(self.school_number)]()
            except Exception as e:
                self._logger.error(" -> Exception while scraping teachers.", exc_info=e)
                scraped_teachers = {}
            else:
                scraped_teachers = {teacher.abbreviation: teacher for teacher in _scraped_teachers}

            self._logger.debug(f" -> Found {len(scraped_teachers)} teachers.")

        self.add_teachers(scraped_teachers, update_timestamp=True)
        self.store_teachers()

    def add_teachers(self, new_teachers: dict[str, Teacher], update_timestamp: bool = False):
        self._logger.debug(f"=> Updating teachers... ({len(new_teachers)})")

        old_teachers = self.teachers.to_dict()
        all_abbreviations = set(old_teachers.keys()) | set(new_teachers.keys())

        merged_teachers = []
        for abbreviation in all_abbreviations:
            new_teacher = new_teachers.get(abbreviation, Teacher(abbreviation))
            old_teacher = old_teachers.get(abbreviation, Teacher(abbreviation))

            merged_teachers.append(
                Teacher.merge(new_teacher, old_teacher)
            )

        self.teachers = Teachers(
            teachers=merged_teachers,
            scrape_timestamp=datetime.datetime.now() if update_timestamp else self.teachers.scrape_timestamp
        )

    def store_teachers(self):
        self._logger.info("* Storing teachers...")
        self.cache.store_meta_file(
            json.dumps(self.teachers.serialize()),
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
        self.store_teachers()
