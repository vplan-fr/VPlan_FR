import requests
from bs4 import BeautifulSoup

def ostwald_teachers():
    r = requests.post("https://www.ostwaldgymnasium.de/index.php/schule/lehrer", data={"limit": "0"})
    soup = BeautifulSoup(r.text, features="html.parser")
    soup = soup.find("ul", {"class": "category"})
    teachers = soup.find_all("li")
    teacher_data = {}
    for teacher in teachers:
        name, faecher = [elem.strip() for elem in teacher.find("a").text.strip().split(" -")[:2]]
        teacher.find("a").decompose()
        additional_info = teacher.find("div", {"class": "list-title"}).text.strip()
        kuerzel = teacher.find("div", {"class": "span3"}).text.strip()
        teacher_data[kuerzel] = {
            "name": name.split(" ")[-1],
            "title": " ".join(name.split(" ")[:-1]),
            "kuerzel": kuerzel,
            "faecher": faecher.split(" "),
            "info": additional_info,
        }
    return teacher_data


if __name__ == "__main__":
    o = ostwald_teachers()
    print(o)