import asyncio
import concurrent.futures
import dataclasses
import datetime
import logging
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
    date: datetime.date
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

    def submit(self, **kwargs):
        return submit_event(self.construct(**kwargs))


def _submit_event(event: Event):
    event_base_dict = event.get_base_dict()

    out = {}
    for key, value in dataclasses.asdict(event).items():
        if key in event_base_dict:
            continue

        if isinstance(value, (datetime.datetime, datetime.date)):
            out[key] = value.isoformat()
        else:
            out[key] = value

    entity = {
        **event_base_dict,
        "type": event.__class__.__name__,
        "data": out
    }

    _EVENTS_COLLECTION.insert_one(entity)


def submit_event(event: Event):
    if _DISABLED:
        logging.debug("MongoDB event collection disabled. Not submitting event.")
        return

    return _thread_pool_executor.submit(_submit_event, event)


_T2 = typing.TypeVar("_T2", bound=Event)


def iterate_events(type_: typing.Type[_T2], school_number: str | None = None) -> typing.Iterator[_T2]:
    cursor = _EVENTS_COLLECTION.find(
        {
            **({"type": type_.__name__} if type_ is not None else {}),
            **({"school_number": school_number} if school_number is not None else {}),
        },
        sort=[("start_time", pymongo.ASCENDING)]
    )

    for event in cursor:
        obj = type_.__new__(type_)

        for field in dataclasses.fields(obj):
            if field.name in event:
                continue

            if field.type is datetime.datetime:
                obj.__dict__[field.name] = datetime.datetime.fromisoformat(event["data"][field.name])
            else:
                try:
                    obj.__dict__[field.name] = event["data"][field.name]
                except KeyError:
                    pass

        obj.__dict__["school_number"] = event["school_number"]
        obj.__dict__["start_time"] = datetime.datetime.fromisoformat(event["start_time"])
        obj.__dict__["end_time"] = datetime.datetime.fromisoformat(event["end_time"])

        obj.__class__ = type_

        yield obj


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


_DISABLED: bool
_EVENTS_COLLECTION: pymongo.collection.Collection | None
_thread_pool_executor: concurrent.futures.ThreadPoolExecutor | None


def init_mongodb_event_collection():
    global _DISABLED, _EVENTS_COLLECTION, _thread_pool_executor
    env = dotenv.DotEnv(dotenv_path=dotenv.find_dotenv())

    _DISABLED = False
    if not env.get("PRODUCTION"):
        logging.warning("Not in production mode. Not submitting events.")
        _DISABLED = True

    if (mongo_uri := env.get("MONGO_URL")) is not None:
        collection = pymongo.MongoClient(mongo_uri).get_database("vplan").get_collection("events")
        logging.info("Event collection found.")
        _EVENTS_COLLECTION = collection
    else:
        logging.warning("No MONGO_URI found in .env file.")
        _DISABLED = True
        _EVENTS_COLLECTION = None

    if not _DISABLED:
        _thread_pool_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)


init_mongodb_event_collection()
