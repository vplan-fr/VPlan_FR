import abc
import asyncio
import concurrent.futures
import dataclasses
import datetime
import json
import logging
import multiprocessing
import typing
from http.server import HTTPServer, BaseHTTPRequestHandler

import aiohttp
import urllib3.util


class Message(abc.ABC):
    @abc.abstractmethod
    def serialize(self):
        ...

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, data):
        ...


@dataclasses.dataclass
class NewRevisionAvailable(Message):
    school_number: str
    date: datetime.date
    revision: datetime.datetime

    def serialize(self):
        return {
            "school_number": self.school_number,
            "date": self.date.isoformat(),
            "revision": self.revision.isoformat()
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            school_number=data["school_number"],
            date=datetime.date.fromisoformat(data["date"]),
            revision=datetime.datetime.fromisoformat(data["revision"])
        )


_CLASSES = NewRevisionAvailable,
_PORT = 54341


class _UnknownClassError(Exception): ...


class _DeserializeError(Exception): ...


def _serialize(msg: Message | None) -> bytes:
    return json.dumps({
        "class_name": msg.__class__.__name__,
        "data": msg.serialize() if msg is not None else None,
        "success": True
    }).encode("utf-8")


def _deserialize(data: bytes) -> Message | None:
    data = json.loads(data.decode("utf-8"))

    if not data["success"]:
        raise _DeserializeError(f"Received message with success=False. Message: {data!r}.")

    if data["data"] is None:
        return None

    class_name = data["class_name"]
    for class_ in _CLASSES:
        if class_.__name__ == class_name:
            break
    else:
        raise _UnknownClassError(f"Received message of unknown class {class_name!r}.")

    try:
        return class_.deserialize(data["data"])
    except Exception as e:
        raise _DeserializeError(f"Error while deserializing message of class {class_name!r}. Data: {data!r}.") from e


async def send_message_async(message: Message) -> Message | None:
    async with asyncio.timeout(10):
        try:
            async with aiohttp.ClientSession() as session:
                session: aiohttp.ClientSession

                data = _serialize(message)

                url = urllib3.util.Url(scheme="http", host="localhost", port=_PORT)

                async with session.post(str(url), data=data, timeout=5) as response:
                    return _deserialize(await response.content.read())
        except aiohttp.ClientConnectorError as e:
            if e.errno == 111:
                logging.getLogger("comm").warning(f"Error while sending message. Error: {str(e)}")
                return None
            else:
                raise
        except Exception as e:
            logging.getLogger("comm").error("Error while sending message.", exc_info=e)
            return None


_process_pool_executor = concurrent.futures.ProcessPoolExecutor(max_workers=2)


def _send_message_sync(message):
    return asyncio.run(send_message_async(message))


def send_message(message: Message) -> Message | None:
    return _process_pool_executor.submit(_send_message_sync, message).result()


def _listen_messages(callback: typing.Callable[[Message], None | Message]):
    logger = logging.getLogger("comm")

    class _HttpRequestHandler(BaseHTTPRequestHandler):
        def _set_response(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            data = self.rfile.read(content_length)

            try:
                msg = _deserialize(data)
            except _UnknownClassError as e:
                logger.error(f"Received message of unknown class.", exc_info=e)

                self._set_response()
                response = {"data": "Unknown class.", "success": False, "class_name": None}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            except _DeserializeError as e:
                logger.exception(f"Error while deserializing message.",
                                 exc_info=e)

                self._set_response()
                response = {"data": "Error while deserializing message.", "success": False, "class_name": None}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            else:
                out = callback(msg)
                data = _serialize(out)

                self._set_response()
                self.wfile.write(data)

    httpd = HTTPServer(server_address=('', _PORT), RequestHandlerClass=_HttpRequestHandler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def listen_messages(callback: typing.Callable[[Message], None | Message]):
    multiprocessing.Process(target=_listen_messages, args=(callback,), daemon=True).start()
