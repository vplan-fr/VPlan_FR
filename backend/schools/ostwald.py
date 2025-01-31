from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from backend.teacher import Teacher
from backend.room import Room


def _scrape_teachers_url(url: str) -> list[Teacher]:
    r = requests.post(url, data={"limit": "0"})

    soup = BeautifulSoup(r.text, features="html.parser")
    soup = soup.find("table", {"id": "contactList"}).find("tbody")

    teachers = soup.find_all("tr")
    teacher_data = []

    for teacher in teachers:
        name_and_subjects_a = teacher.find("a")

        teacher_link = name_and_subjects_a["href"]

        # very slow
        # teacher_link = teacher.find("a")["href"]
        # teacher_data.append(
        #     scrape_teacher(f"https://www.ostwaldgymnasium.de{teacher_link}")
        # )

        if "-" not in name_and_subjects_a.text:
            name = name_and_subjects_a.text.strip()
            subjects = set()
        else:
            name, subjects_str = [elem.strip() for elem in name_and_subjects_a.text.strip().split(" -")[:2]]
            subjects = set(subjects_str.replace("G/R/W", "GRW").split())

        name_and_subjects_a.decompose()

        additional_info = "\n".join(c.text.strip() for c in teacher.find("td").contents if c.text.strip())
        kuerzel = teacher.find("li", {"class": "kuerzel"}).find("span", {"class": "field-value"}).text.strip()

        if teacher_link:
            teacher_link = f"https://www.ostwaldgymnasium.de{teacher_link}#display-form"

        teacher_data.append(
            Teacher(
                full_name=None,
                full_surname=name,
                plan_long=Teacher.strip_titles(name.replace("Madame", "Frau").replace("Monsieur", "Herr")),
                plan_short=kuerzel,
                subjects=subjects,
                info=additional_info if additional_info else None,
                contact_link=teacher_link
            )
        )

    return teacher_data


def scrape_teachers() -> list[Teacher]:
    return (
        _scrape_teachers_url("https://www.ostwaldgymnasium.de/index.php/schule/kollegium/lehrer")
        + _scrape_teachers_url("https://www.ostwaldgymnasium.de/index.php/schule/kollegium/schulleitung")
    )


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
    a = scrape_teachers()
    breakpoint()
