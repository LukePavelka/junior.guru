import logging
import os
from pathlib import Path
from typing import Any, Generator, Iterable, cast

from coop.lib import global_state
from coop.lib.chunks import chunks


MUTED_LOGGERS = [
    "asyncio",
    "discord",
    "google",
    "googleapiclient",
    "gql.transport.requests",
    "httpcore",
    "httpx",
    "juniorguru.lib.mutations.allowing",
    "juniorguru.sync.club_content.store",
    "juniorguru.web.templates",
    "MARKDOWN",
    "oauth2client",
    "openai._base_client",
    "peewee",
    "PIL",
    "protego",
    "stripe",
    "tornado.access",
    "urllib3",
]


class Logger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configured = False

    def __getitem__(self, name) -> logging.Logger:
        return self.getChild(str(name))

    def progress(
        self, iterable: Iterable, chunk_size=100
    ) -> Generator[Any, None, None]:
        total_count = 0
        for chunk in chunks(iterable, size=chunk_size):
            yield from chunk
            total_count += len(chunk)
            self.info(f"Done {total_count} items")


def _configure():
    level = _infer_level(global_state.get("log_level"), os.environ)
    timestamp = _infer_timestamp(global_state.get("log_timestamp"), os.environ)
    format = "[%(asctime)s] " if timestamp else ""
    format += "[%(name)s%(processSuffix)s] %(levelname)s: %(message)s"

    logging.setLogRecordFactory(_record_factory)
    logging.setLoggerClass(Logger)
    logging.root.setLevel(logging.DEBUG)

    for name in MUTED_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    stderr = logging.StreamHandler()
    stderr.setLevel(getattr(logging, level))
    stderr.setFormatter(logging.Formatter(format))
    logging.root.addHandler(stderr)

    # In multiprocessing, the child processes won't automatically
    # inherit logger configuration and this function will run again.
    global_state.set("log_level", level)
    global_state.set("log_timestamp", "true" if timestamp else "false")

    logging.root.configured = True


def reconfigure_level(level: str):
    for handler in logging.root.handlers:
        handler.setLevel(getattr(logging, level.upper()))
    global_state.set("log_level", level)


_original_record_factory = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs) -> logging.LogRecord:
    record = _original_record_factory(*args, **kwargs)
    record.processSuffix = _get_process_suffix(record.processName)
    return record


def _get_process_suffix(process_name: str) -> str:
    return (
        process_name.replace("MainProcess", "")
        .replace("SpawnPoolWorker-", "/worker")
        .replace("ForkPoolWorker-", "/worker")
        .replace("Process-", "/process")
    )


def _infer_level(global_value: str, env: dict) -> str:
    value = global_value
    if value is None:
        value = env.get("LOG_LEVEL")
    if not value:
        return "INFO"
    return value.upper()


def _infer_timestamp(global_value: str, env: dict) -> bool:
    value = global_value
    if value is None:
        value = env.get("LOG_TIMESTAMP")
    if value is None:
        value = env.get("CI")
    if not value or value.lower() in ["0", "false"]:
        return False
    return True


def get(name) -> Logger:
    return cast(Logger, logging.getLogger(name))


def from_path(path, cwd=None) -> Logger:
    cwd = cwd or os.getcwd()
    relative_path = str(Path(path).relative_to(cwd))
    name = ".".join(
        relative_path.removesuffix(".py")
        .removesuffix("__init__")
        .rstrip("/")
        .split("/")
    )
    return get(f"jg.{name}")


if not getattr(logging.root, "configured", False):
    _configure()
