from pydantic import BaseSettings
from typing import Literal


METHODS = Literal["get", "post", "delete", "put", "patch"]


class Settings(BaseSettings):
    ...


settings = Settings()
