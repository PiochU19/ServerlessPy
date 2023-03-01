from typing import Union

from aws_spy.core import params


def Query(name: Union[str, None] = None) -> params.Query:
    return params.Query(name)


def Path(name: Union[str, None] = None) -> params.Path:
    return params.Path(name)


def Header(name: Union[str, None] = None) -> params.Header:
    return params.Header(name)
