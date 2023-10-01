import os

from backend.models import Teacher, Room


# teachers and images from: https://taroschule.de/lehrerinnen/
def get_teacher_images() -> list[str]:
    return os.listdir("client/public/base_static/images/teachers/10453929")


# matches provided by students (data that is private except for students of that school)
def get_teachers() -> list[Teacher]:
    teacher_lst = []
    if not os.path.exists("backend/schools/private_data/taro_teachers.csv"):
        return []
    with open("backend/schools/private_data/taro_teachers.csv", "r", encoding="utf-8") as f:
        hard_coded_teachers = f.read().split("\n")[1:]
    teacher_images = get_teacher_images()
    for teacher in hard_coded_teachers:
        teacher_data = teacher.split(",")
        if len(teacher_data) != 3:
            continue
        if teacher_data[1] and teacher_data[2]:
            for name in teacher_images:
                if name[:-4].startswith(teacher_data[2]) and name[:-4].endswith(teacher_data[1]):
                    teacher_lst.append(Teacher(
                        abbreviation=teacher_data[0],
                        surname=name[:-4].replace("_", " "),
                        image_path=name
                    ))
                    break
            else:
                teacher_lst.append(
                    Teacher(abbreviation=teacher_data[0], surname=f"{teacher_data[2]} {teacher_data[1]}")
                )
    return teacher_lst


def parse_room(room_str: str) -> Room:
    """
    Es ist fast wie am Ostwald: ([Haus]), [Etage], [Zweistellige Raumnummer]) einziger Unterschied:
        Haus ist nur ein optionaler Hinweis für 'Im Anbau'

    Ein raum im Hauptgebäude wäre also 307 (Dritte Etage, Raum 07)
    Im Anbau: E307 (Anbau, Dritte Etage, Raum 07)
    """
    exceptions = "SH", "TH", "HTWK", "AUL"

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


if __name__ == "__main__":
    # print(get_teacher_names())
    get_teachers()
