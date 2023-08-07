import json
import typing as t

import typing_extensions as te
from pydantic import BaseModel

from aws_spy.core.schemas import LH, Methods


class APIResponse(BaseModel):
    body: str
    status_code: int | None
    headers: dict[str, t.Any] | None
    raw: dict[str, t.Any]

    @property
    def json(self: te.Self) -> dict[str, t.Any]:
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:  # pragma: no cover
            return {}


class TestClient:
    __test__ = False

    @classmethod
    def post(  # type: ignore
        cls: type[te.Self],
        handler: LH,
        *,
        body: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> APIResponse:
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
    def delete(  # type: ignore
        cls: type[te.Self],
        handler: LH,
        *,
        body: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> APIResponse:
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
    def patch(  # type: ignore
        cls: type[te.Self],
        handler: LH,
        *,
        body: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> APIResponse:
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
    def put(  # type: ignore
        cls: type[te.Self],
        handler: LH,
        *,
        body: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> APIResponse:
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
    def get(  # type: ignore
        cls: type[te.Self],
        handler: LH,
        *,
        body: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> APIResponse:
        return cls._call(
            handler,
            cls._build_event(
                method=Methods.GET,
                body=body,
                headers=headers,
                query_params=query_params,
                path_params=path_params,
            ),
        )

    @staticmethod
    def _call(handler: LH, event: dict[str, t.Any]) -> APIResponse:
        response = handler(event, None)
        return APIResponse(
            status_code=response["statusCode"], raw=response, body=response["body"], headers=response["headers"]
        )

    @staticmethod
    def _build_event(
        *,
        method: Methods,
        body: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None,
        path_params: dict[str, str] | None,
    ) -> dict[str, t.Any]:
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
