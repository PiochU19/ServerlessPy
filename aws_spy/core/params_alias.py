from typing import Any, Union

from aws_spy.core import params


def Query(name: str | None = None):
    return params.QueryClass(name)


def Path(name: str | None = None):
    return params.PathClass(name)


def Header(name: str | None = None):
    return params.HeaderClass(name)
