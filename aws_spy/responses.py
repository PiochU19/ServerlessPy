import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from aws_spy.core.encoders import JSONEncoder
from aws_spy.core.schemas import SpyRoute


class ContentType(str, Enum):
    JSON = "application/json"
    XML = "application/xml"
    PLAIN = "text/plain"
    HTML = "text/html"


class BaseResponseSPY(ABC):
    @abstractmethod
    def response(self: Self) -> dict[str, Any]:
        raise NotImplementedError


class JSONResponse(BaseResponseSPY):
    def __init__(
        self: Self,
        data: Union[dict[str, Any], BaseModel],
        additional_headers: Union[dict[str, str], None] = None,
    ) -> None:
        self.data = data
        self.additional_headers = additional_headers
        self.route: Union[SpyRoute, None] = None

    @property
    def response(self: Self) -> dict[str, Any]:
        headers = {
            "Content-Type": ContentType.JSON.value,
        }
        if self.additional_headers is not None:
            headers.update(self.additional_headers)

        if self.route.response_class is not None and isinstance(self.data, dict):
            self.data = self.route.response_class.parse_obj(self.data)

        if (
            self.route.response_class is not None
            and isinstance(self.data, BaseModel)
            and not isinstance(self.data, self.route.response_class)
        ):
            self.data = self.route.response_class.parse_obj(self.data.dict())

        if isinstance(self.data, BaseModel):
            self.data = self.data.dict()

        return {
            "statusCode": self.route.status_code,
            "body": json.dumps(self.data, cls=JSONEncoder, ensure_ascii=False),
            "headers": headers,
        }


class RAWResponse(BaseResponseSPY):
    def __init__(self: Self, response: dict[str, Any]) -> None:
        self.response_ = response

    @property
    def response(self: Self) -> dict[str, Any]:
        return self.response_
