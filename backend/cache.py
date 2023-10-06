from __future__ import annotations

import datetime
from pathlib import Path


class Cache:
    def __init__(self, path: Path):
        self.path = path

    def get_plan_path(self, day: datetime.date, timestamp: datetime.datetime | str | None) -> Path:
        if timestamp is None:
            return self.path / "plans" / day.isoformat()
        elif isinstance(timestamp, datetime.datetime):
            return (
                self.path / "plans" / day.isoformat()
                / timestamp.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
            )
        else:
            return self.path / "plans" / day.isoformat() / timestamp

    def store_plan_file(self, day: datetime.date, timestamp: datetime.datetime | str, content: str, filename: str):
        """Store a plan file in the cache such as "PlanKl.xml" or "rooms.json"."""

        path = self.get_plan_path(day, timestamp) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def remove_plan_file(self, day: datetime.date, timestamp: datetime.datetime | str, filename: str):
        """Remove a plan file from the cache."""

        path = self.get_plan_path(day, timestamp) / filename
        path.unlink(missing_ok=True)

    def get_plan_file(self,
                      day: datetime.date,
                      timestamp: datetime.datetime | str,
                      filename: str,
                      newest_before: bool = False) -> str:
        """Return the contents of a plan file from the cache."""
        # self._logger.debug(f"get_plan_file({day!r}, {timestamp!r}, {filename!r})")

        if newest_before and not isinstance(timestamp, str):
            timestamps = self.get_timestamps(day)
            timestamps = [t for t in timestamps if t <= timestamp]

            for older_timestamp in timestamps:
                try:
                    return self.get_plan_file(day, older_timestamp, filename, newest_before=False)
                except OSError:
                    pass
            else:
                raise FileNotFoundError
        else:
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

    def plan_file_exists(self,
                         day: datetime.date,
                         timestamp: datetime.datetime | str,
                         filename: str,
                         links_allowed: bool = True) -> bool:
        path = self.get_plan_path(day, timestamp) / filename
        return path.exists() and (links_allowed or not path.is_symlink())
