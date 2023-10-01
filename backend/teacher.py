from __future__ import annotations

import dataclasses
import datetime


@dataclasses.dataclass
class Teacher:
    abbreviation: str | None
    full_name: str | None = None
    surname: str | None = None
    info: str | None = None
    subjects: list[str] = dataclasses.field(default_factory=list)
    contact_link: str | None = None
    image_path: str | None = None

    def serialize(self) -> dict:
        return {
            "abbreviation": self.abbreviation,
            "full_name": self.full_name,
            "surname": self.surname,
            "info": self.info,
            "subjects": self.subjects,
            "contact_link": self.contact_link,
            "image_path": self.image_path
        }

    @classmethod
    def deserialize(cls, data: dict) -> Teacher:
        return cls(
            abbreviation=data["abbreviation"],
            full_name=data["full_name"],
            surname=data["surname"],
            info=data["info"],
            subjects=data["subjects"],
            contact_link=data.get("contact_link"),
            image_path=data.get("image_path"),
        )

    def merge(self, other: Teacher) -> Teacher:
        return Teacher(
            full_name=self.full_name or other.full_name,
            surname=self.surname or other.surname,
            info=self.info or other.info,
            abbreviation=self.abbreviation or other.abbreviation,
            subjects=list(set(self.subjects + other.subjects)),
            contact_link=self.contact_link or other.contact_link,
            image_path=self.image_path or other.image_path,
        )

    def surname_no_titles(self):
        """Strip parts of self.surname like "Dr." and return it."""
        if self.surname is not None:
            return " ".join(filter(lambda x: "." not in x, self.surname.split(" ")))
        else:
            return None


@dataclasses.dataclass
class Teachers:
    teachers: list[Teacher] = dataclasses.field(default_factory=list)
    scrape_timestamp: datetime.datetime = datetime.datetime.min

    def serialize(self) -> dict:
        return {
            "teachers": {teacher.abbreviation: teacher.serialize() for teacher in self.teachers},
            "timestamp": self.scrape_timestamp.isoformat()
        }

    @classmethod
    def deserialize(cls, data: dict) -> Teachers:
        return cls(
            teachers=[Teacher.deserialize(teacher) for teacher in data["teachers"].values()],
            scrape_timestamp=datetime.datetime.fromisoformat(data["timestamp"])
        )

    def to_dict(self) -> dict[str, Teacher]:
        return {teacher.abbreviation: teacher for teacher in self.teachers}

    def abbreviation_by_surname(self) -> dict[str, str]:
        return {teacher.surname_no_titles(): teacher.abbreviation
                for teacher in self.teachers
                if teacher.surname is not None}
