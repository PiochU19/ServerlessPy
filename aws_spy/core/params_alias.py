from typing import Any, Union

from aws_spy.core import params


def Query(name: Union[str, None] = None):
    return params.QueryClass(name)


def Path(name: Union[str, None] = None):
    return params.PathClass(name)


def Header(name: Union[str, None] = None):
    return params.HeaderClass(name)
