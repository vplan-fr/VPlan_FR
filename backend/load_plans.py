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

from vplan_utils import group_forms
import models


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

    def get_days(self) -> list[datetime.date]:
        """Return a list of all days for which plans are stored."""

        path = self.path / "plans"
        return sorted([
            datetime.date.fromisoformat(elem.stem)
            for elem in path.iterdir() if elem.is_dir()
        ], reverse=True)

    def set_newest(self, day: datetime.date, timestamp: datetime.datetime):
        newest_path = self.get_plan_path(day, ".newest")
        target_path = self.get_plan_path(day, timestamp)

        newest_path.unlink(missing_ok=True)
        newest_path.symlink_to(target_path, target_is_directory=True)

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

    def __init__(self, client: Stundenplan24Client, cache: Cache):
        self.client = client
        self.cache = cache

        self._logger = logging.getLogger(f"{__name__}-{client.school_number}")

    async def update(self):
        self._logger.debug("Checking for new plans...")
        plan_files = await self.client.fetch_dates_indiware_mobil()  # requests vpdir.php
        needs_meta_update = False

        for filename, timestamp in plan_files.items():
            if filename == "Klassen.xml":
                # this is always the latest day planned
                continue

            cache_filename = "PlanKl.xml"
            date = datetime.datetime.strptime(filename, "PlanKl%Y%m%d.xml").date()

            # check if plan is already cached
            if self.cache.is_cached(date, timestamp, ".processed"):
                continue

            needs_meta_update = True
            self._logger.info(f" * Processing plan for {date}...")

            # download plan
            plan = await self.client.fetch_indiware_mobil(filename)

            self.cache.store_plan_file(date, timestamp, plan, cache_filename)

            self.process_plan(date, timestamp, plan)
            self.cache.set_newest(date, timestamp)

        if needs_meta_update:
            self._logger.info(" -> Updating meta data...")
            self.update_meta()

        self._logger.debug("...Done.")

    async def check_infinite(self, interval: int = 30):
        while True:
            await self.update()

            await asyncio.sleep(interval)

    def update_meta(self):
        meta_extractor = MetaExtractor(self.cache)

        data = {
            "dates": meta_extractor.dates_data(),
            "forms": group_forms(meta_extractor.forms()),
            "groups": meta_extractor.form_groups_data(),
            "teachers": meta_extractor.teachers(),
            "rooms": meta_extractor.rooms(),
            "default_times": meta_extractor.default_times().to_json()
        }
        self._last_meta_data = data
        self.cache.store_meta_file(json.dumps(data), "meta.json")

    def process_plan(self, date: datetime.date, timestamp: datetime.datetime, plan: str) -> None:
        plan_extractor = PlanExtractor(plan)

        self.cache.store_plan_file(
            date, timestamp,
            json.dumps({
                "room_plan": plan_extractor.room_plan(),
                "teacher_plan": plan_extractor.teacher_plan(),
                "form_plan": plan_extractor.form_plan()}, default=models.Lesson.to_json),
            "plans.json"
        )

        all_rooms = set(MetaExtractor(self.cache).rooms())
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

        self.cache.store_plan_file(date, timestamp, "", ".processed")


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
        return [elem.text for elem in self.element_tree.findall(".//Kurz")]

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

    def default_times(self) -> DefaultTimesInfo:
        if not self.element_tree.find(".//KlStunden"):
            return DefaultTimesInfo({})

        _klstunden = self.element_tree.find(".//KlStunden").findall("KlSt")
        data = {
            int(elem.text): (
                datetime.datetime.strptime(elem.get("ZeitVon"), "%H:%M").time(),
                datetime.datetime.strptime(elem.get("ZeitBis"), "%H:%M").time()
            ) for elem in _klstunden
        }

        return DefaultTimesInfo(data)


class MetaExtractor:
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

    def default_times(self) -> DefaultTimesInfo:
        for extractor in self.iterate_daily_extractors():
            default_times = extractor.default_times()
            if default_times.data:
                return default_times

        return DefaultTimesInfo({})

    def dates_data(self) -> dict[str, list[str]]:
        # noinspection PyTypeChecker
        return {
            day.isoformat(): list(map(datetime.datetime.isoformat, self.cache.get_timestamps(day)))
            for day in self.cache.get_days()
        }

    def form_groups_data(self):
        for extractor in self.iterate_daily_extractors():
            return {
                form: extractor.form_groups(form)
                for form in self.forms()
            }


class PlanExtractor:
    def __init__(self, plan_kl: str):
        form_plan = indiware_mobil.FormPlan.from_xml(ET.fromstring(plan_kl))
        self.plan = models.Plan.from_form_plan(form_plan)

    def room_plan(self):
        return self.plan.group_by("room")

    def teacher_plan(self):
        return self.plan.group_by("current_teacher")

    def form_plan(self):
        return self.plan.group_by("form_name")

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
            out[lesson.period].update(lesson.room)

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


async def main():
    logging.basicConfig(level=logging.DEBUG)

    # parse credentials
    with open("creds.json", "r", encoding="utf-8") as f:
        _creds = json.load(f)

    clients = []

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

        clients.append(p)

    await asyncio.gather(
        *[client.check_infinite() for client in clients]
    )


if __name__ == "__main__":
    asyncio.run(main())