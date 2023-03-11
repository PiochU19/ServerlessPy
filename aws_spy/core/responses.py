from abc import ABC, abstractmethod
from typing import Any, Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore


class BaseResponseSPY(ABC):
    route: Union[BaseModel, None]

    @property
    @abstractmethod
    def response(self: Self) -> dict[str, Any]:
        raise NotImplementedError
