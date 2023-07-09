import inspect
import re
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from aws_spy.core import types
from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.params import Param, ParamType

LH = TypeVar("LH", bound=Callable[..., Any])


class ParamSchema(BaseModel):
    name: str
    arg_name: str
    in_: Param
    annotation: type
    is_required: bool
    enum: list[str] | None

    class Config:
        arbitrary_types_allowed = True


class HandlerArgs(BaseModel):
    query: dict[str, ParamSchema]
    path: dict[str, ParamSchema]
    header: dict[str, ParamSchema]
    request_body: type[BaseModel] | None
    request_body_arg_name: str | None

    @property
    def count(self: Self) -> int:
        return len(self.query) + len(self.path) + len(self.header) + (1 if self.request_body is not None else 0)


def _is_request_body(arg) -> bool:
    return arg.default is inspect.Parameter.empty and issubclass(arg.annotation, BaseModel)


def _is_param(arg) -> bool:
    return isinstance(arg.default, Param)


def resolve_handler_args(handler: LH) -> HandlerArgs:
    params: dict[ParamType, dict[str, ParamSchema]] = {
        ParamType.HEADER: {},
        ParamType.PATH: {},
        ParamType.QUERY: {},
    }
    request_body = None
    request_body_arg_name = None
    for arg_name, arg_value in inspect.signature(handler).parameters.items():
        if _is_request_body(arg_value) and request_body is None:
            request_body = arg_value.annotation
            request_body_arg_name = arg_name
            continue
        if _is_param(arg_value):
            param: Param = arg_value.default
            param_name = param.name if param.name is not None else arg_name
            if param_name in params[param.in_].keys():
                msg = f'{handler.__name__} expects two same {param.in_} params: "{param_name}"!'
                raise RouteDefinitionError(msg)

            enum = None
            is_required = types.is_type_required(arg_value.annotation)
            annotation = arg_value.annotation if is_required else types.get_type_from_optional(arg_value.annotation)
            if issubclass(annotation, Enum):
                enum = [e.value for e in annotation]

            params[param.in_][param_name] = ParamSchema(
                name=param_name,
                in_=arg_value.default,
                arg_name=arg_name,
                annotation=annotation,
                enum=enum,
                is_required=is_required,
            )

    return HandlerArgs(
        query=params[ParamType.QUERY],
        path=params[ParamType.PATH],
        header=params[ParamType.HEADER],
        request_body=request_body,
        request_body_arg_name=request_body_arg_name,
    )


def get_path_param_names(path: str) -> set[str]:
    return set(re.findall("{(.*?)}", path))
