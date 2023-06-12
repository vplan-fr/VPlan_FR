# coding=utf-8
from __future__ import annotations

import asyncio
import dataclasses
import datetime
import logging
import typing
from collections import defaultdict
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from stundenplan24_py import Stundenplan24Client, Stundenplan24Credentials, indiware_mobil

from .vplan_utils import group_forms
from . import models


class Cache:
    def __init__(self, path: Path):
        self.path = path

    def get_plan_path(self, day: datetime.date, timestamp: datetime.datetime | str | None):
        if timestamp is None:
            return self.path / "plans" / day.isoformat()
        elif isinstance(timestamp, datetime.datetime):
            return self.path / "plans" / day.isoformat() / timestamp.strftime("%Y-%m-%dT%H-%M-%S")
        else:
            return self.path / "plans" / day.isoformat() / timestamp

    def store_plan_file(self, day: datetime.date, timestamp: datetime.datetime, content: str, filename: str):
        """Store a plan file in the cache such as "PlanKl.xml" or "rooms.json"."""

        path = self.get_plan_path(day, timestamp) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_timestamps(self, day: datetime.date) -> list[datetime.datetime]:
        """Return all stored timestamps for a given day."""

        path = self.get_plan_path(day, None)
        return sorted([
            datetime.datetime.strptime(elem.stem, "%Y-%m-%dT%H-%M-%S")
            for elem in path.iterdir() if elem.is_dir() and not elem.stem.startswith(".")
        ], reverse=True)

    def get_days(self, reverse=True) -> list[datetime.date]:
        """Return a list of all days for which plans are stored."""

        path = self.path / "plans"
        if not path.exists():
            return []

        return sorted([
            datetime.date.fromisoformat(elem.stem)
            for elem in path.iterdir() if elem.is_dir()
        ], reverse=reverse)

    def set_newest(self, day: datetime.date, timestamp: datetime.datetime):
        newest_path = self.get_plan_path(day, ".newest")
        target_path = self.get_plan_path(day, timestamp)

        newest_path.unlink(missing_ok=True)
        newest_path.symlink_to(target_path, target_is_directory=True)

    def update_newest(self, day: datetime.date):
        timestamps = self.get_timestamps(day)
        self.get_plan_path(day, ".newest").unlink(missing_ok=True)
        if timestamps:
            self.set_newest(day, timestamps[0])

    def get_plan_file(self,
                      day: datetime.date,
                      timestamp: datetime.datetime | typing.Literal[".newest"],
                      filename: str) -> str:
        """Return the contents of a plan file from the cache."""

        path = self.get_plan_path(day, timestamp) / filename

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def is_cached(self,
                  day: datetime.date,
                  timestamp: datetime.datetime | typing.Literal[".newest"],
                  filename: str) -> bool:
        return (self.get_plan_path(day, timestamp) / filename).exists()

    def store_meta_file(self, content: str, filename: str):
        """Store a meta file in the cache such as "meta.json"."""

        path = self.path / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_meta_file(self, filename: str) -> str:
        """Return the contents of a meta file from the cache."""

        path = self.path / filename

        with open(path, "r", encoding="utf-8") as f:
            return f.read()


class PlanCrawler:
    """Check for new indiware plans in regular intervals and cache them along with their extracted and parsed
    (meta)data."""

    VERSION = "8"

    def __init__(self, client: Stundenplan24Client, cache: Cache):
        self.client = client
        self.cache = cache
        self.meta_extractor = MetaExtractor(self.cache)

        self._logger = logging.getLogger(f"{__name__}-{client.school_number}")

    async def update_fetch(self):
        self._logger.debug("Checking for new plans...")
        plan_files = await self.client.fetch_dates_indiware_mobil()  # requests vpdir.php

        await self.update(plan_files)

    async def update(self, downloadable_plan_files: dict[str, datetime.datetime], no_meta_update: bool = False):
        needs_meta_update = False

        for filename, timestamp in downloadable_plan_files.items():
            if filename == "Klassen.xml":
                # this is always the latest day planned
                continue

            date = datetime.datetime.strptime(filename, "PlanKl%Y%m%d.xml").date()

            # check if plan is already cached
            if not self.cache.is_cached(date, timestamp, "PlanKl.xml"):
                self._logger.info(f" -> Downloading plan for {date}...")

                plan = await self.client.fetch_indiware_mobil(filename)

                self.cache.store_plan_file(date, timestamp, plan, "PlanKl.xml")
            else:
                plan = None

            needs_meta_update |= self.update_plans(date, timestamp, plan)

        if needs_meta_update and not no_meta_update:
            self.update_meta()

            self._logger.info("...Done.")
        else:
            self._logger.debug("...Done.")

    def migrate_all(self):
        self._logger.info("Migrating cache...")

        for day in self.cache.get_days():
            self.cache.update_newest(day)

            for revision in self.cache.get_timestamps(day):
                self.update_plans(day, revision)

    def update_plans(self, day: datetime.date, revision: datetime.datetime, plan: str | None = None) -> bool:
        if self.cache.is_cached(day, revision, ".processed"):
            if self.cache.get_plan_file(day, revision, ".processed") == self.VERSION:
                return False

            self._logger.info(f" * Migrating plan for {day} to current version...")
        else:
            self._logger.info(f" * Processing plan for {day}...")

        plan = self.cache.get_plan_file(day, revision, "PlanKl.xml") if plan is None else plan
        self.compute_plans(day, revision, plan)

        return True

    async def check_infinite(self, interval: int = 30):
        self.migrate_all()

        while True:
            await self.update_fetch()

            await asyncio.sleep(interval)

    def update_meta(self):
        self._logger.info(" -> Updating meta data...")

        data = {
            "forms": group_forms(self.meta_extractor.forms()),
            "groups": self.meta_extractor.form_groups_data(),
            "teachers": self.meta_extractor.teachers(),
            "rooms": self.meta_extractor.rooms(),
            "default_times": self.meta_extractor.default_times(),
            "free_days": [date.isoformat() for date in self.meta_extractor.free_days()]
        }
        self.cache.store_meta_file(json.dumps(data, default=DefaultTimesInfo.to_json), "meta.json")
        self.cache.store_meta_file(json.dumps(self.meta_extractor.dates_data()), "dates.json")

    def compute_plans(self, date: datetime.date, timestamp: datetime.datetime, plan: str) -> None:
        plan_extractor = PlanExtractor(plan)

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps({
                "rooms": plan_extractor.room_plan(),
                "teachers": plan_extractor.teacher_plan(),
                "forms": plan_extractor.form_plan()}, default=models.Lesson.to_json),
            "plans.json"
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


