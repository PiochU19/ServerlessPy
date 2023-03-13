import pytest
from pydantic import BaseModel

from aws_spy import SpyAPI
from aws_spy.core.exceptions import RouteDefinitionException


class Request(BaseModel):
    ...


def test_get_method_with_request_body(app: SpyAPI) -> None:
    with pytest.raises(
        RouteDefinitionException,
        match='GET method on "/some_path" cannot have request body!',
    ):

        @app.get("/some_path", "test-lambda")
        def handler(request: Request) -> None:
            ...
