from __future__ import annotations

import dataclasses
import datetime
import typing


class Teacher:
    def __init__(self,
                 plan_short: str,
                 full_name: str | None = None,
                 full_surname: str | None = None,
                 _plan_long: dict[str, int] = None,
                 info: str | None = None,
                 subjects: set[str] = None,
                 contact_link: str | None = None,
                 image_path: str | None = None,
                 last_seen: datetime.date = datetime.date.min,
                 plan_long: str = None):
        _plan_long = {} if _plan_long is None else _plan_long
        subjects = set() if subjects is None else subjects

        if plan_long is not None:
            _plan_long[plan_long] = 1

        self.plan_short = plan_short
        self.full_name = full_name
        self.full_surname = full_surname
        self._plan_long: dict[str, int] = _plan_long
        self.info = info  # TODO: to set?
        self.subjects = subjects
        self.contact_link = contact_link
        self.image_path = image_path
        self.last_seen = last_seen

    @property
    def plan_long(self) -> str:
        return max(self._plan_long, key=self._plan_long.get, default=None)

    def serialize(self) -> dict:
        return {
            "plan_short": self.plan_short,
            "full_name": self.full_name,
            "full_surname": self.full_surname,
            "_plan_long": self._plan_long,
            "plan_long": self.plan_long,
            "info": self.info,
            "subjects": list(self.subjects),
            "contact_link": self.contact_link,
            "image_path": self.image_path,
            "last_seen": self.last_seen.isoformat()
        }

    @classmethod
    def deserialize(cls, data: dict) -> Teacher:
        return cls(
            plan_short=data["plan_short"],
            full_name=data["full_name"],
            full_surname=data["full_surname"],
            _plan_long=data["_plan_long"],
            info=data["info"],
            subjects=set(data["subjects"]),
            contact_link=data.get("contact_link"),
            image_path=data.get("image_path"),
            last_seen=datetime.date.fromisoformat(data["last_seen"])
        )

    def merge(self, other: Teacher) -> Teacher:
        return Teacher(
            full_name=other.full_name or self.full_name,
            full_surname=other.full_surname or self.full_surname,
            _plan_long={k: v1 + v2 for k, v1, v2 in zip_dicts(self._plan_long, other._plan_long, default=0)},
            info=other.info or self.info,
            plan_short=other.plan_short or self.plan_short,
            subjects=other.subjects | self.subjects,
            contact_link=other.contact_link or self.contact_link,
            image_path=other.image_path or self.image_path,
            last_seen=max(other.last_seen, self.last_seen)
        )

    @staticmethod
    def strip_titles(surname: str) -> str:
        return " ".join(filter(lambda x: "." not in x, surname.split(" ")))

    @property
    def fullest_available_name(self) -> str:
        return self.full_name or self.full_surname or self.plan_long or self.plan_short


@dataclasses.dataclass
class Teachers:
    teachers: dict[str, Teacher] = dataclasses.field(default_factory=dict)
    scrape_timestamp: datetime.datetime = datetime.datetime.min

    def serialize(self) -> dict:
        return {
            "teachers": {teacher.plan_short: teacher.serialize() for teacher in self.teachers.values()},
            "timestamp": self.scrape_timestamp.isoformat()
        }

    @classmethod
    def deserialize(cls, data: dict) -> Teachers:
        return cls(
            teachers={key: Teacher.deserialize(teacher) for key, teacher in data["teachers"].items()},
            scrape_timestamp=datetime.datetime.fromisoformat(data["timestamp"])
        )

    def add_teachers(self, *teachers: Teacher):
        for teacher in teachers:
            if teacher.plan_short == "":
                continue

            if teacher.plan_short not in self.teachers:
                self.teachers[teacher.plan_short] = teacher
            else:
                self.teachers[teacher.plan_short] = self.teachers[teacher.plan_short].merge(teacher)

    def query(self, **attrs) -> list[Teacher]:
        out = []
        for teacher in self.teachers.values():
            if all(getattr(teacher, attr) == value for attr, value in attrs.items()):
                out.append(teacher)

        return sorted(out, key=lambda t: t.last_seen, reverse=True)

    def query_one(self, **attrs) -> Teacher:
        try:
            return next(iter(self.query(**attrs)))
        except StopIteration as e:
            raise LookupError("No teacher found matching the given attributes.") from e

    def query_plan_teacher(self, long_or_short: str) -> Teacher:
        try:
            return self.teachers[long_or_short]
        except KeyError:
            out = self.query(plan_long=long_or_short)
            if len(out) == 1:
                return out[0]
            elif not out:
                raise LookupError("No teacher found matching the given name.")
            else:
                raise LookupError("Multiple teachers found matching the given name.")


_UNSET = object()


def zip_dicts(*dicts: dict, default=_UNSET) -> typing.Generator[tuple, None, None]:
    if default is _UNSET:
        all_keys = set(dicts[0]).intersection(*dicts)
    else:
        all_keys = set().union(*dicts)

    for key in all_keys:
        yield key, *tuple(d.get(key, default) for d in dicts)
