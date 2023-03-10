import json
from typing import Any, Union

from pydantic import BaseModel
from typing_extensions import Self  # type: ignore

from aws_spy.core.schemas import LH, Methods


class Response(BaseModel):
    body: str
    status_code: int
    raw: dict[str, Any]

    @property
    def json_body(self: Self) -> dict[str, Any]:
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return dict()


class TestClient:
    __test__ = False

    @classmethod
    def post(
        cls: type[Self],
        handler: LH,
        *,
        body: dict[str, Any] = None,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None] = None,
    ) -> Response:
        return cls._call(
            handler,
            cls._build_event(
                method=Methods.POST,
                body=body,
                headers=headers,
                path_params=path_params,
                query_params=query_params,
            ),
        )

    @classmethod
    def delete(
        cls: type[Self],
        handler: LH,
        *,
        body: dict[str, Any] = None,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None] = None,
    ) -> Response:
        return cls._call(
            handler,
            cls._build_event(
                method=Methods.DELETE,
                body=body,
                headers=headers,
                path_params=path_params,
                query_params=query_params,
            ),
        )

    @classmethod
    def patch(
        cls: type[Self],
        handler: LH,
        *,
        body: dict[str, Any] = None,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None] = None,
    ) -> Response:
        return cls._call(
            handler,
            cls._build_event(
                method=Methods.PATCH,
                body=body,
                headers=headers,
                path_params=path_params,
                query_params=query_params,
            ),
        )

    @classmethod
    def put(
        cls: type[Self],
        handler: LH,
        *,
        body: dict[str, Any] = None,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None] = None,
    ) -> Response:
        return cls._call(
            handler,
            cls._build_event(
                method=Methods.PUT,
                body=body,
                headers=headers,
                path_params=path_params,
                query_params=query_params,
            ),
        )

    @classmethod
    def get(
        cls: type[Self],
        handler: LH,
        *,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None] = None,
        path_params: Union[dict[str, str], None] = None,
    ) -> Response:
        return cls._call(
            handler,
            cls._build_event(
                method=Methods.GET,
                headers=headers,
                query_params=query_params,
                path_params=path_params,
            ),
        )

    @staticmethod
    def _call(handler: LH, event: dict[str, Any]) -> Response:
        response = handler(event, None)
        return Response(
            status_code=response["statusCode"], raw=response, body=response["body"]
        )

    @staticmethod
    def _build_event(
        *,
        method: Methods,
        body: dict[str, Any] = None,
        headers: Union[dict[str, str], None] = None,
        query_params: Union[dict[str, str], None],
        path_params: Union[dict[str, str], None],
    ) -> dict[str, Any]:
        if body is None:
            body = {}
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
            "body": json.dumps(body),
        }
