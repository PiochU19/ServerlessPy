import inspect
from functools import wraps
from typing import Any, Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from aws_spy.core.event_utils import get_path_params
from aws_spy.core.exceptions import RouteDefinitionException
from aws_spy.core.responses import BaseResponseSPY
from aws_spy.core.schemas import LH, Decorator, Methods, ServerlessConfig, SpyRoute
from aws_spy.core.schemas_utils import resolve_handler_args
from aws_spy.responses import ErrorResponse, JSONResponse


class _SPY:
    routes: dict[str, dict[Methods, SpyRoute]]
    function_unique_ids: set[str]

    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        self.routes = {}
        self.function_unique_ids = set()
        if isinstance(prefix, str) and not prefix.startswith("/"):
            prefix = "/" + prefix
        self.prefix = prefix or ""

    def register_router(self: Self, router: Self) -> None:
        for path, methods in router.routes.items():
            for method, route in methods.items():
                self.add_route(path, method, route)

    def add_route(self: Self, path: str, method: Methods, route: SpyRoute) -> None:
        if not path.startswith("/"):
            path = "/" + path
        path = self.prefix + path
        if route.name in self.function_unique_ids:
            raise RouteDefinitionException(
                f"There is already {route.name} lambda registered."
            )

        if path in self.routes.keys() and method in self.routes[path]:
            raise RouteDefinitionException(
                f'There is already existing "{method.upper()}" method definition under "{path}" path.'
            )

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
        authorizer: Union[str, None],
        response_class: Union[type[BaseModel], None],
        status_code: Union[int, None],
        tags: Union[list[str], None],
        summary: Union[str, None],
        description: Union[str, None],
        use_vpc: bool,
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
            )
            self.add_route(path, method, route)

            @wraps(handler)
            def wrapper(*args) -> dict[str, Any]:
                event = args[0]
                context = args[1]
                kwargs, errors = {}, []
                inspected_args = inspect.signature(handler).parameters
                handler_args = resolve_handler_args(handler)
                for params, errors_ in [get_path_params(event, handler_args.path)]:
                    kwargs.update(params)
                    errors += errors_

                if errors:
                    return ErrorResponse(errors, status_code=422).response
                if "event" in inspected_args:
                    kwargs["event"] = event
                if "context" in inspected_args:
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
        authorizer: Union[str, None] = None,
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        summary: Union[str, None] = None,
        description: Union[str, None] = None,
        use_vpc: bool = True,
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
        )

    def post(
        self: Self,
        path: str,
        name: str,
        *,
        authorizer: Union[str, None] = None,
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        summary: Union[str, None] = None,
        description: Union[str, None] = None,
        use_vpc: bool = True,
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
        )

    def delete(
        self: Self,
        path: str,
        name: str,
        *,
        authorizer: Union[str, None] = None,
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        summary: Union[str, None] = None,
        description: Union[str, None] = None,
        use_vpc: bool = True,
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
        )

    def put(
        self: Self,
        path: str,
        name: str,
        *,
        authorizer: Union[str, None] = None,
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        summary: Union[str, None] = None,
        description: Union[str, None] = None,
        use_vpc: bool = True,
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
        )

    def patch(
        self: Self,
        path: str,
        name: str,
        *,
        authorizer: Union[str, None] = None,
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        summary: Union[str, None] = None,
        description: Union[str, None] = None,
        use_vpc: bool = True,
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
        )


class SpyAPI(_SPY):
    def __init__(
        self: Self,
        *,
        config: ServerlessConfig,
        environment: Union[dict[str, Any], None] = None,
        title: Union[str, None] = None,
        version: Union[str, None] = None,
        prefix: Union[str, None] = None,
    ) -> None:
        super().__init__(prefix)

        self.title = title or "My API"
        self.version = version or "v0.0.1"
        self.config = config
        self.environment = environment


class SpyRouter(_SPY):
    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        super().__init__(prefix)
