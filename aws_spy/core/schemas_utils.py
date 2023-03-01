import inspect
import re
from typing import Any, Callable, Set, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from aws_spy.core.exceptions import RouteDefinitionException
from aws_spy.core.params import Param, ParamType

LH = TypeVar("LH", bound=Callable[..., Any])


class ParamSchema(BaseModel):
    name: str
    arg_name: str
    in_: Param
    annotation: type

    class Config:
        arbitrary_types_allowed = True


class HandlerArgs(BaseModel):
    query: dict[str, ParamSchema]
    path: dict[str, ParamSchema]
    header: dict[str, ParamSchema]
    request_body: Union[type[BaseModel], None]

    @property
    def count(self: Self) -> int:
        return (
            len(self.query)
            + len(self.path)
            + len(self.header)
            + (1 if self.request_body is not None else 0)
        )


def _is_request_body(arg) -> bool:
    return arg.default is inspect.Parameter.empty and issubclass(
        arg.annotation, BaseModel
    )


def _is_param(arg) -> bool:
    return isinstance(arg.default, Param)


def resolve_handler_args(handler: LH) -> HandlerArgs:
    params: dict[ParamType, dict[str, ParamSchema]] = {
        ParamType.HEADER: {},
        ParamType.PATH: {},
        ParamType.QUERY: {},
    }
    request_body = None

    for arg_name, arg_value in inspect.signature(handler).parameters.items():
        if _is_request_body(arg_value) and request_body is None:
            request_body = arg_value.annotation
            continue
        if _is_param(arg_value):
            param: Param = arg_value.default
            param_name = param.name if param.name is not None else arg_name
            if param_name in params[param.in_].keys():
                raise RouteDefinitionException(
                    f'{handler.__name__} expects two same {param.in_} params: "{param_name}"!'
                )

            params[param.in_][param_name] = ParamSchema(
                name=param_name,
                in_=arg_value.default,
                arg_name=arg_name,
                annotation=arg_value.annotation,
            )

    return HandlerArgs(
        query=params[ParamType.QUERY],
        path=params[ParamType.PATH],
        header=params[ParamType.HEADER],
        request_body=request_body,
    )


def get_path_param_names(path: str) -> Set[str]:
    return set(re.findall("{(.*?)}", path))
