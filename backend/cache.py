from __future__ import annotations

import datetime
import json
import typing
from pathlib import Path


class Cache:
    def __init__(self, path: Path):
        self.path = path

    def get_plan_path(self, day: datetime.date, timestamp: datetime.datetime | str | None):
        if timestamp is None:
            return self.path / "plans" / day.isoformat()
        elif isinstance(timestamp, datetime.datetime):
            return (
                    self.path / "plans" / day.isoformat()
                    / timestamp.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
            )
        else:
            return self.path / "plans" / day.isoformat() / timestamp

    def store_plan_file(self, day: datetime.date, timestamp: datetime.datetime, content: str, filename: str):
        """Store a plan file in the cache such as "PlanKl.xml" or "rooms.json"."""

        path = self.get_plan_path(day, timestamp) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_plan_file(self,
                      day: datetime.date,
                      timestamp: datetime.datetime | typing.Literal[".newest"],
                      filename: str) -> str:
        """Return the contents of a plan file from the cache."""
        # self._logger.debug(f"get_plan_file({day!r}, {timestamp!r}, {filename!r})")

        path = self.get_plan_path(day, timestamp) / filename

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

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

    def get_days(self, reverse=True) -> list[datetime.date]:
        """Return a list of all days for which plans are stored."""

        path = self.path / "plans"
        if not path.exists():
            return []

        return sorted([
            datetime.date.fromisoformat(elem.stem)
            for elem in path.iterdir() if elem.is_dir()
        ], reverse=reverse)

    def get_timestamps(self, day: datetime.date) -> list[datetime.datetime]:
        """Return all stored timestamps for a given day."""

        path = self.get_plan_path(day, None)

        if not path.exists():
            return []

        return sorted([
            datetime.datetime.strptime(elem.stem, "%Y-%m-%dT%H-%M-%S").replace(tzinfo=datetime.timezone.utc)
            for elem in path.iterdir() if elem.is_dir() and not elem.stem.startswith(".")
        ], reverse=True)

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

    def get_all_json_plan_files(self,
                                day: datetime.date,
                                timestamp: datetime.datetime | typing.Literal[".newest"]) -> dict[str, typing.Any]:
        out = {}

        for file in self.get_plan_path(day, timestamp).iterdir():
            if file.suffix == ".json" and not file.name.startswith("."):
                with open(file, "r", encoding="utf-8") as f:
                    out[file.stem] = json.load(f)

        return out

    def contains(self,
                 day: datetime.date,
                 timestamp: datetime.datetime | typing.Literal[".newest"],
                 filename: str) -> bool:
        return (self.get_plan_path(day, timestamp) / filename).exists()
