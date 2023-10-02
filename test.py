import os
from typing import Dict, Tuple
from dotenv import load_dotenv

import requests

load_dotenv()


def match_status_code(code) -> Tuple[bool, bool]:
    if code == 200:
        return True, True
    elif code == 401:
        return True, False
    elif code == 404:
        return False, False
    else:
        raise ValueError(f"status code unknown: {code}")


def get_other_servers() -> Dict[str, str]:
    url = f"https://www.stundenplan24.de/extern/links24k.txt"
    username = os.getenv("LINKS24_USER")
    password = os.getenv("LINKS24_PASSWORD")
    print(username, password)
    r = requests.get(url, auth=(username, password))
    return {elem.split("=")[0]: elem.split("=")[1].strip() for elem in r.text.split("\n")}


class SchoolCandidate:
    test_url: str = ""
    school_exists: bool = False
    is_valid: bool = False
    servers: Dict[str, str] = {}
    needs_password: bool = True

    def __init__(self, abbreviation: str, school_num: str, username: str, password: str, test: bool = True):
        self.abbreviation: str = abbreviation
        self.school_num: str = school_num
        self.username: str = username
        self.password: str = password
        self.servers = get_other_servers()
        self.test_url = self.servers[school_num] if self.school_num in self.servers else f"https://www.stundenplan24.de/{self.school_num}/mobil/"
        self.test() if test else ...

    def test(self) -> Tuple[bool, bool]:
        # testing doesnw really work apparently
        r = requests.get(self.test_url)
        self.school_exists, self.is_valid = match_status_code(r.status_code)
        if self.school_exists:
            self.needs_password = False
            return self.school_exists, self.is_valid
        r = requests.get(self.test_url, auth=(self.username, self.password))
        self.school_exists, self.is_valid = match_status_code(r.status_code)
        return self.school_exists, self.is_valid


if __name__ == "__main__":
    servers = get_other_servers()
    for server_id, server_link in servers.items():
        print(server_id, server_link)
        """i = SchoolCandidate(
            "",
            server_id,
            "",
            ""
        )"""
        #print(i.needs_password)
