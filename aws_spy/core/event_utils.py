import json
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from aws_spy.core.schemas_utils import ParamSchema

RequestBodyType = TypeVar("RequestBodyType", bound=BaseModel)


def export_params_from_event(
    in_event_params: dict[str, Any] | None,
    expected_params: list[ParamSchema],
    type_: Literal["path", "header", "query"],
) -> tuple[dict[str, Any], list[str]]:
    if in_event_params is None:
        in_event_params = {}
    args, errors = {}, []
    for expected_param in expected_params:
        param = in_event_params.get(expected_param.name)
        if param is None and expected_param.is_required:
            errors.append(f"Required parameter {expected_param.name} not found in {type_}.")
            continue
        try:
            param = expected_param.annotation(param) if param is not None else None
        except ValueError:
            errors.append(f"{expected_param.name} should be {expected_param.annotation.__name__} type.")
            continue
        args[expected_param.arg_name] = param

    return args, errors


def export_request_body(
    body: str, request_body_class: type[RequestBodyType]
) -> tuple[RequestBodyType | dict[str, Any] | None, list[str]]:
    try:
        body = json.loads(body)
    except json.JSONDecodeError:
        return None, ["Request body is empty!"]
    try:
        request_body = request_body_class.model_validate(body)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            if error["type"].startswith("type_error"):
                errors.append(f'Wrong type received at: {error["loc"][0]}. Expected: {error["type"].split(".")[-1]}')
                continue
            if error["type"].endswith("missing"):
                errors.append(f'Value not found at: {error["loc"][0]}')
                continue
            errors.append(f"Unknown error: {error}")  # pragma: no cover
        return None, errors

    return request_body, []
