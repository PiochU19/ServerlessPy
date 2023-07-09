# import json
# from enum import Enum
# from typing import Any, Union

# from openapi_schema_pydantic.v3.v3_0_3 import OpenAPI
# from openapi_schema_pydantic.v3.v3_0_3.parameter import Parameter
# from openapi_schema_pydantic.v3.v3_0_3.util import (
#     PydanticSchema,
#     Schema,
#     construct_open_api_with_schema_class,
# )

# from aws_spy.core.schemas import Methods, SpyRoute
# from aws_spy.core.types import is_type_required

# SCHEMA_PARAM = {
#     int: "integer",
#     str: "string",
#     bool: "boolean",
#     float: "number",
#     Enum: "string",
# }


# def _get_path_item(method: Methods, route: SpyRoute) -> dict[str, Any]:
#     item = {
#         "responses": {
#             route.status_code: {
#                 "description": "Successful response",
#                 "content": {
#                     "application/json": {
#                         "schema": PydanticSchema(schema_class=route.response_class) if route.response_class else {}
#                     }
#                 },
#             },
#             422: {
#                 "description": "Validation Error",
#                 "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SPY422ErrorResponse"}}},
#             },
#         }
#     }
#     item["parameters"] = [  # type: ignore
#         Parameter(
#             name=route_param.name,
#             required=is_type_required(route_param.annotation),
#             param_in=route_param.in_.in_,
#             param_schema=Schema(
#                 type=SCHEMA_PARAM.get(route_param.annotation, "string"),
#                 enum=route_param.enum,
#             ),
#         )
#         for route_param in route.header_params + route.path_params + route.query_params
#     ]
#     if route.tags:
#         item["tags"] = route.tags  # type: ignore
#     if route.summary:
#         item["summary"] = route.summary  # type: ignore
#     if route.description:
#         item["description"] = route.description  # type: ignore
#     if method not in (Methods.GET, Methods.DELETE):
#         item.update(
#             {
#                 "requestBody": {
#                     "content": {  # type: ignore
#                         "application/json": {
#                             "schema": PydanticSchema(schema_class=route.request_body) if route.request_body else {}
#                         }
#                     }
#                 }
#             }
#         )

#     return item


# def construct_base_open_api(title: str, version: str | None, routes: dict[str, dict[Methods, SpyRoute]]) -> OpenAPI:
#     info = {"title": title}
#     if version is not None:
#         info["version"] = version
#     return OpenAPI.parse_obj(
#         {
#             "info": info,
#             "paths": {
#                 path: {method: _get_path_item(method, route) for method, route in route_dict.items()}
#                 for path, route_dict in routes.items()
#             },
#             "components": {
#                 "schemas": {
#                     "SPY422SingleError": {
#                         "title": "SPY 422 Single Error Schema",
#                         "required": ["message"],
#                         "type": "object",
#                         "properties": {
#                             "message": {
#                                 "title": "Error message",
#                                 "type": "string",
#                             }
#                         },
#                     },
#                     "SPY422ErrorResponse": {
#                         "title": "SPY 422 Error Response",
#                         "required": ["error"],
#                         "type": "object",
#                         "properties": {
#                             "errors": {
#                                 "type": "array",
#                                 "items": {"$ref": "#/components/schemas/SPY422SingleError"},
#                                 "example": [
#                                     "Wrong type received at: age. Expected: integer",
#                                     "Value not found at: name",
#                                     "Required parameter authorization not found in header.",
#                                     "user_id should be UUID type.",
#                                 ],
#                             }
#                         },
#                     },
#                 }
#             },
#         }
#     )


# def get_openapi(title: str, version: str | None, routes: dict[str, dict[Methods, SpyRoute]]) -> dict[str, Any]:
#     return json.loads(
#         construct_open_api_with_schema_class(construct_base_open_api(title, version, routes)).json(
#             by_alias=True, exclude_none=True, indent=2
#         )
#     )
