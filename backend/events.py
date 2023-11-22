import asyncio
import dataclasses
import datetime
import logging
import time
import typing

import dotenv.main as dotenv
import pymongo


@dataclasses.dataclass
class Event:
    school_number: str
    start_time: datetime.datetime
    end_time: datetime.datetime

    def get_base_dict(self):
        assert self.start_time.tzinfo is not None is not self.end_time.tzinfo
        return {
            "school_number": self.school_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }


@dataclasses.dataclass
class PlanDownload(Event):
    plan_type: str  # Ex: "PlanKl.xml" or "VPlanKl.xml"
    last_modified: datetime.datetime
    file_length: int


@dataclasses.dataclass
class AllPlansDownloaded(Event):
    pass


@dataclasses.dataclass
class PlanCrawlCycle(Event):
    pass


@dataclasses.dataclass
class RevisionProcessed(Event):
    version: str
    date: datetime.date
    revision: datetime.datetime


@dataclasses.dataclass
class StudentsRevisionProcessed(RevisionProcessed):
    has_vplan: bool | None


@dataclasses.dataclass
class TeachersRevisionProcessed(RevisionProcessed):
    pass


@dataclasses.dataclass
class TeacherScrape(Event):
    teacher_count: int


@dataclasses.dataclass
class MetaUpdate(Event):
    pass


_T = typing.TypeVar("_T", bound=Event)


class Timer(typing.Generic[_T]):
    start: datetime.datetime
    end: datetime.datetime

    def __init__(self, school_number: str, event_type: typing.Type[_T]):
        self.school_number = school_number
        self.event_type = event_type

    def __enter__(self):
        self.start = now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = now()

    def construct(self, **kwargs) -> _T:
        return self.event_type(
            school_number=self.school_number,
            start_time=self.start,
            end_time=self.end,
            **kwargs
        )

    async def submit_async(self, **kwargs):
        await submit_event_async(self.construct(**kwargs))

    def submit(self, **kwargs):
        return _submit_event(self.construct(**kwargs))


def _submit_event(event: Event):
    if _EVENTS_COLLECTION is None:
        logging.debug("No MongoDB collection found. Not submitting event.")
        return

    event_base_dict = event.get_base_dict()

    out = {}
    for key, value in dataclasses.asdict(event).items():
        if key in event_base_dict:
            continue

        if isinstance(value, datetime.datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value

    entity = {
        **event_base_dict,
        "type": event.__class__.__name__,
        "data": out
    }

    _EVENTS_COLLECTION.insert_one(entity)


async def submit_event_async(event: Event):
    await asyncio.get_event_loop().run_in_executor(None, _submit_event, event)


def submit_event(event: Event):
    return asyncio.get_event_loop().create_task(submit_event_async(event))


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def get_mongodb_event_collection() -> pymongo.collection.Collection | None:
    env = dotenv.DotEnv(dotenv_path=dotenv.find_dotenv())

    if not env.get("PRODUCTION"):
        logging.warning("Not in production mode. Not submitting events.")
        return

    if (mongo_uri := env.get("MONGO_URL")) is not None:
        collection = pymongo.MongoClient(mongo_uri).get_database("vplan").get_collection("events")
        logging.info("Event collection found.")
        return collection
    else:
        logging.warning("No MONGO_URI found in .env file.")


_EVENTS_COLLECTION = get_mongodb_event_collection()
