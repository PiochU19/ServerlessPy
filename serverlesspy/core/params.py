from abc import ABC
from enum import Enum
from typing import Union

from typing_extensions import Self  # type: ignore


class ParamType(str, Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"


class Param(ABC):
    in_: ParamType

    def __init__(self: Self, name: Union[str, None]) -> None:
        self.name = name


class Query(Param):
    in_ = ParamType.QUERY


class Path(Param):
    in_ = ParamType.PATH


class Header(Param):
    in_ = ParamType.HEADER
