from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from backend.models import Teacher, Room


def scrape_teachers():
    r = requests.post("https://www.ostwaldgymnasium.de/index.php/schule/lehrer", data={"limit": "0"})

    soup = BeautifulSoup(r.text, features="html.parser")
    soup = soup.find("ul", {"class": "category"})

    teachers = soup.find_all("li")
    teacher_data = []

    for teacher in teachers:
        name, faecher = [elem.strip() for elem in teacher.find("a").text.strip().split(" -")[:2]]
        teacher.find("a").decompose()
        additional_info = teacher.find("div", {"class": "list-title"}).text.strip()
        kuerzel = teacher.find("div", {"class": "span3"}).text.strip()

        teacher_data.append(
            Teacher(
                full_name=None,
                surname=name,
                abbreviation=kuerzel,
                subjects=faecher.split(" "),
                info=additional_info,
            )
        )

    return teacher_data


def parse_room(room_str: str) -> Room:
    """Parses any room string and returns a Room object. Some examples:
    - "Aula"
    - "SH"
    - "TH1"
    - "12"
    - "2110"
    - "110"
    - "-2113"
    - "2104b"
    """

    cls = Room

    if room_str.startswith("TH"):
        _, __, room_nr = room_str.partition("TH")
        return cls("TH", None, int(room_nr))

    if room_str[0].isalpha():
        return cls(room_str, None, None)

    # check floor sign
    if room_str.startswith("-"):
        floor = -1
        room_str = room_str[1:]
    else:
        floor = 1

    # strip appendix
    if room_str[-1].isalpha():
        appendix = room_str[-1]
        room_str = room_str[:-1]
    else:
        appendix = ""

    if len(room_str) <= 2:
        # house and floor is omitted
        assert floor != -1

        house = 0
        floor = 0
        room_nr = int(room_str)

    elif len(room_str) == 3:
        # floor is omitted if 0
        assert floor != -1, "Floor cannot be omitted if negative."

        house = int(room_str[0])
        floor = 0
        room_nr = int(room_str[1:])

    elif len(room_str) == 4:
        house = int(room_str[0])
        floor *= int(room_str[1])
        room_nr = int(room_str[2:])

    else:
        raise ValueError(f"Invalid room string {room_str!r}.")

    return cls(house, floor, room_nr, appendix)


if __name__ == "__main__":
    o = scrape_teachers()
    print(o)
