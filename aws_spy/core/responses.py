import typing as t
from abc import ABC, abstractmethod

import typing_extensions as te
from pydantic import BaseModel


class BaseResponseSPY(ABC):
    route: BaseModel | None

    @property
    @abstractmethod
    def response(self: te.Self) -> dict[str, t.Any]:
        raise NotImplementedError  # pragma: no cover
