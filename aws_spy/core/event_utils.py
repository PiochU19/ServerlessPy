from typing import Any, TypedDict, Union

from aws_spy.core.schemas_utils import ParamSchema


class Event(TypedDict):
    path: str
    httpMethod: str
    headers: dict[str, str]
    queryStringParameters: Union[dict[str, str], None]
    multiValueQueryStringParameters: Union[dict[str, str], None]
    pathParameters: Union[dict[str, str], None]
    body: Union[str, None]
    isBase64Encoded: bool


# TODO: export functionality for all kind of paths
def get_path_params(
    event: Event, expected_path_params: dict[str, ParamSchema]
) -> tuple[dict[str, Any], list[str]]:
    args, errors = {}, []
    path_params = event.get("pathParameters")
    if path_params is None:
        path_params = {}

    for _, expected_path_param in expected_path_params.items():
        param = path_params.get(expected_path_param.name)
        if param is None and expected_path_param.is_required:
            errors.append(f"ERROR")
            continue
        try:
            param = expected_path_param.annotation(param)
        except ValueError:
            errors.append(f"TYPE ERROR")
            continue
        args[expected_path_param.arg_name] = param

    return args, errors
