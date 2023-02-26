from functools import wraps
from typing import Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from serverlesspy.core.exceptions import RouteDefinitionException
from serverlesspy.core.schemas import LH, LRT, Decorator, Methods, SpyRoute


class _SPY:
    routes: dict[str, dict[Methods, SpyRoute]]

    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        self.routes = {}
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

        if path in self.routes.keys() and method in self.routes[path]:
            raise RouteDefinitionException(
                f'There is already existing "{method.upper()}" method definition under "{path}" path.'
            )

        if path not in self.routes.keys():
            self.routes[path] = {}

        self.routes[path][method] = route

    def route(
        self: Self,
        *,
        method: Methods,
        path: str,
        response_class: Union[type[BaseModel], None],
        status_code: Union[int, None],
        tags: Union[list[str], None],
        name: Union[str, None],
        description: Union[str, None],
    ) -> Decorator:
        self.add_route(
            path,
            method,
            SpyRoute(
                method=method,  # pass method for root validator
                response_class=response_class,
                status_code=status_code,
                tags=tags,
                name=name,
                description=description,
            ),
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
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ) -> Decorator:
        return self.route(
            method=Methods.get,
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
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ) -> Decorator:
        return self.route(
            method=Methods.post,
            path=path,
            response_class=response_class,
            status_code=status_code,
            tags=tags,
            name=name,
            description=description,
        )

    def delete(
        self: Self,
        path: str,
        *,
        response_class: Union[type[BaseModel], None] = None,
        status_code: Union[int, None] = None,
        tags: Union[list[str], None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ) -> Decorator:
        return self.route(
            method=Methods.delete,
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
