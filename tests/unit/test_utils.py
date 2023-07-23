import pytest

from aws_spy import Provider, ServerlessConfig, SpyAPI
from aws_spy.helpers.utils import LoadAppFromStringError, load_app_from_string

provider = Provider()
config = ServerlessConfig(service="lambdas", provider=provider)
app = SpyAPI(config=config)


def test_load_app_no_semicolon() -> None:
    with pytest.raises(LoadAppFromStringError, match='Path must be in format "<module>:<app_name>"'):
        load_app_from_string("path.without.module")


def test_load_app_wrong_module() -> None:
    with pytest.raises(LoadAppFromStringError):
        load_app_from_string("tests.unit.test_utilss:app")


def test_load_app_wrong_app() -> None:
    with pytest.raises(LoadAppFromStringError):
        load_app_from_string("tests.unit.test_utils:app1")


def test_load_app_from_string() -> None:
    load_app_from_string("tests.unit.test_utils:app")
