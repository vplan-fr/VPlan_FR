from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Teacher:
    abbreviation: str | None
    full_name: str | None = None
    surname: str | None = None
    info: str | None = None
    subjects: list[str] = dataclasses.field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "abbreviation": self.abbreviation,
            "full_name": self.full_name,
            "surname": self.surname,
            "info": self.info,
            "subjects": self.subjects
        }

    def merge(self, other: Teacher) -> Teacher:
        return Teacher(
            full_name=self.full_name or other.full_name,
            surname=self.surname or other.surname,
            info=self.info or other.info,
            abbreviation=self.abbreviation or other.abbreviation,
            subjects=list(set(self.subjects + other.subjects))
        )
