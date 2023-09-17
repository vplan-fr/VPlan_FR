from __future__ import annotations
from typing import List

import requests
from bs4 import BeautifulSoup

from backend.models import Teacher, Room


def scrape_teachers() -> List[Teacher]:
    r = requests.post("https://www.ostwaldgymnasium.de/index.php/schule/lehrer", data={"limit": "0"})

    soup = BeautifulSoup(r.text, features="html.parser")
    soup = soup.find("ul", {"class": "category"})

    teachers = soup.find_all("li")
    teacher_data = []

    for teacher in teachers:
        teacher_link = teacher.find("a")["href"]
        """
        # very slow
        teacher_link = teacher.find("a")["href"]
        teacher_data.append(
            scrape_teacher(f"https://www.ostwaldgymnasium.de{teacher_link}")
        )"""
        name, faecher = [elem.strip() for elem in teacher.find("a").text.strip().split(" -")[:2]]
        teacher.find("a").decompose()
        additional_info = teacher.find("div", {"class": "list-title"}).text.strip()
        kuerzel = teacher.find("div", {"class": "span3"}).text.strip()

        if teacher_link:
            teacher_link = f"https://www.ostwaldgymnasium.de{teacher_link}#display-form"
        teacher_data.append(
            Teacher(
                full_name=None,
                surname=name.replace("Madame", "Frau").replace("Monsieur", "Herr"),
                abbreviation=kuerzel,
                subjects=faecher.replace("G/R/W", "GRW").split(" "),
                info=additional_info,
                contact_link=teacher_link
            )
        )

    r2 = requests.get("https://www.ostwaldgymnasium.de/index.php/kontakte/12-schulleitung")
    soup = BeautifulSoup(r2.text, features="html.parser")
    soup = soup.find("ul", {"class": "category"})
    teachers = soup.find_all("li")
    for teacher in teachers:
        teacher_link = teacher.find("a")["href"]
        teacher_data.append(
            scrape_teacher(f"https://www.ostwaldgymnasium.de{teacher_link}")
        )
    return teacher_data


def scrape_teacher(teacher_link: str) -> Teacher:
    r = requests.get(teacher_link)
    soup = BeautifulSoup(r.text, features="html.parser")
    name_field = soup.find("span", {"class": "contact-name"}).text.strip()
    if "-" in name_field:
        name, subjects, _ = name_field.split(" -")
        name, subjects = name.strip(), subjects.strip()
        subjects = subjects.split(" ")
    else:
        name = name_field
        subjects = soup.find("span", {"class": "contact-misc"}).find("p").text.strip().split("/")

    additional_info = soup.find("dd", {"itemprop": "jobTitle"})
    if additional_info:
        additional_info = additional_info.text.strip()
    else:
        additional_info = ""
    kuerzel = soup.find("span", {"class": "contact-mobile", "itemprop": "telephone"}).text.strip()
    return Teacher(
        full_name=None,
        surname=name.replace("Madama", "Frau").replace("Monsieur", "Frau"),
        subjects=subjects,
        abbreviation=kuerzel,
        info=additional_info,
        contact_link=f"{teacher_link}#display-form"
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
    ...
