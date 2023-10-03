import os
from typing import Dict, Tuple
from dotenv import load_dotenv

import requests

load_dotenv()


def match_status_code(code) -> Tuple[bool, bool]:
    if code == 200:
        return True, True
    elif code == 401 or code == 403:
        return True, False
    elif code == 404:
        return False, False
    else:
        raise ValueError(f"status code unknown: {code}")


# returns a dict with keys school nums and values urls
def get_other_servers() -> Dict[str, str]:
    url = f"https://www.stundenplan24.de/extern/links24k.txt"
    username = os.getenv("LINKS24_USER")
    password = os.getenv("LINKS24_PASSWORD")
    r = requests.get(url, auth=(username, password))
    return {elem.split("=")[0]: elem.split("=")[1].strip() for elem in r.text.split("\n")}


class SchoolCandidate:
    test_url: str = ""
    school_exists: bool = False
    is_valid: bool = False
    servers: Dict[str, str] = {}
    needs_password: bool = True

    def __init__(self, abbreviation: str, school_num: str, username: str, password: str, test: bool = True) -> None:
        self.abbreviation: str = abbreviation
        self.school_num: str = school_num
        self.username: str = username
        self.password: str = password
        self.servers = SERVERS
        self.test_url = self.servers[school_num] if self.school_num in self.servers else f"https://www.stundenplan24.de/{self.school_num}/mobil/"
        self.test() if test else ...

    def test(self) -> Tuple[bool, bool]:
        try:
            r = requests.get(self.test_url)
        except requests.exceptions.ConnectionError or requests.exceptions.SSLError:
            return self.school_exists, self.is_valid
        self.school_exists, self.is_valid = match_status_code(r.status_code)
        if not self.school_exists:
            return self.school_exists, self.is_valid
        if self.is_valid:
            self.needs_password = False
            return self.school_exists, self.is_valid
        try:
            r = requests.get(self.test_url, auth=(self.username, self.password))
        except requests.exceptions.ConnectionError or requests.exceptions.SSLError:
            self.school_exists = False
            return self.school_exists, self.is_valid
        self.school_exists, self.is_valid = match_status_code(r.status_code)
        return self.school_exists, self.is_valid

    def __repr__(self) -> str:
        return f"SchoolCandidate(abbreviation={self.abbreviation}, school_num={self.school_num}, username={self.username}, password={self.password}, test_url={self.test_url}, school_exists={self.school_exists}, is_valid={self.is_valid}, needs_password={self.needs_password})"


SERVERS = get_other_servers()


def test_other_servers():
    for server in SERVERS:
        i = SchoolCandidate("", server, "", "")


if __name__ == "__main__":
    print(
        SchoolCandidate("", "123456578", "schueler", "testpasswort")
    )
