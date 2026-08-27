from datetime import datetime, tzinfo, UTC
from importlib import import_module
from threading import Lock


class Singleton(type):
    """Thread safe implementation of Singleton pattern"""

    __instances = {}
    __lock = Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            with cls.__lock:
                if cls not in cls.__instances:
                    cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]


def load_object(path: str):
    """
    Import object located at path.

    :param path: path-like string with the format package.path:<object-name>
    """
    parts = path.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid path: {path}")
    package_path, object_name = path.split(":")
    module = import_module(package_path)
    return getattr(module, object_name)


def to_utc_instant(local_naive: datetime, tz: tzinfo) -> datetime:
    """
    Interpret a naive wall-clock datetime in the given timezone and return the absolute UTC instant.

    :param local_naive: Naive datetime, read as wall-clock time in `tz`.
    :param tz: Timezone the wall-clock time belongs to.
    """
    return local_naive.replace(tzinfo=tz).astimezone(UTC)


def to_local_naive(instant: datetime, tz: tzinfo) -> datetime:
    """
    Convert an absolute instant to naive wall-clock time in the given timezone.

    :param instant: Timezone-aware datetime.
    :param tz: Timezone to express the instant in.
    """
    return instant.astimezone(tz).replace(tzinfo=None)
