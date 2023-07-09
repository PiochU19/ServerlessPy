from enum import Enum
from typing import Union
from uuid import UUID

import pytest

from aws_spy import Header, Path, Query, SpyAPI
from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.schemas import Methods, ParamSchema


class ExampleEnum(str, Enum):
    example = "example"


METHODS = list(Methods)


@pytest.mark.parametrize("method", METHODS)
def test_path_param_not_found(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method)
    path = "/path_without_user_id"

    with pytest.raises(
        RouteDefinitionError,
        match=(f'Your user_id path parameter is missing in {method.upper()} method on "{path}" path!'),
    ):

        @app_method(path, "lambda")
        def handler(user_id: str = Path()) -> None:
            ...


@pytest.mark.parametrize("method", METHODS)
def test_same_param_names(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method)
    path = "path"

    with pytest.raises(
        RouteDefinitionError,
        match='handler expects two same header params: "user_id"!',
    ):

        @app_method(path, "lambda")
        def handler(user_id: str = Header(), something: str = Header("user_id")) -> None:
            ...


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize(
    ["path", "param", "route_param"],
    [
        ["/user_id", Query(), "query_params"],
        ["/{user_id}", Path(), "path_params"],
        ["/user_id", Header(), "header_params"],
    ],
)
@pytest.mark.parametrize(
    ["param_annotation", "expected_annotation", "is_required", "enum"],
    [
        [str, str, True, None],
        [int, int, True, None],
        [ExampleEnum, ExampleEnum, True, ["example"]],
        [UUID, UUID, True, None],
        [Union[str, None], str, False, None],
        [Union[ExampleEnum, None], ExampleEnum, False, ["example"]],
        [Union[str, int, ExampleEnum, None], str, False, None],  # only first arg
    ],
)
def test_params(
    app: SpyAPI,
    method: Methods,
    param,
    path: str,
    route_param: str,
    param_annotation: type,
    expected_annotation: type,
    is_required: bool,
    enum: list[str] | None,
) -> None:
    app_method = getattr(app, method.value)
    expected_param = ParamSchema(
        name="user_id",
        arg_name="user_id",
        in_=param,
        annotation=expected_annotation,
        is_required=is_required,
        enum=enum,
    )

    @app_method(path, "lambda")
    def handler(user_id: param_annotation = param) -> None:  # type: ignore
        ...

    assert len(app.routes) == 1
    route = app.routes[path][method]
    params = getattr(route, route_param)
    assert len(params) == 1
    assert params[0] == expected_param
