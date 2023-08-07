import os
import sys
from argparse import ArgumentParser
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from shutil import copyfile, copytree
from typing import get_args

import yaml  # type: ignore

from aws_spy import SpyAPI
from aws_spy.core import logger
from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.core.schemas import Function, Functions
from aws_spy.core.types import is_type_required

# from aws_spy.helpers.documentation import get_openapi
from aws_spy.helpers.exceptions import PythonEnvironmentError, WrongArgumentError
from aws_spy.helpers.utils import LoadAppFromStringError, load_app_from_string


def unpack_args(function: Callable[..., None]) -> Callable[..., None]:  # pragma: no cover
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
                    logger.error(e)
                    return

            is_required = is_type_required(argument_type_hint)
            argument_type = argument_type_hint if is_required else get_args(argument_type_hint)[0]

            parser.add_argument(
                f"-{argument_name[0]}",
                f"--{argument_name}",
                type=argument_type,
                required=is_required,
            )
        function_kwargs.update(
            {name: value for name, value in parser.parse_args().__dict__.items() if name not in ("function", "app")}
        )
        return function(**function_kwargs)

    return wrapper


@unpack_args
def _deploy_layer(stage: str, region: str) -> None:  # pragma: no cover
    return _deploy_layer(stage=stage, region=region)


def deploy_layer(stage: str, region: str) -> None:  # pragma: no cover
    site_packages = None
    for path in sys.path:
        if path.endswith("site-packages"):
            site_packages = path

    if site_packages is None:
        msg = "Couldn't find site-packages folder."
        raise PythonEnvironmentError(msg)
    spy_package_name = "aws_spy"

    serverlesspy_path = Path(os.path.join(site_packages, spy_package_name))
    layer_path = Path(os.path.join(serverlesspy_path, "layer", "spy", "python"))
    serverless_layer_path = Path(os.path.join(layer_path, spy_package_name))
    serverless_layer_path.mkdir(parents=True, exist_ok=True)

    for package in ("pydantic",):
        package_path = Path(os.path.join(site_packages, package))
        if not package_path.is_dir():
            msg = f'Could not find "{package}" package. Make sure it is installed in your current environment.'
            raise PythonEnvironmentError(msg)
        copytree(str(package_path), os.path.join(layer_path, package))

    copyfile(
        os.path.join(site_packages, "typing_extensions.py"),
        os.path.join(layer_path, "typing_extensions.py"),
    )

    copytree(
        os.path.join(serverlesspy_path, "core"),
        os.path.join(serverless_layer_path, "core"),
    )
    for file_to_copy in ("__init__.py", "main.py", "responses.py"):
        copyfile(
            os.path.join(serverlesspy_path, file_to_copy),
            os.path.join(serverless_layer_path, file_to_copy),
        )
    current_working_dir = os.getcwd()
    os.chdir(os.path.join(serverlesspy_path, "layer"))
    os.system(f"serverless deploy -s {stage} -c spy-layer.yml --region {region}")  # noqa: S605
    os.chdir(current_working_dir)


# @unpack_args
# def generate_openapi(app: SpyAPI, path: str) -> None:
#     open_api = get_openapi(app.title, app.version, app.routes)
#     with open(f"./{path}", "w") as file:
#         json.dump(open_api, file)


@unpack_args
def _generate_serverless_file(app: SpyAPI, path: str) -> None:  # pragma: no cover
    return generate_serverless_file(app=app, path=path)


def generate_serverless_file(app: SpyAPI, path: str) -> None:
    if not path.endswith(".yml"):
        msg = "File is not YAML file."
        raise WrongArgumentError(msg)

    functions: dict[str, Function] = {}
    for route_path, route_dict in app.routes.items():
        for method, route in route_dict.items():
            if route.authorizer is not None and (
                app.config.provider.httpApi is None
                or app.config.provider.httpApi.authorizers is None
                or route.authorizer not in app.config.provider.httpApi.authorizers.keys()
            ):
                msg = f"Authorizer {route.authorizer} not defined"
                raise RouteDefinitionError(msg)

            functions[route.name] = Function.from_route(route=route, method=method, path=route_path)
    for function in app.functions:
        functions[function.name] = Function.from_function(function=function)

    app.config.functions = functions

    with open(path, "w") as file:
        yaml.dump(app.config.model_dump(exclude_none=True), file)


FUNCTIONS_DEFINITIONS: dict[str, Callable[..., None]] = {
    "layer": _deploy_layer,
    # "openapi": generate_openapi,
    "sls": _generate_serverless_file,
}


def cli_handler() -> None:  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument("function", type=Functions)
    args, _ = parser.parse_known_args()

    return FUNCTIONS_DEFINITIONS[args.function](parser=parser)
