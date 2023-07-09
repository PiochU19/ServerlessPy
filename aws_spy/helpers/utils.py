import importlib
import sys
from pathlib import Path

from aws_spy import SpyAPI


class LoadAppFromStringError(Exception):
    ...


def load_app_from_string(import_string: str) -> SpyAPI:
    sys.path.append(str(Path().resolve()))

    module_string, _, app_name = import_string.partition(":")
    if not module_string or not app_name:
        msg = 'Path must be in format "<module>:<app_name>"'
        raise LoadAppFromStringError(msg)

    try:
        module = importlib.import_module(module_string)
    except ImportError as exc:
        if exc.name != module_string:
            raise exc from None
        msg = f'Could not import "{module_string}"'
        raise LoadAppFromStringError(msg) from None

    try:
        return getattr(module, app_name)
    except AttributeError:
        msg = f'Attribute "{app_name}" not found in "{module_string}" module'
        raise LoadAppFromStringError(msg) from None
