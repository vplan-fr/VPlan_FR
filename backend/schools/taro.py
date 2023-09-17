from backend.models import Room


def parse_room(room_str: str) -> Room:
    """
    Es ist fast wie am Ostwald: ([Haus]),[Etage],[Zweistellige Raumnummer) Einziger Unterschied:
        Haus ist nur ein optionaler Hinweis für 'Im Anbau'

    Ein raum im Hauptgebäude wäre also 307 (Dritte Etage, Raum 07)
    Im Anbau: E307 (Anbau, Dritte Etage, Raum 07)
    """
    exceptions = "SH", "TH", "HTWK"

    for exception in exceptions:
        if room_str.startswith(exception):
            return Room(exception, None, int(room_str[len(exception):]), "")

    if room_str.startswith("E"):
        house = "Anbau"
        room_str = room_str[1:]
    else:
        house = "Haupthaus"

    floor = int(room_str[0])
    room_nr = int(room_str[1:])

    return Room(house, floor, room_nr, "")
