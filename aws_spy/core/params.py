from abc import ABC
from enum import Enum

from typing_extensions import Self  # type: ignore


class ParamType(str, Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"


class Param(ABC):
    in_: ParamType

    def __init__(self: Self, name: str | None) -> None:
        self.name = name


class QueryClass(Param):
    in_ = ParamType.QUERY


class PathClass(Param):
    in_ = ParamType.PATH


class HeaderClass(Param):
    in_ = ParamType.HEADER
