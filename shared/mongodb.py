import logging

import dotenv.main as dotenv
import pymongo.database

ENABLED: bool
DATABASE: pymongo.database.Database | None


def _init():
    global ENABLED, DATABASE
    logger = logging.getLogger("mongodb_provider")

    env = dotenv.DotEnv(dotenv_path=dotenv.find_dotenv())

    if (mongo_uri := env.get("MONGO_URL")) is not None:
        DATABASE = pymongo.MongoClient(mongo_uri).get_database("vplan")
    else:
        logger.warning("No MONGO_URI found in .env file.")
        DATABASE = None

    ENABLED = False
    if env.get("PRODUCTION") and DATABASE is not None:
        logger.info("Enabling DB.")
        ENABLED = True
    elif not env.get("PRODUCTION"):
        logger.warning("Not in production mode. Disabling DB.")
    elif DATABASE is None:
        logger.warning("No MongoDB database found. Disabling DB.")


_init()
