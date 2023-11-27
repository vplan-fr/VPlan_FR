import json
import os

from shared import comm
from shared import mongodb

import pywebpush

import dotenv

dotenv.load_dotenv()

_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE")
_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC")

_CLAIM = {
    "sub": "mailto:elanus4506@gmail.com"
}

_USERS_COLLECTION = mongodb.DATABASE.get_collection("users") if mongodb.DATABASE is not None else None


def msg_handler(msg: comm.Message) -> comm.Message | None:
    if isinstance(msg, comm.NewRevisionAvailable):
        if not mongodb.ENABLED:
            return None
        res = _USERS_COLLECTION.find({
            "authorized_schools": msg.school_number,
            "webpush_subscriptions": {"$exists": True}
        })
        for user in res:
            for subscription in user.get("webpush_subscriptions", []):
                try:
                    pywebpush.webpush(
                        subscription_info=subscription,
                        data=json.dumps({
                            "type": "new-revision-available",
                            "data": msg.serialize()
                        }),
                        vapid_private_key=_PRIVATE_KEY,
                        vapid_claims=_CLAIM
                    )
                except pywebpush.WebPushException as e:
                    print(e.response.text)
                    return None

    return None


def start_listen():
    comm.listen_messages(msg_handler)
