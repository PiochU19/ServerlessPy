from argparse import ArgumentParser
from functools import wraps
from typing import Callable, get_args

from serverlesspy import SpyAPI
from serverlesspy.core.schemas import Functions
from serverlesspy.helpers import types
from serverlesspy.helpers.documentation import get_openapi
from serverlesspy.helpers.utils import LoadAppFromStringError, load_app_from_string


def unpack_args(function: Callable[..., None]) -> Callable[..., None]:
    @wraps(function)
    def wrapper(*_, **kwargs: ArgumentParser) -> None:
        parser = kwargs["parser"]
        function_kwargs = {}
        for argument_name, argument_type_hint in function.__annotations__.items():
            if argument_name == "return":
                continue

            if argument_name == "app":
                parser.add_argument("app", type=str)
                args, __ = parser.parse_known_args()
                try:
                    function_kwargs["app"] = load_app_from_string(args.app)
                    continue
                except LoadAppFromStringError as e:
                    print(e)
                    return

            is_required = types.is_required(argument_type_hint)
            argument_type = (
                argument_type_hint if is_required else get_args(argument_type_hint)[0]
            )

            parser.add_argument(
                f"-{argument_name[0]}",
                f"--{argument_name}",
                type=argument_type,
                required=is_required,
            )
        function_kwargs.update(
            {
                name: value
                for name, value in parser.parse_args().__dict__.items()
                if name not in ("function", "app")
            }
        )
        return function(**function_kwargs)

    return wrapper


@unpack_args
def deploy_layer(app: SpyAPI) -> None:
    print("Hi from layer")


@unpack_args
def generate_openapi(app: SpyAPI) -> None:
    print(app.routes)
    # openapi = get_openapi(app.routes)
    # print(openapi)


FUNCTIONS_DEFINITIONS: dict[str, Callable[..., None]] = {
    "layer": deploy_layer,
    "openapi": generate_openapi,
}


def cli_handler() -> None:
    parser = ArgumentParser()
    parser.add_argument("function", type=Functions)
    args, _ = parser.parse_known_args()

    return FUNCTIONS_DEFINITIONS[args.function](parser=parser)
