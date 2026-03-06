import sys
from multiprocessing import Queue

from uvicorn import Config, Server

from spygraph.core import WebApi


class QueueWriter:
    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, message: str):
        if message and message.strip():
            self.queue.put(message.rstrip("\n"))

    def flush(self):
        pass

    def isatty(self):
        return False

    def fileno(self):
        raise AttributeError("QueueWriter has no file descriptor")


def run_api(
    queue: Queue,
    host: str = "0.0.0.0",
    port: int = 8000,
    ssl_cert: str | None = None,
    ssl_key: str | None = None,
    uuid: str | None = None,
    ipwhois: bool = False,
):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    queue_writer = QueueWriter(queue)

    sys.stdout = queue_writer
    sys.stderr = queue_writer

    try:
        api = WebApi(config={"forced_uuid": uuid, "ipwhois": ipwhois})

        config_kwargs = {"app": api, "host": host, "port": port, "log_level": "info", "server_header": False}

        if ssl_cert and ssl_key:
            config_kwargs["ssl_certfile"] = ssl_cert
            config_kwargs["ssl_keyfile"] = ssl_key

        config = Config(**config_kwargs)
        server = Server(config)
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        queue.put(None)
