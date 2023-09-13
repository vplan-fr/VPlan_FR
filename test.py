from typing import Tuple

import requests
from base64 import b64encode


class SchoolCandidate:
    def __init__(self, abbreviation: str, school_num: str, username: str, password: str,
                 server: str = "www.stundenplan24.de"):
        self.abbreviation = abbreviation
        self.school_num = school_num
        self.username = username
        self.password = password
        self.server = server
        self.school_exists = None
        self.is_valid = None

    def get_other_servers(self):
        ...

    def test(self) -> Tuple[bool, bool]:
        url = f"https://{self.server}/{self.school_num}/mobil/"
        headers = {
            "Authorization": f"Basic {b64encode(f'{self.username}:{self.password}'.encode('utf-8')).decode('utf-8')}"
        }
        r = requests.get(url, headers=headers)
        self.school_exists = False
        self.is_valid = False
        if r.status_code == 200:
            self.school_exists = True
            self.is_valid = True
        elif r.status_code == 401:
            self.school_exists = True
        elif r.status_code == 404:
            ...
        return self.school_exists, self.is_valid


if __name__ == "__main__":
    i = SchoolCandidate(
        "ostwald2",
        "10001329",
        "schueler",
        "WOGLeipzig@22"
    ).test()
    print(i)
