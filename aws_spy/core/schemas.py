import inspect
import os
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, root_validator, validator
from typing_extensions import Self  # type: ignore

from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.schemas_utils import (
    ParamSchema,
    get_path_param_names,
    resolve_handler_args,
)

# from aws_spy.dependencies import DependencySchema, get_dependencies

# pydantic_yaml won't be in the layer
try:
    from pydantic_yaml import YamlModel  # type: ignore
except ImportError:  # pragma: no cover

    class YamlModel(BaseModel):  # type: ignore
        ...


LHReturnType = TypeVar("LHReturnType")
LH = Callable[..., LHReturnType]  # Lambda Handler
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
    tags: list[str] | None
    summary: str = Field("API endpoint")
    description: str | None
    request_body_arg_name: str | None
    request_body: type[BaseModel] | None
    response_class: type[BaseModel] | None
    header_params: list[ParamSchema] = Field(default_factory=list)
    path_params: list[ParamSchema] = Field(default_factory=list)
    query_params: list[ParamSchema] = Field(default_factory=list)
    # dependencies: list[DependencySchema] = Field(default_factory=list)
    use_vpc: bool = Field(True)
    authorizer: str | None = Field(None)
    layers: list[str] = Field(default_factory=list)
    add_event: bool = Field(default=False)
    add_context: bool = Field(default=False)
    skip_validation: bool = Field(default=False)

    @root_validator(pre=True)
    def set_status_code(  # type: ignore
        cls: type[Self],  # noqa: N805
        values: dict[str, Any],
    ) -> dict[str, Any]:
        if values.get("status_code") is None:
            values["status_code"] = DEFAULT_STATUS_CODES[values["method"]]

        return values

    @validator("summary", pre=True)
    def set_summary(cls: type[Self], summary: str | None) -> str:  # type: ignore  # noqa: N805
        return summary or "API endpoint"

    @root_validator
    def validate_handler_params(  # type: ignore
        cls: type[Self],  # noqa: N805
        values: dict[str, Any],
    ) -> dict[str, Any]:
        method: Methods = values["method"]
        path: str = values["path"]
        handler: LH = values["handler"]

        path_params = get_path_param_names(path)
        handler_args = resolve_handler_args(handler)
        # values["dependencies"] = get_dependencies(handler)

        args = inspect.signature(handler).parameters
        args_count = len(args)
        # exclude lambdas event and context from count
        if "event" in args:
            values["add_event"] = True
            args_count -= 1
        if "context" in args:
            values["add_context"] = True
            args_count -= 1
        if handler_args.count != args_count and not values["skip_validation"]:
            msg = f'Unrecognized params for {method.upper()} method on "{path}" path!'
            raise RouteDefinitionError(msg)

        for path_param in path_params:
            if path_param not in handler_args.path.keys():
                msg = f"You did not specify {path_param} in your handler arguments!"
                raise RouteDefinitionError(msg)

        for path_arg in handler_args.path.keys():
            if path_arg not in path_params:
                msg = f'Your {path_arg} path parameter is missing in {method.upper()} method on "{path}" path!'
                raise RouteDefinitionError(msg)

        if method in (Methods.GET, Methods.DELETE) and handler_args.request_body:
            msg = f'{method.upper()} method on "{path}" cannot have request body!'
            raise RouteDefinitionError(msg)

        if handler_args.request_body:
            values["request_body"] = handler_args.request_body
            values["request_body_arg_name"] = handler_args.request_body_arg_name

        for attr_name in ("path", "query", "header"):
            values[f"{attr_name}_params"] += [param for _, param in getattr(handler_args, attr_name).items()]

        return values


class _CloudFormationRef(BaseModel):
    stack_name: str
    export_name: str

    def __str__(self: Self) -> str:
        return f"${{cf:{self.stack_name}-${{opt:stage}}.{self.export_name}}}"