@dataclasses.dataclass
class DefaultTimesInfo:
    data: dict[int, tuple[datetime.time, datetime.time]]

    def to_json(self) -> dict:
        return {
            period: (start.isoformat(), end.isoformat()) for period, (start, end) in self.data.items()
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


class DailyMetaExtractor:
    """Extracts meta information for a single day's plan."""

    def __init__(self, plankl_file: str):
        self.element_tree = ET.fromstring(plankl_file)
        self.form_plan = indiware_mobil.FormPlan.from_xml(self.element_tree)

    def teachers(self) -> dict[str, list[str]]:
        teachers = {}
        for elem in self.element_tree.findall(".//UeNr"):
            cur_teacher = elem.get("UeLe")
            cur_subject = elem.get("UeFa")
            cur_subject = cur_subject if cur_subject not in ["KL", "AnSt", "FÖ"] else ""
            if not cur_teacher: continue

            if cur_teacher not in teachers:
                teachers[cur_teacher] = []

            if cur_subject and cur_subject not in teachers[cur_teacher]:
                teachers[cur_teacher].append(cur_subject)

        for elem in self.element_tree.findall(".//KKz"):
            cur_teacher = elem.get("KLe")
            if cur_teacher and cur_teacher not in teachers:
                teachers[cur_teacher] = []

        return teachers

    def forms(self) -> list[str]:
        return [form.short_name for form in self.form_plan.forms]

    def rooms(self) -> set[str]:
        return set(room for elem in self.element_tree.findall(".//Ra") if elem.text for room in elem.text.split())

    def form_groups(self, form: str):
        kl = [elem for elem in self.element_tree.findall(".//Kl") if
              "" != elem.find("Kurz").text.strip() == form]
        if not kl:
            return []

        kl = kl[0]

        kurse = kl.find("Kurse")
        kurse = [elem.find("KKz") for elem in kurse.findall("Ku")]
        kurse = [(elem.text.strip(), elem.get("KLe", "")) for elem in kurse]
        return kurse
        # unterricht = kl.find("Unterricht")
        # unterricht = [elem.find("UeNr") for elem in unterricht.find_all("Ue")]
        # unterricht = [(elem.get("UeFa", ""), elem.get("UeLe", ""), elem.get("UeGr", ""), elem.text.strip())
        #               for elem in unterricht if elem]
        # return unterricht

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

    def teachers(self):
        teachers: dict[str, list[str]] = defaultdict(list)

        for extractor in self.iterate_daily_extractors():
            for teacher, subjects in extractor.teachers().items():
                teachers[teacher].extend(subjects)

        for teacher, subjects in teachers.items():
            teachers[teacher] = sorted(set(subjects))

        return teachers

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

    def form_groups_data(self):
        for extractor in self.iterate_daily_extractors():
            return {
                form: extractor.form_groups(form)
                for form in self.forms()
            }

    def free_days(self) -> list[datetime.date]:
        for extractor in self.iterate_daily_extractors():
            return extractor.free_days()


class PlanExtractor:
    def __init__(self, plan_kl: str):
        form_plan = indiware_mobil.FormPlan.from_xml(ET.fromstring(plan_kl))
        self.plan = models.Plan.from_form_plan(form_plan)
        self.lessons_grouped = self.plan.lessons.blocks_grouped()

    def room_plan(self):
        return self.lessons_grouped.group_by("rooms")

    def teacher_plan(self):
        return self.lessons_grouped.group_by("current_teacher")

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
    clients = await get_clients()

    await asyncio.gather(
        *[client.check_infinite() for client in clients.values()]
    )


if __name__ == "__main__":
    asyncio.run(main())
