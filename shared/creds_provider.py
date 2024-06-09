import abc
import json
import logging
from pathlib import Path

import pymongo.database
from dotenv.main import DotEnv, find_dotenv


class CredsProvider(abc.ABC):
    @abc.abstractmethod
    def get_creds(self, ignore_disabled: bool = False) -> dict:
        pass


class FileCredsProvider(CredsProvider):
    def __init__(self, path: Path):
        self.path = path

    def get_creds(self, ignore_disabled: bool = False) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)


class MongoDbCredsProvider(CredsProvider):
    def __init__(self, collection: pymongo.database.Collection):
        self.collection = collection

    def get_creds(self, ignore_disabled: bool = False) -> dict:
        pipeline = [
            *([{
                "$match": {
                    "$or": [
                        {"is_disabled": {"$exists": False}},
                        {"is_disabled": False},
                    ]
                }
            }] if not ignore_disabled else []),
            {
                "$sort": {"count": pymongo.DESCENDING},
            },
            {
                "$project": {
                    "count": False,
                    "comment": False,
                }
            }
        ]

        out = self.collection.aggregate(pipeline)

        return {elem["short_name"]: elem for elem in out}


def get_creds_provider(creds_filepath: Path | None) -> CredsProvider:
    dotenv = DotEnv(dotenv_path=find_dotenv())

    if (mongo_uri := dotenv.get("MONGO_URL")) is not None:
        collection = pymongo.MongoClient(mongo_uri).get_database("vplan").get_collection("creds")
        logging.info("Using MongoDB as credentials source.")
        return MongoDbCredsProvider(collection)
    else:
        logging.debug("No MONGO_URI found in .env file.")

    if creds_filepath.exists():
        logging.info(f"Using {creds_filepath!r} as credentials source.")
        return FileCredsProvider(creds_filepath)
    else:
        logging.debug(f"Creds file {creds_filepath!r} does not exist.")

    raise FileNotFoundError(f"Could not find a credentials source.")
