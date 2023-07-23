import pytest

from aws_spy import SpyAPI
from aws_spy.core.exceptions import FunctionDefinitionError, RouteDefinitionError
from aws_spy.core.schemas import Methods

METHODS = list(Methods)


@pytest.mark.parametrize("method", METHODS)
def test_same_name(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method)
    func_name = "test-name"

    @app.function(func_name)
    def handler() -> None:
        ...

    with pytest.raises(RouteDefinitionError, match=f"There is already {func_name} lambda registered."):

        @app_method("/", func_name)
        def handler() -> None:
            ...

    with pytest.raises(FunctionDefinitionError, match=f"There is already {func_name} lambda registered."):

        @app.function(func_name)
        def handler() -> None:
            ...


@pytest.mark.parametrize("method", METHODS)
def test_same_path_same_method(app: SpyAPI, method: Methods) -> None:
    app_method = getattr(app, method)
    path = "/path"

    @app_method(path, "lambda")
    def handler() -> None:
        ...

    with pytest.raises(
        RouteDefinitionError,
        match=f'There is already existing "{method.upper()}" method definition under "{path}" path.',
    ):

        @app_method(path, "lambda1")
        def handler() -> None:
            ...
