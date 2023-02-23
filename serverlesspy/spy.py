from pydantic import BaseModel
from serverlesspy.core import METHODS, settings
from typing import TypeVar, Callable, Any, Union
from functools import wraps

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


LambdaHandler = TypeVar("LambdaHandler", bound=Callable[..., dict[str, Any]])
Decorator = Callable[[LambdaHandler], LambdaHandler]


class SpyRoute(BaseModel):
    method: METHODS
    path: str


class _SPY:
    routes: list[SpyRoute]

    def __init__(self: Self, prefix: Union[str, None] = None) -> None:
        self.routes = []
        self.prefix = prefix or ""

    def register_router(self: Self, *, router: Self) -> None:
        self.routes += router.routes

    def add_route(
        self: Self,
        *,
        method: METHODS,
        path: str,
    ) -> None:
        if not path.startswith("/"):
            path = "/" + path
        path = self.prefix + path

        self.routes.append(SpyRoute(method=method, path=path))

    def route(self: Self, *, method: METHODS, path: str) -> Decorator:
        self.add_route(method=method, path=path)

        def decorator(func: LambdaHandler) -> LambdaHandler:
            @wraps(func)
            def wrapper(*args, **kwargs) -> dict[str, Any]:
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get(self: Self, path: str) -> Decorator:
        return self.route(method="get", path=path)

    def post(self: Self, path: str) -> Decorator:
        return self.route(method="post", path=path)


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