class CloudFormationRef(_CloudFormationRef):
    def __new__(cls: type[Self], stack_name: str, export_name: str) -> str:  # type: ignore
        instance = _CloudFormationRef(stack_name=stack_name, export_name=export_name)
        return str(instance)


class _JSONFileRef(BaseModel):
    file_path: str
    field: str

    def __str__(self: Self) -> str:
        return f"${{file({self.file_path}):{self.field}}}"


class JSONFileRef(_JSONFileRef):
    def __new__(cls: type[Self], file_path: str, field: str) -> str:  # type: ignore
        instance = _JSONFileRef(file_path=file_path, field=field)
        return str(instance)


def build_cognito_issue_url(user_pool_id: str | CloudFormationRef | JSONFileRef) -> str:
    return f"https://cognito-idp.${{region}}.amazonaws.com/{user_pool_id}"


class Authorizer(BaseModel):
    type: Literal["jwt"] = "jwt"  # noqa: A003
    identitySource: str = "$request.header.Authorization"  # noqa: N815
    issuerUrl: str  # noqa: N815
    audience: list[str | CloudFormationRef | JSONFileRef]


class CORS(BaseModel):
    allowedHeaders: list[str]  # noqa: N815
    exposedResponseHeaders: list[str]  # noqa: N815
    allowedMethods: list[str]  # noqa: N815
    allowedOrigins: list[str]  # noqa: N815


class HTTPApi(BaseModel):
    authorizers: dict[str, Authorizer]
    cors: CORS


class VPC(BaseModel):
    securityGroupIds: list[str | CloudFormationRef | JSONFileRef]  # noqa: N815
    subnetIds: list[str | CloudFormationRef | JSONFileRef]  # noqa: N815


class Function(BaseModel):
    handler: str
    module: str
    events: list[dict[str, Any]]
    layers: list[str | CloudFormationRef | JSONFileRef]
    environment: dict[str, Any] | None = Field(None)

    @staticmethod
    def generate_rel_path_for_function(route: SpyRoute) -> str:
        return os.path.relpath(Path(route.handler.__code__.co_filename), Path().resolve())

    @classmethod
    def from_route(cls: type[Self], *, route: SpyRoute, path: str, method: Methods) -> Self:  # type: ignore
        rel_path = cls.generate_rel_path_for_function(route)
        http_api_event: dict[str, Any] = {"path": path, "method": method.upper()}
        if route.authorizer:
            http_api_event["authorizer"] = {"name": route.authorizer}

        return cls(
            handler=(f'{rel_path.split(os.sep)[-1].replace(".py", "")}' f".{route.handler.__name__}"),  # noqa: ISC001
            module="/".join(rel_path.split(os.sep)[:-1]),
            events=[{"httpApi": http_api_event}],
            layers=list(
                set(
                    [
                        CloudFormationRef(
                            stack_name="spy-layer",
                            export_name="ServerlesspyLayerExport",
                        )
                    ],
                    *route.layers,  # type: ignore
                )
            ),
        )


class Provider(BaseModel):
    name: str = "aws"
    runtime: str = "python3.9"
    region: str
    role: str | CloudFormationRef | JSONFileRef
    httpApi: HTTPApi  # noqa: N815
    vpc: VPC | None


class ServerlessConfig(YamlModel):
    service: str
    custom: dict[str, Any] | None = Field(None)
    plugins: list[str]
    configValidationMode: str = "error"  # noqa: N815
    provider: Provider
    package: dict[str, bool] = Field({"individually": True})
    functions: dict[str, Function] | None = Field(None)

    @validator("plugins", pre=True)
    def set_default_plugins(cls: type[Self], value: list[str] | None) -> list[str]:  # type: ignore  # noqa: N805
        value = value if value is not None else []
        value += [
            "serverless-python-requirements",
            "serverless-plugin-common-excludes",
            "serverless-plugin-include-dependencies",
        ]
        return list(set(value))
