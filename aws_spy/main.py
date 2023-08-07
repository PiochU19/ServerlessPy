import typing as t
from functools import wraps

import typing_extensions as te
from pydantic import BaseModel

from aws_spy.core.event_utils import export_params_from_event, export_request_body
from aws_spy.core.exceptions import (
    BaseSpyError,
    FunctionDefinitionError,
    RouteDefinitionError,
)
from aws_spy.core.responses import BaseResponseSPY
from aws_spy.core.schemas import (
    LH,
    Decorator,
    Methods,
    ServerlessConfig,
    SpyFunction,
    SpyRoute,
)
from aws_spy.responses import ErrorResponse, JSONResponse


class _SPY:
    routes: dict[str, dict[Methods, SpyRoute]]
    functions: list[SpyFunction]
    function_unique_ids: set[str]

    def __init__(self: te.Self, prefix: str | None = None) -> None:
        self.routes = {}
        self.functions = []
        self.function_unique_ids = set()
        if isinstance(prefix, str) and not prefix.startswith("/"):
            prefix = "/" + prefix
        self.prefix = prefix or ""

    def register_router(self: te.Self, router: t.Any) -> None:
        for path, methods in router.routes.items():
            for method, route in methods.items():
                self.add_route(path, method, route)
        for function in router.functions:
            self.add_function(function)

    def add_function(self: te.Self, function: SpyFunction) -> None:
        if function.name in self.function_unique_ids:
            msg = f"There is already {function.name} lambda registered."
            raise FunctionDefinitionError(msg)
        self.function_unique_ids.add(function.name)
        self.functions.append(function)

    def add_route(self: te.Self, path: str, method: Methods, route: SpyRoute) -> None:
        if not path.startswith("/"):
            path = "/" + path
        path = self.prefix + path
        if route.name in self.function_unique_ids:
            msg = f"There is already {route.name} lambda registered."
            raise RouteDefinitionError(msg)

        if path in self.routes.keys() and method in self.routes[path]:
            msg = f'There is already existing "{method.upper()}" method definition under "{path}" path.'
            raise RouteDefinitionError(msg)

        if path not in self.routes.keys():
            self.routes[path] = {}

        self.function_unique_ids.add(route.name)
        self.routes[path][method] = route

    def function(
        self: te.Self,
        name: str,
        *,
        response_class: type[BaseModel] | None = None,
        use_vpc: bool | None = False,
        skip_validation: bool | None = False,
        layers: list[str] | None = None,
    ) -> Decorator:
        def decorartor(handler: LH) -> LH:
            function = SpyFunction(
                name=name,
                handler=handler,
                response_class=response_class,
                use_vpc=use_vpc,
                skip_validation=skip_validation,
                layers=layers,
            )
            self.add_function(function)

            @wraps(handler)
            def wrapper(*args) -> dict[str, t.Any]:
                if function.skip_validation:
                    return handler(*args)
                return handler(*args)

            return wrapper

        return decorartor

    def route(
        self: te.Self,
        *,
        method: Methods,
        path: str,
        name: str,
        authorizer: str | None = None,
        response_class: type[BaseModel] | None = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        use_vpc: bool | None = None,
        skip_validation: bool | None = None,
        layers: list[str] | None = None,
    ) -> Decorator:
        def decorator(handler: LH) -> LH:
            route = SpyRoute(
                method=method,
                path=path,
                name=name,
                handler=handler,
                response_class=response_class,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                authorizer=authorizer,
                use_vpc=use_vpc,
                skip_validation=skip_validation,
                layers=layers,
            )
            self.add_route(path, method, route)

            @wraps(handler)
            def wrapper(*args) -> dict[str, t.Any]:
                if route.skip_validation:
                    return handler(*args)
                event = args[0]
                context = args[1]
                kwargs, errors = {}, []
                for params, errors_ in [
                    export_params_from_event(event.get("pathParameters"), route.path_params, "path"),
                    export_params_from_event(event.get("headers"), route.header_params, "header"),
                    export_params_from_event(event.get("queryStringParameters"), route.query_params, "query"),
                ]:
                    kwargs.update(params)
                    errors += errors_

                if route.request_body and route.request_body_arg_name:
                    request_body, request_body_errors = export_request_body(event.get("body", ""), route.request_body)
                    errors += request_body_errors
                    kwargs[route.request_body_arg_name] = request_body

                if errors:
                    return ErrorResponse(errors, status_code=422).response
                if route.add_event:
                    kwargs["event"] = event
                if route.add_context:
                    kwargs["context"] = context

                try:
                    return_obj = handler(**kwargs)
                except BaseSpyError as e:
                    return ErrorResponse(
                        e.error, status_code=e.status_code, additional_headers=e.additional_headers
                    ).response

                if not isinstance(return_obj, BaseResponseSPY):
                    return_obj = JSONResponse(return_obj)
                return_obj.route = route

                return return_obj.response

            return wrapper

        return decorator

    def get(
        self: te.Self,
        path: str,
        name: str,
        *,
        authorizer: str | None = None,
        response_class: type[BaseModel] | None = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        use_vpc: bool = True,
        skip_validation: bool = False,
        layers: list[str] | None = None,
    ) -> Decorator:
        return self.route(
            method=Methods.GET,
            path=path,
            name=name,
            authorizer=authorizer,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            use_vpc=use_vpc,
            skip_validation=skip_validation,
            layers=layers,
        )

    def post(
        self: te.Self,
        path: str,
        name: str,
        *,
        authorizer: str | None = None,
        response_class: type[BaseModel] | None = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        use_vpc: bool = True,
        skip_validation: bool = False,
        layers: list[str] | None = None,
    ) -> Decorator:
        return self.route(
            method=Methods.POST,
            path=path,
            name=name,
            authorizer=authorizer,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            use_vpc=use_vpc,
            skip_validation=skip_validation,
            layers=layers,
        )

    def delete(
        self: te.Self,
        path: str,
        name: str,
        *,
        authorizer: str | None = None,
        response_class: type[BaseModel] | None = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        use_vpc: bool = True,
        skip_validation: bool = False,
        layers: list[str] | None = None,
    ) -> Decorator:
        return self.route(
            method=Methods.DELETE,
            path=path,
            name=name,
            authorizer=authorizer,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            use_vpc=use_vpc,
            skip_validation=skip_validation,
            layers=layers,
        )

    def put(
        self: te.Self,
        path: str,
        name: str,
        *,
        authorizer: str | None = None,
        response_class: type[BaseModel] | None = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        use_vpc: bool = True,
        skip_validation: bool = False,
        layers: list[str] | None = None,
    ) -> Decorator:
        return self.route(
            method=Methods.PUT,
            path=path,
            name=name,
            authorizer=authorizer,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            use_vpc=use_vpc,
            skip_validation=skip_validation,
            layers=layers,
        )

    def patch(
        self: te.Self,
        path: str,
        name: str,
        *,
        authorizer: str | None = None,
        response_class: type[BaseModel] | None = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        use_vpc: bool = True,
        skip_validation: bool = False,
        layers: list[str] | None = None,
    ) -> Decorator:
        return self.route(
            method=Methods.PATCH,
            path=path,
            name=name,
            authorizer=authorizer,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            use_vpc=use_vpc,
            skip_validation=skip_validation,
            layers=layers,
        )


class SpyAPI(_SPY):
    def __init__(
        self: te.Self,
        *,
        config: ServerlessConfig,
        environment: dict[str, t.Any] | None = None,
        title: str | None = None,
        version: str | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(prefix)

        self.title = title or "My API"
        self.version = version or "v0.0.1"
        self.config: ServerlessConfig = config
        self.environment = environment


class SpyRouter(_SPY):
    def __init__(self: te.Self, prefix: str | None = None) -> None:
        super().__init__(prefix)
