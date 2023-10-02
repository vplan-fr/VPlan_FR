import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import unquote


def download_path(base_url, cur_path):
    print(f"{base_url}/{cur_path}")
    r = requests.get(f"{base_url}/{cur_path}")
    os.makedirs(f"downloaded_files/{cur_path}", exist_ok=True)
    soup = BeautifulSoup(r.text, features="html.parser")
    links = soup.find_all("a")
    links = [link["href"] for link in links if link.text.strip() != "Parent Directory" and link.get("href")]
    print(links)
    for link in links:
        if link.endswith("/"):
            download_path(base_url=base_url, cur_path=f"{cur_path}/{link}")
        else:
            download_link = f"{base_url}/{cur_path}{link}"
            print(f"getting {download_link}")
            r = requests.get(download_link)
            with open(f"downloaded_files/{cur_path}{unquote(link)}", "wb+") as f:
                f.write(r.content)


def download_indiware_service_data():
    download_path(base_url="https://www.indiware.de", cur_path="service")


if __name__ == "__main__":
    download_indiware_service_data()