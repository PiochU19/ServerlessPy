from aws_spy import ServerlessConfig, SpyAPI, __version__


def test_app() -> None:
    assert __version__ == "0.1.3"


def test_app_conf(app: SpyAPI, config: ServerlessConfig) -> None:
    assert app.config == config
