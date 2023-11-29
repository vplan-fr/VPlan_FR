import json
from bson import ObjectId

from utils import creds, users, meta

DATABASES = {
    "creds": creds,
    "users": users,
    "meta": meta
}
USE_ONLINE = False


def json_default(value):
    if isinstance(value, ObjectId):
        return str(value)  # Convert ObjectId to a string
    raise TypeError(f"Type {type(value)} is not JSON serializable")


def download_databases():
    for name in DATABASES:
        with open(f"datascience/data/{name}.json", "w+") as f:
            json.dump(list(DATABASES[name].find({})), f, default=json_default)


def load_database(database):
    if not USE_ONLINE:
        with open(f"datascience/data/{database}.json", "r") as f:
            return json.load(f)
    return list(DATABASES[database].find({}))


if __name__ == "__main__":
    download_databases()
