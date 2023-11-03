from __future__ import annotations

import dataclasses
import datetime


@dataclasses.dataclass
class Teacher:
    plan_short: str
    full_name: str | None = None
    full_surname: str | None = None
    plan_long: str | None = None
    info: str | None = None  # TODO: to set?
    subjects: set[str] = dataclasses.field(default_factory=set)
    contact_link: str | None = None
    image_path: str | None = None
    last_seen: datetime.date = datetime.date.min

    def serialize(self) -> dict:
        return {
            "plan_short": self.plan_short,
            "full_name": self.full_name,
            "full_surname": self.full_surname,
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
            plan_long=data["plan_long"],
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
            plan_long=other.plan_long or self.plan_long,
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
        return self.teachers.get(long_or_short, self.query_one(plan_long=long_or_short))
