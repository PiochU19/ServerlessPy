from typing_extensions import Self  # type: ignore

from aws_spy.main import SpyAPI


class TestClient:
    def __init__(self: Self, app: SpyAPI) -> None:
        self.app = app
