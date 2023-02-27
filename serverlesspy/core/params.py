from enum import Enum

from typing_extensions import Self  # type: ignore


class ParamType(str, Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"


class Query:
    in_ = ParamType.QUERY


# class Path:
