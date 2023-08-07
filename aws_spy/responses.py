import json
import typing as t
from enum import Enum

import typing_extensions as te
from pydantic import BaseModel

from aws_spy.core.encoders import JSONEncoder
from aws_spy.core.responses import BaseResponseSPY
from aws_spy.core.schemas import SpyRoute


class ContentType(str, Enum):
    JSON = "application/json"


class JSONResponse(BaseResponseSPY):
    def __init__(
        self: te.Self,
        data: dict[str, t.Any] | BaseModel,
        *,
        status_code: int | None = None,
        additional_headers: dict[str, t.Any] | None = None,
    ) -> None:
        self.data = data
        self.status_code = status_code
        self.additional_headers = additional_headers
        self.route: SpyRoute | None = None

    @property
    def response(self: te.Self) -> dict[str, t.Any]:
        headers = {
            "Content-Type": ContentType.JSON.value,
        }
        if self.additional_headers is not None:
            headers.update(self.additional_headers)

        if self.route is not None and self.route.response_class is not None and isinstance(self.data, dict):
            self.data = self.route.response_class.model_validate(self.data)

        if (
            self.route is not None
            and self.route.response_class is not None
            and isinstance(self.data, BaseModel)
            and not isinstance(self.data, self.route.response_class)
        ):
            self.data = self.route.response_class.model_validate(self.data.model_dump())

        if isinstance(self.data, BaseModel):
            self.data = self.data.model_dump()

        if self.status_code is not None:
            status_code = self.status_code
        elif self.route is None or self.route.status_code is None:
            status_code = 200
        else:
            status_code = self.route.status_code

        return {
            "statusCode": status_code,
            "body": json.dumps(self.data, cls=JSONEncoder, ensure_ascii=False),
            "headers": headers,
        }


class RAWResponse(BaseResponseSPY):
    def __init__(self: te.Self, response: dict[str, t.Any]) -> None:
        self.response_ = response

    @property
    def response(self: te.Self) -> dict[str, t.Any]:
        return self.response_


class ErrorResponse(BaseResponseSPY):
    def __init__(
        self: te.Self,
        errors: str | list[str],
        status_code: int = 400,
        additional_headers: dict[str, str] | None = None,
    ) -> None:
        self.errors = errors
        self.status_code = status_code
        self.additional_headers = additional_headers

    @property
    def response(self: te.Self) -> dict[str, t.Any]:
        headers = {
            "Content-Type": ContentType.JSON.value,
        }
        if self.additional_headers is not None:
            headers.update(self.additional_headers)

        if isinstance(self.errors, str):
            body = {"message": self.errors}
        elif isinstance(self.errors, list) and len(self.errors) == 1:
            body = {"message": self.errors[0]}
        else:
            body = {"errors": [{"message": error} for error in self.errors]}  # type: ignore

        return {
            "statusCode": self.status_code,
            "body": json.dumps(
                body,
                cls=JSONEncoder,
                ensure_ascii=False,
            ),
            "headers": headers,
        }
