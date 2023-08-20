from __future__ import annotations

import asyncio
import dataclasses
import datetime
import json
import logging
from collections import defaultdict
from xml.etree import ElementTree as ET

from stundenplan24_py import (
    IndiwareStundenplanerClient, IndiwareMobilClient, PlanClientError, SubstitutionPlanClient, UnauthorizedError,
    substitution_plan, PlanNotFoundError, StudentsSubstitutionPlanEndpoint, TeachersSubstitutionPlanEndpoint
)

from .cache import Cache


import stundenplan24_py.client
stundenplan24_py.client.set_min_delay_between_requests(0.2)


@dataclasses.dataclass(frozen=True)
class PlanFileMetadata:
    plan_filename: str
    last_modified: datetime.datetime
    etag: str

    def serialize(self) -> dict:
        return {
            "plan_filename": self.plan_filename,
            "last_modified": self.last_modified.isoformat(),
            "etag": self.etag,
        }

    @classmethod
    def deserialize(cls, data: dict) -> PlanFileMetadata:
        return cls(
            plan_filename=data["plan_filename"],
            last_modified=datetime.datetime.fromisoformat(data["last_modified"]),
            etag=data["etag"],
        )


class PlanDownloader:
    """Check for new indiware plans in regular intervals store them in cache."""

    def __init__(self, client: IndiwareStundenplanerClient, cache: Cache, *, logger: logging.Logger):
        self._logger = logger

        self.client = client
        self.cache = cache

    async def check_infinite(self, interval: int = 60):
        self.migrate_all()
        # await asyncio.sleep(random.randint(0, 5))

        while True:
            await self.update_fetch()

            await asyncio.sleep(interval)

    async def update_fetch(self) -> dict[tuple[datetime.date, datetime.datetime], list[PlanFileMetadata]]:
        self._logger.debug("* Checking for new plans...")

        new: set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]] = set()

        # not using asyncio.gather because the logs would be confusing
        for indiware_client in self.client.indiware_mobil_clients:
            new |= await self.fetch_indiware_mobil(indiware_client)

        new |= await self.fetch_substitution_plans()

        out: dict[tuple[datetime.date, datetime.datetime], list[PlanFileMetadata]] = defaultdict(list)
        for date, revision, file_metadata in new:
            out[date, revision].append(file_metadata)

        return out

    async def fetch_indiware_mobil(
            self,
            indiware_client: IndiwareMobilClient
    ) -> set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]]:
        try:
            self._logger.debug(f"=> Fetching Indiware Mobil available files.")
            plan_files = await indiware_client.fetch_dates()
        except PlanClientError as e:
            if e.status_code in (401, 404):
                self._logger.debug(f"=> Insufficient credentials (or invalid URL) to fetch Indiware Mobil endpoint "
                                   f"{indiware_client.endpoint.url!r}. Error: {e.args[0]!r}.")
                return set()
            else:
                raise
        else:
            return await self.download_indiware_mobil(indiware_client, plan_files)

    async def download_indiware_mobil(
            self,
            client: IndiwareMobilClient,
            downloadable_plan_files: dict[str, datetime.datetime]
    ) -> set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]]:
        new: set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]] = set()

        for filename, last_modified in downloadable_plan_files.items():
            if "Plan" not in filename:
                # this is always the latest day planned, e.g. "Klassen.xml" or "Raeume.xml"
                continue

            date = datetime.datetime.strptime(filename[6:], "%Y%m%d.xml").date()
            plan_filename = filename[:6] + ".xml"

            assert plan_filename in {"PlanKl.xml", "PlanRa.xml", "PlanLe.xml"}, f"Invalid filename {plan_filename!r}"

            revision = last_modified

            if self.cache.plan_file_exists(date, revision, plan_filename):
                self._logger.debug(f" -> Skipping indiware {filename!r}. (date: {date!s})")
            else:
                self._logger.info(f" -> Downloading indiware {filename!r}. (date: {date!s})")

                plan_response = await client.fetch_plan(filename)

                assert plan_response.last_modified is not None
                downloaded_file = PlanFileMetadata(
                    plan_filename=plan_filename,
                    last_modified=plan_response.last_modified,
                    etag=plan_response.etag,
                )

                self.cache.store_plan_file(date, revision, plan_response.content, plan_filename)
                self.cache.store_plan_file(date, revision, json.dumps(downloaded_file.serialize()),
                                           plan_filename + ".json")
                self.complete_revision(date, revision)

                new.add((date, revision, downloaded_file))
        return new

    async def fetch_substitution_plans(self) -> set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]]:
        out = set()
        for substitution_plan_client in self.client.substitution_plan_clients:
            out |= await self.fetch_substitution_plan(substitution_plan_client)

        return out

    async def fetch_substitution_plan(
            self,
            plan_client: SubstitutionPlanClient
    ) -> set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]]:
        self._logger.debug("* Checking for new substitution plans...")

        try:
            base_plan = await plan_client.fetch_plan()
        except PlanNotFoundError:
            self._logger.debug(f"=> No substitution plan available for {plan_client.endpoint.url!r}.")
            return set()
        except UnauthorizedError:
            self._logger.debug(f"=> Insufficient credentials to fetch substitution plan from "
                               f"{plan_client.endpoint.url!r}.")
            return set()
        else:
            free_days = set(substitution_plan.SubstitutionPlan.from_xml(ET.fromstring(base_plan.content)).free_days)

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
            except PlanNotFoundError:
                self._logger.debug(f"=> Stopping substitution plan download at date {plan_date!s}.")
                break

        for plan_date in valid_date_iterator(datetime.date.today() + datetime.timedelta(days=1), step=1):
            try:
                out |= await self.download_substitution_plan(plan_client, plan_date)
            except PlanNotFoundError:
                self._logger.debug(f"=> Stopping substitution plan download at date {plan_date!s}.")
                break

        return out

    async def download_substitution_plan(
            self,
            plan_client: SubstitutionPlanClient,
            date: datetime.date
    ) -> set[tuple[datetime.date, datetime.datetime, PlanFileMetadata]]:
        if isinstance(plan_client.endpoint, StudentsSubstitutionPlanEndpoint):
            plan_filename = "VplanKl.xml"
        elif isinstance(plan_client.endpoint, TeachersSubstitutionPlanEndpoint):
            plan_filename = "VplanLe.xml"
        else:
            assert False

        # alternative to first doing a HEAD request: pass newest downloaded last_modified or etag to fetch_plan method
        # via get_latest_downloaded_file_timestamp() or get_downloaded_file_metadata(last_modified=None)
        for rev in self.cache.get_timestamps(date):
            if self.cache.plan_file_exists(date, rev, plan_filename + ".json"):
                metadata = PlanFileMetadata.deserialize(
                    json.loads(self.cache.get_plan_file(date, rev, plan_filename + ".json"))
                )
                last_modified = metadata.last_modified
                etag = metadata.etag
                break
        else:
            last_modified = None
            etag = None
        try:
            plan_response = await plan_client.fetch_plan(date, if_modified_since=last_modified, if_none_match=etag)
        except stundenplan24_py.NotModifiedError:
            self._logger.debug(f" -> Skipping substitution plan for date {date!s}.")
            return set()
        else:
            assert plan_response.last_modified is not None
            revision = plan_response.last_modified
            self._logger.info(f"=> Downloaded substitution plan for date {date!s}. Revision: {revision!s}.")
            downloaded_file = PlanFileMetadata(
                plan_filename=plan_filename,
                last_modified=plan_response.last_modified,
                etag=plan_response.etag,
            )

            self.cache.store_plan_file(date, revision, plan_response.content, plan_filename)
            self.cache.store_plan_file(date, revision, json.dumps(downloaded_file.serialize()), plan_filename + ".json")
            self.complete_revision(date, revision)

            return {(date, revision, downloaded_file)}

    def complete_revision(self, date: datetime.date, revision: datetime.datetime):
        if self.cache.plan_file_exists(date, revision, ".complete"):
            self._logger.debug(f" -> Revision {revision!s} for date {date!s} already completed.")
            return

        self._logger.debug(f" -> Completing revision {revision!s} for date {date!s}.")

        try:
            timestamps = [t for t in self.cache.get_timestamps(date) if t < revision]
            latest_revision = timestamps[0]  # before `revision`
        except IndexError:
            self._logger.debug(f" -> No previous revision found for date {date!s}.")
            self.cache.store_plan_file(date, revision, "", ".complete")
            return

        for file in self.cache.get_plan_path(date, latest_revision).iterdir():
            if not (file.name.endswith(".xml") or file.name.endswith(".xml.json")):
                continue

            if self.cache.plan_file_exists(date, revision, file.name, links_allowed=False):
                self._logger.debug(f" -> Skipping file {file.name!r}. Already exists.")
                continue

            self._logger.debug(f" -> Creating symlink for file {file.name!r}.")
            self.cache.store_plan_file_link(
                date,
                revision, file.name,
                latest_revision, file.name
            )

        self.cache.store_plan_file(date, revision, "", ".complete")

    def migrate_all(self):
        self._logger.debug(f"* Migrating cache ({self.__class__.__name__})...")

        for day in self.cache.get_days():
            self.cache.update_newest(day)

            for revision in reversed(self.cache.get_timestamps(day)):
                self._logger.debug(f"=> Date: {day!s}, Revision: {revision!s}.")
                self.complete_revision(day, revision)
