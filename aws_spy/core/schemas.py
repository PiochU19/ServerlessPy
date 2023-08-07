import inspect
import os
import typing as t
from collections.abc import Callable
from enum import Enum
from pathlib import Path

import typing_extensions as te
from pydantic import BaseModel, Field, field_validator, model_validator

from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.schemas_utils import (
    ParamSchema,
    get_path_param_names,
    resolve_handler_args,
)

# from aws_spy.dependencies import DependencySchema, get_dependencies


LHReturnType = t.TypeVar("LHReturnType")
LH = Callable[..., LHReturnType]  # Lambda Handler
Decorator = Callable[[LH], LH]
MANDATORY_PLUGINS = [
    "serverless-python-requirements",
    "serverless-plugin-common-excludes",
    "serverless-plugin-include-dependencies",
]


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
    # OPENAPI = "openapi"
    SLS = "sls"


class _CloudFormationRef(BaseModel):
    stack_name: str
    export_name: str

    def __str__(self: te.Self) -> str:
        return f"${{cf:{self.stack_name}-${{opt:stage}}.{self.export_name}}}"


class CloudFormationRef(_CloudFormationRef):
    def __new__(cls: type[te.Self], stack_name: str, export_name: str) -> str:  # type: ignore
        instance = _CloudFormationRef(stack_name=stack_name, export_name=export_name)
        return str(instance)


class _JSONFileRef(BaseModel):
    file_path: str
    field: str

    def __str__(self: te.Self) -> str:
        return f"${{file({self.file_path}):{self.field}}}"


class JSONFileRef(_JSONFileRef):
    def __new__(cls: type[te.Self], file_path: str, field: str) -> str:  # type: ignore
        instance = _JSONFileRef(file_path=file_path, field=field)
        return str(instance)


class SpyBaseModel(BaseModel):
    name: str
    handler: LH
    use_vpc: bool = Field(True)
    layers: list[str | CloudFormationRef | JSONFileRef] | None = Field(default_factory=list)
    add_event: bool = Field(default=False)
    add_context: bool = Field(default=False)
    skip_validation: bool = Field(default=False)
    request_body_arg_name: str | None = Field(None)
    request_body: type[BaseModel] | None = Field(None)
    response_class: type[BaseModel] | None = Field(None)

    @field_validator("layers", mode="before")
    def set_layers(cls: type[te.Self], layers: list[str] | None) -> list[str]:  # type: ignore  # noqa: N805
        return layers or []


class SpyFunction(SpyBaseModel):
    ...


class SpyRoute(SpyBaseModel):
    path: str
    method: Methods
    status_code: int
    authorizer: str | None = Field(None)
    tags: list[str] | None = Field(None)
    summary: str = Field("API endpoint")
    description: str | None = Field(None)
    header_params: list[ParamSchema] = Field(default_factory=list)
    path_params: list[ParamSchema] = Field(default_factory=list)
    query_params: list[ParamSchema] = Field(default_factory=list)
    # dependencies: list[DependencySchema] = Field(default_factory=list)

    @model_validator(mode="before")
    def set_status_code(  # type: ignore
        cls: type[te.Self],  # noqa: N805
        values: dict[str, t.Any],
    ) -> dict[str, t.Any]:
        if values.get("status_code") is None:
            values["status_code"] = DEFAULT_STATUS_CODES[values["method"]]

        return values

    @field_validator("summary", mode="before")
    def set_summary(cls: type[te.Self], summary: str | None) -> str:  # type: ignore  # noqa: N805
        return summary or "API endpoint"

    @model_validator(mode="after")
    def validate_handler_params(  # type: ignore
        cls: type[te.Self],  # noqa: N805
        model: te.Self,
    ) -> dict[str, t.Any]:
        method: Methods = model.method
        path: str = model.path
        handler: LH = model.handler

        path_params = get_path_param_names(path)
        handler_args = resolve_handler_args(handler)
        # values["dependencies"] = get_dependencies(handler)

        args = inspect.signature(handler).parameters
        args_count = len(args)
        # exclude lambdas event and context from count
        if "event" in args:
            model.add_event = True
            args_count -= 1
        if "context" in args:
            model.add_context = True
            args_count -= 1
        if handler_args.count != args_count and not model.skip_validation:
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

        if handler_args.request_body:
            model.request_body = handler_args.request_body
            model.request_body_arg_name = handler_args.request_body_arg_name

        for attr_name in ("path", "query", "header"):
            setattr(
                model,
                f"{attr_name}_params",
                getattr(model, f"{attr_name}_params")
                + [param for _, param in getattr(handler_args, attr_name).items()],
            )

        return model


