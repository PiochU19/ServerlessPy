from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore


class BaseResponseSPY(ABC):
    route: BaseModel | None

    @property
    @abstractmethod
    def response(self: Self) -> dict[str, Any]:
        raise NotImplementedError  # pragma: no cover
