from enum import Enum
from typing import Callable, TypeVar, Union

from pydantic import BaseModel, root_validator, validator
from typing_extensions import Self  # type: ignore

from serverlesspy.core.exceptions import RouteDefinitionException

LRT = TypeVar("LRT")  # Lambda Return Type
LH = Callable[..., LRT]  # Lambda Handler
Decorator = Callable[[LH], LH]


class Methods(str, Enum):
    get = "get"
    post = "post"
    delete = "delete"
    put = "put"
    patch = "patch"


DEFAULT_STATUS_CODES = {
    Methods.get: "200",
    Methods.post: "201",
    Methods.delete: "204",
    Methods.put: "200",
    Methods.patch: "200",
}


class Functions(str, Enum):
    layer = "layer"
    openapi = "openapi"


class SpyRoute(BaseModel):
    status_code: int
    tags: Union[list[str], None]
    name: str
    description: Union[str, None]
    response_class: Union[type[BaseModel], None]
    path_params: Union[list[str], None]
    query_string_params: Union[list[str], None]

    @validator("method", pre=True, check_fields=False)
    def validate_method_provided(
        cls: type[Self], value: Union[Methods, None]
    ) -> Methods:
        if value is None:
            raise RouteDefinitionException(
                "You need to provide HTTP method in order to complete validation."
            )
        return value

    @validator("status_code", pre=True)
    def set_status_code(cls: type[Self], status_code: Union[int, None]) -> int:
        return status_code or 200

    @validator("name", pre=True)
    def set_name(cls: type[Self], name: Union[str, None]) -> str:
        return name or "My API endpoint"

    @root_validator(pre=True)
    def validate_method(
        cls: type[Self],
        values: dict[str, Union[type[BaseModel], int, list[str], str, None, Methods]],
    ) -> dict[str, Union[type[BaseModel], int, list[str], str, None]]:
        return values
