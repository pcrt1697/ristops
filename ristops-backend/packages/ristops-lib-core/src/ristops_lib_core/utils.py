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
