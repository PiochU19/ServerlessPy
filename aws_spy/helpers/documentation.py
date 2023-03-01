import json
from typing import Any, Union

from openapi_schema_pydantic.v3.v3_0_3 import OpenAPI
from openapi_schema_pydantic.v3.v3_0_3.parameter import Parameter
from openapi_schema_pydantic.v3.v3_0_3.util import (
    PydanticSchema,
    Schema,
    construct_open_api_with_schema_class,
)

from aws_spy.core.schemas import Methods, SpyRoute
from aws_spy.core.utils import is_type_required

SCHEMA_PARAM = {
    int: "integer",
    str: "string",
}


def _get_path_item(method: Methods, route: SpyRoute) -> dict[str, Any]:
    item = {
        "responses": {
            route.status_code: {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": PydanticSchema(schema_class=route.response_class)
                        if route.response_class
                        else {}
                    }
                },
            }
        }
    }
    item["parameters"] = [  # type: ignore
        Parameter(
            name=route_param.name,
            required=is_type_required(route_param.annotation),
            param_in=route_param.in_.in_,
            param_schema=Schema(
                type=SCHEMA_PARAM.get(route_param.annotation, "string")
            ),
        )
        for route_param in route.params
    ]
    if route.tags:
        item["tags"] = route.tags  # type: ignore
    if route.summary:
        item["summary"] = route.summary  # type: ignore
    if route.description:
        item["description"] = route.description  # type: ignore
    if method not in (Methods.GET, Methods.DELETE):
        item.update(
            {
                "requestBody": {
                    "content": {  # type: ignore
                        "application/json": {
                            "schema": PydanticSchema(schema_class=route.request_body)
                            if route.request_body
                            else {}
                        }
                    }
                }
            }
        )

    return item


def construct_base_open_api(
    title: str, version: Union[str, None], routes: dict[str, dict[Methods, SpyRoute]]
) -> OpenAPI:
    info = {"title": title}
    if version is not None:
        info["version"] = version
    return OpenAPI.parse_obj(
        {
            "info": info,
            "paths": {
                path: {
                    method: _get_path_item(method, route)
                    for method, route in route_dict.items()
                }
                for path, route_dict in routes.items()
            },
        }
    )


def get_openapi(
    title: str, version: Union[str, None], routes: dict[str, dict[Methods, SpyRoute]]
) -> dict[str, Any]:
    return json.loads(
        construct_open_api_with_schema_class(
            construct_base_open_api(title, version, routes)
        ).json(by_alias=True, exclude_none=True, indent=2)
    )
