import json
import os

from shared import comm

import pywebpush

import dotenv

dotenv.load_dotenv()

_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE")
_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC")

_CLAIM = {
    "sub": "mailto:elanus4506@gmail.com"
}


def msg_handler(msg: comm.Message) -> comm.Message | None:
    if isinstance(msg, comm.NewRevisionAvailable):
        subs = []

        for subscription in subs:
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


comm.listen_messages(msg_handler)
