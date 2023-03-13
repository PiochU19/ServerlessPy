import pytest
from pydantic import BaseModel

from aws_spy import SpyAPI
from aws_spy.core.schemas import Methods


class Request(BaseModel):
    ...


@pytest.mark.parametrize("method", [method for method in Methods if method])
def test_request_body(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method.value)
    path = "/somepath"

    @app_method(path, "lambda", response_class=Request)
    def handler() -> None:
        ...

    assert len(app.routes) == 1
    route = app.routes[path][method]
    assert route.response_class == Request
