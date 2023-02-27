import inspect
from enum import Enum
from typing import Any, Callable, TypeVar, Union

from pydantic import BaseModel, root_validator, validator
from typing_extensions import Self  # type: ignore

from serverlesspy.core.exceptions import RouteDefinitionException

LRT = TypeVar("LRT")  # Lambda Return Type
LH = Callable[..., LRT]  # Lambda Handler
Decorator = Callable[[LH], LH]


class Methods(str, Enum):
    GET = "get"
    POST = "post"
    DELETE = "delete"
    PUT = "put"
    PATCH = "patch"


DEFAULT_STATUS_CODES = {
    Methods.GET: "200",
    Methods.POST: "201",
    Methods.DELETE: "204",
    Methods.PUT: "200",
    Methods.PATCH: "200",
}


class Functions(str, Enum):
    LAYER = "layer"
    OPENAPI = "openapi"


class SpyRoute(BaseModel):
    path: str
    method: Methods
    handler: LH
    status_code: int
    tags: Union[list[str], None]
    summary: str
    description: Union[str, None]
    request_body: Union[type[BaseModel], None]
    response_class: Union[type[BaseModel], None]
    path_params: Union[list[str], None]
    query_string_params: Union[list[str], None]

    @root_validator(pre=True)
    def set_status_code(
        cls: type[Self],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        if values.get("status_code") is None:
            values["status_code"] = DEFAULT_STATUS_CODES[values["method"]]

        return values

    @root_validator
    def get_request_body_from_handler(
        cls: type[Self],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        handler: LH = values["handler"]
        method: Methods = values["method"]
        path: str = values["path"]

        bm_positional_args = []
        for _, arg in inspect.signature(handler).parameters.items():
            if arg.default is inspect.Parameter.empty and issubclass(
                arg.annotation, BaseModel
            ):
                bm_positional_args.append(arg.annotation)

        if method in (Methods.GET, Methods.DELETE) and bm_positional_args:
            raise RouteDefinitionException(
                f'{method.upper()} method on "{path}" cannot have request body!'
            )

        if len(bm_positional_args) > 1:
            raise RouteDefinitionException(
                "Only one request body definition allowed!\n"
                f'{method.upper()} on "{path}"'
            )

        if bm_positional_args:
            values["request_body"] = bm_positional_args[0]

        return values

    @validator("summary", pre=True)
    def set_summary(cls: type[Self], name: Union[str, None]) -> str:
        return name or "API endpoint"
