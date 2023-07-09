import pytest
from pydantic import BaseModel

from aws_spy import SpyAPI
from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.schemas import Methods


class Request(BaseModel):
    ...


@pytest.mark.parametrize(
    "method",
    [method for method in Methods if method in (Methods.GET, Methods.DELETE)],
)
def test_get_method_with_request_body(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method.value)
    with pytest.raises(
        RouteDefinitionError,
        match=f'{method.upper()} method on "/some_path" cannot have request body!',
    ):

        @app_method("/some_path", "test-lambda")
        def handler(request: Request) -> None:  # noqa: ARG001
            ...


@pytest.mark.parametrize(
    "method",
    [method for method in Methods if method not in (Methods.GET, Methods.DELETE)],
)
def test_request_body(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method.value)
    path = "/somepath"

    @app_method(path, "lambda")
    def handler(request: Request) -> None:  # noqa: ARG001
        ...

    assert len(app.routes) == 1
    route = app.routes[path][method]
    assert route.request_body == Request
    assert route.request_body_arg_name == "request"