def build_cognito_issue_url(user_pool_id: str | CloudFormationRef | JSONFileRef) -> str:
    return f"https://cognito-idp.${{region}}.amazonaws.com/{user_pool_id}"


class Authorizer(BaseModel):
    type: t.Literal["jwt"] = Field("jwt", frozen=True)  # noqa: A003
    identitySource: str = "$request.header.Authorization"  # noqa: N815
    issuerUrl: str  # noqa: N815
    audience: list[str | CloudFormationRef | JSONFileRef]


class CORS(BaseModel):
    allowedHeaders: list[str]  # noqa: N815
    exposedResponseHeaders: list[str]  # noqa: N815
    allowedMethods: list[str]  # noqa: N815
    allowedOrigins: list[str]  # noqa: N815


class HTTPApi(BaseModel):
    authorizers: dict[str, Authorizer] | None = Field(None)
    cors: CORS | None = Field(None)


class VPC(BaseModel):
    securityGroupIds: list[str | CloudFormationRef | JSONFileRef]  # noqa: N815
    subnetIds: list[str | CloudFormationRef | JSONFileRef]  # noqa: N815


class Function(BaseModel):
    handler: str
    module: str
    events: list[dict[str, t.Any]] | None = Field(None)
    layers: list[str | CloudFormationRef | JSONFileRef]
    environment: dict[str, t.Any] | None = Field(None)

    @staticmethod
    def generate_rel_path_for_function(route: SpyRoute) -> str:
        return os.path.relpath(Path(route.handler.__code__.co_filename), Path().resolve())

    @staticmethod
    def build_handler_string(relative_path: str, function_name: str) -> str:
        return relative_path.split(os.sep)[-1].replace(".py", "") + f".{function_name}"

    @staticmethod
    def build_module_string(relative_path: str) -> str:
        return "/".join(relative_path.split(os.sep)[:-1])

    @staticmethod
    def build_layers(
        layers: list[str | CloudFormationRef | JSONFileRef],
    ) -> list[str | CloudFormationRef | JSONFileRef]:
        return list(
            set(
                [  # noqa: RUF005
                    CloudFormationRef(
                        stack_name="spy-layer",
                        export_name="ServerlesspyLayerExport",
                    )
                ]
                + layers,
            )
        )

    @classmethod
    def from_function(cls: type[te.Self], *, function: SpyFunction) -> te.Self:  # type: ignore
        rel_path = cls.generate_rel_path_for_function(function)
        return cls(
            handler=cls.build_handler_string(rel_path, function.handler.__name__),
            module=cls.build_module_string(rel_path),
            layers=cls.build_layers(function.layers),  # type: ignore
        )

    @classmethod
    def from_route(cls: type[te.Self], *, route: SpyRoute, path: str, method: Methods) -> te.Self:  # type: ignore
        rel_path = cls.generate_rel_path_for_function(route)
        http_api_event: dict[str, t.Any] = {"path": path, "method": method.upper()}
        if route.authorizer:
            http_api_event["authorizer"] = {"name": route.authorizer}

        return cls(
            handler=cls.build_handler_string(rel_path, route.handler.__name__),
            module=cls.build_module_string(rel_path),
            events=[{"httpApi": http_api_event}],
            layers=cls.build_layers(route.layers),  # type: ignore
        )


class Provider(BaseModel):
    name: t.Literal["aws"] = Field("aws", frozen=True)
    runtime: t.Literal["python3.10"] = Field("python3.10", frozen=True)
    region: str = "eu-central-1"
    architecture: t.Literal["arm64", "x86_64"] = Field("arm64", frozen=True)  # pydantic_core
    role: str | CloudFormationRef | JSONFileRef | None = Field(None)
    httpApi: HTTPApi | None = Field(None)  # noqa: N815
    vpc: VPC | None = Field(None)


class ServerlessConfig(BaseModel):
    service: str
    custom: dict[str, t.Any] | None = Field(None)
    plugins: list[str]
    configValidationMode: t.Literal["error", "warn"] = Field("warn", frozen=True)  # noqa: N815
    provider: Provider
    package: dict[str, bool] = Field({"individually": True})
    functions: dict[str, Function] | None = Field(None)

    @model_validator(mode="before")
    def set_default_plugins(  # type: ignore
        cls: type[te.Self],  # noqa: N805
        values: dict[str, t.Any],
    ) -> dict[str, t.Any]:
        provided_plugins = values.get("plugins")
        provided_plugins = provided_plugins if provided_plugins is not None else []
        values["plugins"] = list(set(provided_plugins + MANDATORY_PLUGINS))

        return values
