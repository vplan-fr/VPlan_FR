import typing

from . import ostwald, taro
from ..models import Teacher, Room

teacher_scrapers: dict[str, typing.Callable[[], list[Teacher]]] = {
    "10001329": ostwald.scrape_teachers
}

room_parsers: dict[str, typing.Callable[[str], Room]] = {
    "10001329": ostwald.parse_room,
    "10453929": taro.parse_room
}
