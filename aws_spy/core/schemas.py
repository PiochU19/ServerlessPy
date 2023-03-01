import inspect
import os
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal, TypeVar, Union

from pydantic import BaseModel, Field, root_validator, validator
from typing_extensions import Self  # type: ignore

from aws_spy.core.exceptions import RouteDefinitionException
from aws_spy.core.schemas_utils import (
    ParamSchema,
    get_path_param_names,
    resolve_handler_args,
)

# pydantic_yaml won't be in the layer
try:
    from pydantic_yaml import YamlModel
except ImportError:

    class YamlModel(BaseModel):  # type: ignore
        ...


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
    SLS = "sls"


class SpyRoute(BaseModel):
    name: str
    path: str
    method: Methods
    handler: LH
    status_code: int
    tags: Union[list[str], None]
    summary: str
    description: Union[str, None]
    request_body: Union[type[BaseModel], None]
    response_class: Union[type[BaseModel], None]
    params: list[ParamSchema] = Field(default_factory=list)
    use_vpc: bool = Field(True)
    authorizer: Union[str, None] = Field(None)

    @root_validator(pre=True)
    def set_status_code(
        cls: type[Self],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        if values.get("status_code") is None:
            values["status_code"] = DEFAULT_STATUS_CODES[values["method"]]

        return values

    @validator("summary", pre=True)
    def set_summary(cls: type[Self], summary: Union[str, None]) -> str:
        return summary or "API endpoint"

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

        args = inspect.signature(handler).parameters
        args_count = len(args)
        # exclude lambdas event and context from count
        if "event" in args:
            args_count -= 1
        if "context" in args:
            args_count -= 1
        if handler_args.count != args_count:
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

        for attr_name in ("path", "query", "header"):
            values["params"] += [
                param for _, param in getattr(handler_args, attr_name).items()
            ]

        return values


class _CloudFormationRef(BaseModel):
    stack_name: str
    export_name: str

    def __str__(self: Self) -> str:
        return f"${{cf:{self.stack_name}-${{opt:stage}}.{self.export_name}}}"


class CloudFormationRef(_CloudFormationRef):
    def __new__(cls: type[Self], *args: list[Any], **kwargs: dict[str, Any]) -> str:  # type: ignore
        instance = _CloudFormationRef(**kwargs)
        return str(instance)


class _JSONFileRef(BaseModel):
    file_path: str
    field: str

    def __str__(self: Self) -> str:
        return f"${{file({self.file_path}):{self.field}}}"


class JSONFileRef(_JSONFileRef):
    def __new__(cls: type[Self], *args: list[Any], **kwargs: dict[str, Any]) -> str:  # type: ignore
        instance = _JSONFileRef(**kwargs)
        return str(instance)


def build_cognito_issue_url(
    user_pool_id: Union[str, CloudFormationRef, JSONFileRef]
) -> str:
    return f"https://cognito-idp.${{region}}.amazonaws.com/{user_pool_id}"


class Authorizers(BaseModel):
    type: Literal["jwt"] = "jwt"
    identitySource: str = "$request.header.Authorization"
    issuerUrl: str
    audience: list[Union[str, CloudFormationRef, JSONFileRef]]


class CORS(BaseModel):
    allowedHeaders: list[str]
    exposedResponseHeaders: list[str]
    allowedMethods: list[str]


class HTTPApi(BaseModel):
    authorizers: dict[str, Authorizers]
    cors: CORS


class VPC(BaseModel):
    securityGroupIds: list[Union[str, CloudFormationRef, JSONFileRef]]
    subnetIds: list[Union[str, CloudFormationRef, JSONFileRef]]


class Function(BaseModel):
    handler: str
    module: str
    events: list[dict[str, Any]]
    layers: list[Union[str, CloudFormationRef, JSONFileRef]]
    environment: Union[dict[str, Any], None] = Field(None)

    @staticmethod
    def generate_rel_path_for_function(route: SpyRoute) -> str:
        return os.path.relpath(
            Path(route.handler.__code__.co_filename), Path().resolve()
        )

    @classmethod
    def from_route(
        cls: type[Self], *, route: SpyRoute, path: str, method: Methods
    ) -> Self:
        rel_path = cls.generate_rel_path_for_function(route)
        http_api_event: dict[str, Any] = {"path": path, "method": method.upper()}
        if route.authorizer:
            http_api_event["authorizer"] = {"name": route.authorizer}

        return cls(
            handler=f'{rel_path.split(os.sep)[-1].replace(".py", "")}.{route.handler.__name__}',
            module="/".join(rel_path.split(os.sep)[:-1]),
            events=[{"httpApi": http_api_event}],
            layers=["xd"],
        )


class Provider(BaseModel):
    name: str = "aws"
    runtime: str = "python3.9"
    region: str
    role: Union[str, CloudFormationRef, JSONFileRef]
    httpApi: HTTPApi
    vpc: Union[VPC, None]


class ServerlessConfig(YamlModel):
    service: str
    custom: Union[dict[str, Any], None] = Field(None)
    plugins: list[str]
    configValidationMode: str = "error"
    provider: Provider
    package: dict[str, bool] = Field({"individually": True})
    functions: Union[dict[str, Function], None] = Field(None)

    @validator("plugins", pre=True)
    def set_default_plugins(
        cls: type[Self], value: Union[list[str], None]
    ) -> list[str]:
        value = value if value is not None else []
        value += [
            "serverless-python-requirements",
            "serverless-plugin-common-excludes",
            "serverless-plugin-include-dependencies",
        ]
        return list(set(value))
