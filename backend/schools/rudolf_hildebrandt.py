from __future__ import annotations

from backend.room import Room


def parse_room(room: str) -> Room:
    """
    Ja es gibt einteilung in haus a, b und c. T ist die turnhalle und au die aula.
    Etagen sind immer die erste nummer z.b. 235 ist dann etage 2 zimmer 35

    """

    if room in ("Au", "Bibo"):
        return Room(room, None, None)

    house, number = room[0], room[1:].rjust(3, "0")

    floor, room_number = int(number[0]), int(number[1:])

    if len(number) == 1:
        floor = None

    return Room(
        house=house,
        floor=floor,
        room_nr=room_number
    )
