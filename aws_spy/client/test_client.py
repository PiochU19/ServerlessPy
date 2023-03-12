from typing import Any, Union

from typing_extensions import Self  # type: ignore

from aws_spy.core.schemas import LH, Methods
from aws_spy.main import SpyAPI


class Response:
    body: dict[str, Any]
    status_code: int
    raw: dict[str, Any]


class TestClient:
    def __init__(self: Self, app: SpyAPI) -> None:
        self.app = app

    def post(
        self: Self,
        handler: LH,
        *,
        body: str = "",
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None],
    ) -> dict[str, Any]:
        return self._call(
            handler,
            self._build_event(
                Methods.POST,
                body=body,
                headers=headers,
                path_params=path_params,
                query_params=query_params,
            ),
        )

    def get(
        self: Self,
        handler: LH,
        *,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None] = None,
    ) -> dict[str, Any]:
        return self._call(
            handler,
            self._build_event(
                Methods.GET,
                headers=headers,
                query_params=query_params,
                path_params=path_params,
            ),
        )

    @staticmethod
    def _call(handler: LH, event: dict[str, Any]) -> dict[str, Any]:
        return handler(event)

    @staticmethod
    def _build_event(
        *,
        method: Methods,
        body: str = "",
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None],
        path_params: Union[dict[str, str], None],
    ) -> dict[str, Any]:
        base_headers = {
            "content-type": "application/json",
        }
        if headers is not None:
            base_headers.update(headers)

        return {
            "httpMethod": method.value,
            "headers": base_headers,
            "queryStringParameters": query_params,
            "pathParameters": path_params,
            "body": body,
        }
