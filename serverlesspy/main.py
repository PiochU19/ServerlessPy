from functools import wraps
from typing import Any, Callable, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from serverlesspy.core import METHODS

LRT = TypeVar("LRT")  # Lambda Return Type
LH = Callable[..., LRT]  # Lambda Handler
Decorator = Callable[[LH], LH]


class SpyRoute(BaseModel):
    method: METHODS
    path: str
    response_class: Union[BaseModel, None]
    status_code: Union[int, None]
    tags: Union[list[str], None]
    name: Union[str, None]
    description: Union[str, None]


class _SPY:
    routes: list[SpyRoute]

    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        self.routes = []
        if isinstance(prefix, str) and not prefix.startswith("/"):
            prefix = "/" + prefix
        self.prefix = prefix or ""

    def register_router(self: Self, router: Self) -> None:
        for route in router.routes:
            route.path = self.prefix + route.path
        self.routes += router.routes

    def add_route(self: Self, route: SpyRoute) -> None:
        if not route.path.startswith("/"):
            route.path = "/" + route.path
        route.path = self.prefix + route.path

        self.routes.append(route)

    def route(
        self: Self,
        *,
        method: METHODS,
        path: str,
        response_class: Union[int, None],
        status_code: Union[int, None],
        tags: Union[list[str], None],
        name: Union[str, None],
        description: Union[str, None],
    ) -> Decorator:
        self.add_route(
            SpyRoute(
                method=method,
                path=path,
                response_class=response_class,
                status_code=status_code,
                tags=tags,
                name=name,
                description=description,
            )
        )

        def decorator(func: LH) -> LH:
            @wraps(func)
            def wrapper(*args, **kwargs) -> LRT:
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get(
        self: Self,
        path: str,
        *,
        response_class: Union[int, None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ) -> Decorator:
        return self.route(
            method="get",
            path=path,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            name=name,
            description=description,
        )

    def post(
        self: Self,
        path: str,
        *,
        response_class: Union[int, None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ) -> Decorator:
        return self.route(
            method="post",
            path=path,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            name=name,
            description=description,
        )


class SpyAPI(_SPY):
    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        super().__init__(prefix)

    def deploy_layer(self: Self) -> None:
        ...

    def generate_openapi(self: Self) -> None:
        ...


class SpyRouter(_SPY):
    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        super().__init__(prefix)
