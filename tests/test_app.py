import pytest

from aws_spy import ServerlessConfig, SpyAPI, SpyRouter, __version__
from aws_spy.core.schemas import Methods


def test_app() -> None:
    assert __version__ == "0.2.11"


def test_app_conf(app: SpyAPI, config: ServerlessConfig) -> None:
    assert app.config == config


@pytest.mark.parametrize("prefix", ["api", "/api", "/somet_other_prefix"])
def test_prefix(config: ServerlessConfig, prefix: str) -> None:
    app = SpyAPI(config=config, prefix=prefix)
    expected_prefix = prefix if prefix.startswith("/") else f"/{prefix}"
    assert app.prefix == expected_prefix


@pytest.mark.parametrize("method", list(Methods))
def test_register_router(config: ServerlessConfig, method: Methods) -> None:
    app = SpyAPI(config=config, prefix="/api")
    router = SpyRouter(prefix="/router")
    router_method = getattr(router, method.value)

    @router_method("path", "lambda")
    def handler1() -> None:
        ...

    @router.function("test-function")
    def handler2() -> None:
        ...

    assert len(router.routes) == 1
    assert len(router.functions) == 1
    assert len(app.routes) == 0
    assert len(app.functions) == 0
    assert router.routes["/router/path"][method]

    app.register_router(router)
    assert len(app.routes) == 1
    assert len(app.functions) == 1
    assert app.routes["/api/router/path"][method]
