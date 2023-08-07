import os
import typing as t
from pathlib import Path

import pytest
import yaml
from deepdiff import DeepDiff

from aws_spy import SpyAPI
from aws_spy.core.exceptions import RouteDefinitionError
from aws_spy.helpers.cli import generate_serverless_file
from aws_spy.helpers.exceptions import WrongArgumentError


def are_two_yaml_files_same(file_path_1: str, file_path_2: str) -> bool:
    with open(file_path_1) as file_1:
        with open(file_path_2) as file_2:
            return (
                DeepDiff(
                    yaml.safe_load(file_1),
                    yaml.safe_load(file_2),
                    ignore_order=True,
                    ignore_type_in_groups=[(str, int)],
                )
                == {}
            )


def test_generate_file(app: SpyAPI, build_data_path: t.Callable[[str], str], tmp_path: Path) -> None:
    file_path = str(os.path.join(tmp_path, "serverless.yml"))
    sls_file = build_data_path("serverless_file.yml")
    sls_file_wout_functions = build_data_path("serverless_file_without_functions.yml")

    generate_serverless_file(app, file_path)
    assert are_two_yaml_files_same(file_path, sls_file_wout_functions)
    assert not are_two_yaml_files_same(file_path, sls_file)

    @app.function("test-function", use_vpc=True, layers=["test-layer"])
    def handler() -> None:
        ...

    @app.get("/test", "test-route", authorizer="jwt")
    def handler1() -> None:
        ...

    generate_serverless_file(app, file_path)
    assert not are_two_yaml_files_same(file_path, sls_file_wout_functions)
    assert are_two_yaml_files_same(file_path, sls_file)


def test_generate_file_wrong_file(app: SpyAPI) -> None:
    file_path = "serverless.txt"

    with pytest.raises(WrongArgumentError, match="File is not YAML file."):
        generate_serverless_file(app, file_path)


def test_generate_file_wrong_authorizer(app: SpyAPI) -> None:
    authorizer = "jwt1"

    @app.get("/", "test-route", authorizer=authorizer)
    def handler() -> None:
        ...

    file_path = "serverless.yml"
    with pytest.raises(RouteDefinitionError, match=f"Authorizer {authorizer} not defined"):
        generate_serverless_file(app, file_path)
