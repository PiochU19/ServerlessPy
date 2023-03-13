import json
from enum import Enum
from typing import Any, Literal, Union

import pytest
from pydantic import BaseModel, Field

from aws_spy.core.event_utils import export_params_from_event, export_request_body
from aws_spy.core.params_alias import Header
from aws_spy.core.schemas import ParamSchema


class ExampleEnum(str, Enum):
    example = "example"


class ExampleRequestBody(BaseModel):
    a: int
    b: str
    c: bool
    d: Union[int, None]
    example: Union[ExampleEnum, None] = Field(None)


def gpm(
    name: str,
    arg_name: str,
    annotation: type,
    is_required: bool = True,
    enum: Union[list[str], None] = None,
) -> ParamSchema:
    return ParamSchema(
        name=name,
        arg_name=arg_name,
        in_=Header(),
        annotation=annotation,
        is_required=is_required,
        enum=enum,
    )


@pytest.mark.parametrize(
    [
        "in_event_params",
        "expected_params",
        "type_",
        "expected_params_result",
        "expected_errors_result",
    ],
    [
        (None, [], "path", {}, []),
        [
            {"user_id": "valid user id"},
            [gpm("user_id", "user_id", str)],
            "path",
            {"user_id": "valid user id"},
            [],
        ],
        [
            {"user_id": "valid user id"},
            [gpm("user_id", "user_id", int)],
            "path",
            {},
            ["user_id should be int type."],
        ],
        [
            None,
            [gpm("user_id", "user_id", int)],
            "path",
            {},
            ["Required parameter user_id not found in path."],
        ],
        [
            None,
            [gpm("user_id", "user_id", int, False)],
            "path",
            {"user_id": None},
            [],
        ],
        [
            {"user_id": "example"},
            [gpm("user_id", "user_id", ExampleEnum)],
            "path",
            {"user_id": "example"},
            [],
        ],
        [
            {"user_id": "valid user id"},
            [gpm("user_id", "user_id", ExampleEnum)],
            "path",
            {},
            ["user_id should be ExampleEnum type."],
        ],
    ],
)
def test_export_params_from_event_success(
    in_event_params: Union[dict[str, Any], None],
    expected_params: list[ParamSchema],
    type_: Literal["path", "header", "query"],
    expected_params_result: dict[str, Any],
    expected_errors_result: list[str],
) -> None:
    params, errors = export_params_from_event(in_event_params, expected_params, type_)
    assert params == expected_params_result
    assert errors == expected_errors_result


@pytest.mark.parametrize(
    ["body", "expected_errors"],
    [
        (json.dumps({"a": 1, "b": "string", "c": True, "d": None}), []),
        ["", ["Request body is empty!"]],
        (
            json.dumps({"a": "str", "b": "string", "c": "str", "d": None}),
            [
                "Wrong type received at: a. Expected: integer",
                "Wrong type received at: c. Expected: bool",
            ],
        ),
        (
            json.dumps(
                {"a": 1, "b": "string", "c": True, "d": "10", "example": "not example"}
            ),
            ["Wrong type received at: example. Expected: enum"],
        ),
        (
            json.dumps({"b": "string", "c": True, "d": "10", "example": "example"}),
            ["Value not found at: a"],
        ),
    ],
)
def test_export_request_body(body: str, expected_errors: list[str]) -> None:
    request_body, errors = export_request_body(body, ExampleRequestBody)
    assert errors == expected_errors
    if not errors:
        assert isinstance(request_body, ExampleRequestBody)
