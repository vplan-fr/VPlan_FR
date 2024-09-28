import dataclasses
import datetime
import typing

import pymongo

import shared.mongodb


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
    proxies_used: int | None = None


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
    # noinspection PyDataclass
    for key, value in dataclasses.asdict(event).items():
        if isinstance(value, (datetime.datetime, datetime.date)):
            out[key] = value.isoformat()
        else:
            out[key] = value

    entity = {
        **event_base_dict,
        "type": event.__class__.__name__,
        "data": out
    }

    with pymongo.timeout(5):
        _COLLECTION.insert_one(entity)


def submit_event(event: Event):
    if not shared.mongodb.ENABLED:
        # logging.debug("MongoDB event collection disabled. Not submitting event.")
        return

    _submit_event(event)


_T2 = typing.TypeVar("_T2", bound=Event)


def iterate_events(type_: typing.Type[_T2], school_number: str | None = None,
                   since: datetime.datetime | None = None,
                   until: datetime.datetime | None = None) -> typing.Iterator[_T2]:
    cursor = _COLLECTION.find(
        {
            **({"type": type_.__name__} if type_ is not None else {}),
            **({"school_number": school_number} if school_number is not None else {}),
            **({"start_time": {"$gte": since.isoformat()}} if since is not None else {}),
            **({"end_time": {"$lte": until.isoformat()}} if until is not None else {}),
        },
        sort=[("start_time", pymongo.ASCENDING)]
    )

    for event in cursor:
        obj = type_.__new__(type_)

        obj.__dict__ = event["data"]
        base_keys = [f.name for f in dataclasses.fields(Event)]

        for field in dataclasses.fields(obj):
            if field.name in base_keys:
                continue

            if field.type is datetime.datetime and obj.__dict__[field.name] is not None:
                obj.__dict__[field.name] = datetime.datetime.fromisoformat(obj.__dict__[field.name])
            elif field.type is datetime.date and obj.__dict__[field.name] is not None:
                obj.__dict__[field.name] = datetime.date.fromisoformat(obj.__dict__[field.name])

        obj.__dict__["school_number"] = event["school_number"]
        obj.__dict__["start_time"] = datetime.datetime.fromisoformat(event["start_time"])
        obj.__dict__["end_time"] = datetime.datetime.fromisoformat(event["end_time"])

        obj.__class__ = type_

        yield obj


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


_COLLECTION = shared.mongodb.DATABASE.get_collection("events") if shared.mongodb.DATABASE is not None else None
