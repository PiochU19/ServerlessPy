from argparse import ArgumentParser
from enum import Enum
from typing import Callable, get_args, get_origin, Union
from functools import wraps


def unpack_args(function: Callable[..., None]) -> Callable[..., None]:
    @wraps(function)
    def wrapper(*_, **kwargs: dict[str, ArgumentParser]) -> None:
        parser = kwargs["parser"]
        for argument_name, argument_type_hint in function.__annotations__.items():
            if argument_name == "return":
                continue

            is_required = get_origin(argument_type_hint) is not Union and type(
                None
            ) not in get_args(argument_type_hint)
            argument_type = (
                argument_type_hint if is_required else get_args(argument_type_hint)[0]
            )

            parser.add_argument(
                f"-{argument_name[0]}",
                f"--{argument_name}",
                type=argument_type,
                required=is_required,
            )
        return function(
            **{
                name: value
                for name, value in parser.parse_args().__dict__.items()
                if name != "function"
            }
        )

    return wrapper


@unpack_args
def deploy_layer(path: Union[str, None]) -> None:
    print("Hi from layer")


@unpack_args
def generate_openapi(path: str, something: int) -> None:
    print("Hi from openapi")


class Functions(str, Enum):
    layer = "layer"
    openapi = "openapi"


FUNCTIONS_DEFINITIONS: dict[str, Callable[[], None]] = {
    "layer": deploy_layer,
    "openapi": generate_openapi,
}


def handler() -> None:
    parser = ArgumentParser()
    parser.add_argument("function", type=Functions)
    args, _ = parser.parse_known_args()

    return FUNCTIONS_DEFINITIONS[args.function](parser=parser)
