from ..room import Room


def parse_room(room_str: str) -> Room:
    """
    Raum 102:
    1 02
    |  |
    |  > Raumnummer auf der Etage
    > Etage

    E: Erweiterungsbau (kleines Haus, oder auch Schlümpfe Bau ;) )
    Z.B. E003: Erweiterungsbau, 0. Etage, Raum 3
    """
    exceptions = "SH", "Feld", "Gang", "C", "Aula"

    for exception in exceptions:
        if room_str.startswith(exception):
            _num_after = room_str[len(exception):]
            num_after = int(_num_after) if _num_after else None
            return Room(exception, None, num_after, "")

    if room_str.startswith("E"):
        house = "Erweiterungsbau"
        room_str = room_str[1:]
    else:
        house = "Haupthaus"

    floor = int(room_str[0])
    room_nr = int(room_str[1:])

    return Room(house, floor, room_nr, "")
