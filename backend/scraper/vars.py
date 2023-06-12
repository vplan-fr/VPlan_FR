import typing

from backend.scraper.teacher_scraper import *

teacher_scrapers: dict[str, typing.Callable[[], list[Teacher]]] = {
    "10001329": ostwald_teachers
}
