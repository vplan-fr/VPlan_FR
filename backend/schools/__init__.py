import typing

from . import ostwald, taro, rudolf_hildebrandt, school_10252109
from ..room import Room
from ..teacher import Teacher

teacher_scrapers: dict[str, typing.Callable[[], list[Teacher]]] = {
    # "10001329": ostwald.scrape_teachers,  # TODO
    # "10453929": taro.get_teachers,
}

room_parsers: dict[str, typing.Callable[[str], Room]] = {
    "10001329": ostwald.parse_room,
    "10453929": taro.parse_room,
    "10078734": rudolf_hildebrandt.parse_room,
    "10252109": school_10252109.parse_room
}
