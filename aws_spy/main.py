from functools import wraps
from typing import Any

from pydantic import BaseModel
from typing_extensions import Self

from aws_spy.core.event_utils import export_params_from_event, export_request_body
from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.responses import BaseResponseSPY
from aws_spy.core.schemas import LH, Decorator, Methods, ServerlessConfig, SpyRoute
from aws_spy.responses import ErrorResponse, JSONResponse


class _SPY:
    routes: dict[str, dict[Methods, SpyRoute]]
    function_unique_ids: set[str]

    def __init__(self: Self, prefix: str | None = None) -> None:
        self.routes = {}
        self.function_unique_ids = set()
        if isinstance(prefix, str) and not prefix.startswith("/"):
            prefix = "/" + prefix
        self.prefix = prefix or ""

    def register_router(self: Self, router: Any) -> None:
        for path, methods in router.routes.items():
            for method, route in methods.items():
                self.add_route(path, method, route)

    def add_route(self: Self, path: str, method: Methods, route: SpyRoute) -> None:
        if not path.startswith("/"):
            path = "/" + path
        path = self.prefix + path
        if route.name in self.function_unique_ids:
            msg = f"There is already {route.name} lambda registered."
            raise RouteDefinitionError(msg)

        if path in self.routes.keys() and method in self.routes[path]:
            msg = f'There is already existing "{method.upper()}" method definition under "{{path}}" path.'
            raise RouteDefinitionError(msg)

        if path not in self.routes.keys():
            self.routes[path] = {}

        self.function_unique_ids.add(route.name)
        self.routes[path][method] = route

    def route(
        self: Self,
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
            )
            self.add_route(path, method, route)

            @wraps(handler)
            def wrapper(*args) -> dict[str, Any]:
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

                return_obj = handler(**kwargs)
                if not isinstance(return_obj, BaseResponseSPY):
                    return_obj = JSONResponse(return_obj)
                return_obj.route = route

                return return_obj.response

            return wrapper

        return decorator

    def get(
        self: Self,
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
        )

    def post(
        self: Self,
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
        )

    def delete(
        self: Self,
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
        )

    def put(
        self: Self,
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
        )

    def patch(
        self: Self,
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
        )


class SpyAPI(_SPY):
    def __init__(
        self: Self,
        *,
        config: ServerlessConfig,
        environment: dict[str, Any] | None = None,
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
    def __init__(self: Self, prefix: str | None = None) -> None:
        super().__init__(prefix)
