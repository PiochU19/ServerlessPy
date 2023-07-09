import json
from typing import Any, Union

import pytest
from pydantic import BaseModel

from aws_spy.core.schemas import SpyRoute
from aws_spy.responses import ErrorResponse, JSONResponse, RAWResponse


class ExampleResponseClass(BaseModel):
    x: int
    y: int


class SameAsExampleResponseClass(BaseModel):
    x: int
    y: int


@pytest.mark.parametrize(
    ["data", "response_class", "expected_response_body", "additional_headers"],
    [
        (
            ExampleResponseClass(x=10, y=15),
            ExampleResponseClass,
            json.dumps({"x": 10, "y": 15}),
            None,
        ),
        (
            SameAsExampleResponseClass(x=10, y=15),
            ExampleResponseClass,
            json.dumps({"x": 10, "y": 15}),
            None,
        ),
        (
            {"x": 10, "y": 15},
            ExampleResponseClass,
            json.dumps({"x": 10, "y": 15}),
            None,
        ),
    ],
)
def test_json_response(
    data: BaseModel | dict[str, Any],
    response_class: type[BaseModel],
    expected_response_body: str,
    additional_headers: dict[str, str] | None,
) -> None:
    expected_headers = {
        "Content-Type": "application/json",
    }
    if additional_headers:
        expected_headers.update(additional_headers)

    route = SpyRoute(
        name="random",
        path="/path",
        method="get",
        handler=lambda: "nothing",
        status_code=202,
        response_class=response_class,
    )
    response_cls = JSONResponse(data, additional_headers)
    response_cls.route = route
    response = response_cls.response
    assert response["statusCode"] == 202
    assert response["body"] == expected_response_body
    assert response["headers"] == expected_headers
