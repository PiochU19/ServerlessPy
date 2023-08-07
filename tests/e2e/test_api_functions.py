import typing as t
import uuid

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from aws_spy import BaseSpyError, Header, Path, Query, SpyAPI
from aws_spy.core.schemas import Methods
from aws_spy.responses import JSONResponse
from aws_spy.test import APIResponse, TestClient

client = TestClient()


class ExampleResponse(BaseModel):
    x: int
    y: t.Literal[2]


class ExampleResponseFactory(ModelFactory[ExampleResponse]):
    __model__ = ExampleResponse


class ExampleRequest(BaseModel):
    x: int
    y: t.Literal[2]


class ExampleRequestFactory(ModelFactory[ExampleRequest]):
    __model__ = ExampleRequest


@pytest.mark.parametrize("method", list(Methods))
def test_api_functions(method: Methods, app: SpyAPI) -> None:
    app_method = getattr(app, method.value)
    client_method = getattr(client, method.value)
    path = "/path/{user_id}/{car_id}"

    @app_method(path, "lambda", authorizer="jwt", use_vpc=False, status_code=200, response_class=ExampleResponse)
    def handler(
        request: ExampleRequest,
        user_id: int = Path(),  # noqa: B008
        car_id: uuid.UUID = Path(),  # noqa: B008
        user_id_header: int = Header("user_id"),  # noqa: B008
        car_id_query: uuid.UUID = Query("car_id"),  # noqa: B008
    ) -> JSONResponse:
        assert isinstance(user_id, int)
        assert isinstance(car_id, uuid.UUID)
        assert isinstance(car_id_query, uuid.UUID)
        assert isinstance(user_id_header, int)
        assert isinstance(request, ExampleRequest)
        return JSONResponse(ExampleResponseFactory.build(), status_code=201, additional_headers={"X-Total-Count": 1})

    response: APIResponse = client_method(
        handler,
        body=ExampleRequestFactory.build().model_dump(),
        path_params={"user_id": "123", "car_id": str(uuid.uuid4())},
        headers={"user_id": "123"},
        query_params={"car_id": str(uuid.uuid4())},
    )
    assert response.status_code == 201
    assert ExampleResponse(**response.json)
    assert response.headers == {"Content-Type": "application/json", "X-Total-Count": 1}


@pytest.mark.parametrize("method", list(Methods))
def test_api_functions_raise_error(method: Methods, app: SpyAPI) -> None:
    app_method = getattr(app, method.value)
    client_method = getattr(client, method.value)

    @app_method("/path", "lambda", response_class=ExampleResponse)
    def handler() -> JSONResponse:
        message = "Something went wrong"
        raise BaseSpyError(message, status_code=400)
        return JSONResponse(ExampleResponseFactory.build(), status_code=201, additional_headers={"X-Total-Count": 1})

    response: APIResponse = client_method(handler)
    assert response.status_code == 400
    assert response.json == {"message": "Something went wrong"}

    @app_method("/path1", "lambda1", response_class=ExampleResponse)
    def handler1() -> JSONResponse:
        message = "Something went wrong"
        raise BaseSpyError([message], status_code=402)
        return JSONResponse(ExampleResponseFactory.build(), status_code=201, additional_headers={"X-Total-Count": 1})

    response1: APIResponse = client_method(handler)
    assert response1.status_code == 402
    assert response1.json == {"message": "Something went wrong"}

    @app_method("/path2", "lambda2", response_class=ExampleResponse)
    def handler2() -> JSONResponse:
        message1 = "Something went wrong"
        message2 = "Something else went wrong"
        raise BaseSpyError(
            [message1, message2],
            status_code=404,
        )
        return JSONResponse(ExampleResponseFactory.build(), status_code=201, additional_headers={"X-Total-Count": 1})

    response2: APIResponse = client_method(handler)
    assert response2.status_code == 404
    assert response2.json == {"errors": [{"message": "Something went wrong"}, {"message": "Something else went wrong"}]}
