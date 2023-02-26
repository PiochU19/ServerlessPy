from openapi_schema_pydantic import (
    Info,
    OpenAPI,
    Operation,
    PathItem,
    RequestBody,
    Response,
)
from openapi_schema_pydantic.util import PydanticSchema

from serverlesspy.core.schemas import Methods, SpyRoute


def _get_path_item(route: SpyRoute) -> PathItem:
    operation_kwargs = {
        "tags": route.tags,
        "summary": "Endpoint summary",
        "description": route.description,
        "requestBody": RequestBody(
            content={
                "application/json": {
                    "schema": PydanticSchema(schema_class=route.response_class)
                }
            },
            required=True,
        ),
        "responses": "",
    }
    if route.method == Methods.get:
        return PathItem(get=Operation(**operation_kwargs))
    if route.method == Methods.post:
        return PathItem(post=Operation(**operation_kwargs))


def get_openapi(routes: list[SpyRoute]) -> None:
    return OpenAPI(
        info=Info(title="My own API", version="0.1.0", summary="Short description"),
        paths={route.path: _get_path_item(route) for route in routes},
    )
