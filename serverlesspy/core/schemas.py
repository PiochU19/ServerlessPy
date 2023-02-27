from enum import Enum
from typing import Any, Callable, TypeVar, Union

from pydantic import BaseModel, Field, root_validator, validator
from typing_extensions import Self  # type: ignore

from serverlesspy.core.exceptions import RouteDefinitionException
from serverlesspy.core.schemas_utils import (
    ParamSchema,
    get_path_param_names,
    resolve_handler_args,
)

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
    path_params: list[ParamSchema] = Field(default_factory=list)
    query_string_params: list[ParamSchema] = Field(default_factory=list)
    headers: list[ParamSchema] = Field(default_factory=list)

    @root_validator(pre=True)
    def set_status_code(
        cls: type[Self],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        if values.get("status_code") is None:
            values["status_code"] = DEFAULT_STATUS_CODES[values["method"]]

        return values

    @validator("summary", pre=True)
    def set_summary(cls: type[Self], name: Union[str, None]) -> str:
        return name or "API endpoint"

    @root_validator
    def validate_handler_params(
        cls: type[Self],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        method: Methods = values["method"]
        path: str = values["path"]
        handler: LH = values["handler"]

        path_params = get_path_param_names(path)
        handler_args = resolve_handler_args(handler)
        if handler_args.count != len(handler.__annotations__):
            raise RouteDefinitionException(
                f'Unrecognized params for {method.upper()} method on "{path}" path!'
            )

        for path_param in path_params:
            if path_param not in handler_args.path.keys():
                raise RouteDefinitionException(
                    f"You did not specify {path_param} in your handler arguments!"
                )

        for path_arg in handler_args.path.keys():
            if path_arg not in path_params:
                raise RouteDefinitionException(
                    f'Your {path_arg} path parameter is missing in {method.upper()} method on "{path} path!"'
                )

        if method == Methods.POST and handler_args.query:
            raise RouteDefinitionException("POST method doesn't support query params!")

        if method in (Methods.GET, Methods.DELETE) and handler_args.request_body:
            raise RouteDefinitionException(
                f'{method.upper()} method on "{path}" cannot have request body!'
            )

        if handler_args.request_body:
            values["request_body"] = handler_args.request_body

        for field_name, attr_name in (
            ("path_params", "path"),
            ("query_string_params", "query"),
            ("headers", "header"),
        ):
            values[field_name] = [
                param for _, param in getattr(handler_args, attr_name).items()
            ]

        return values
