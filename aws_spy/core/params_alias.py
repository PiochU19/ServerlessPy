from aws_spy.core import params


def Query(name: str | None = None):  # noqa: N802
    return params.QueryClass(name)


def Path(name: str | None = None):  # noqa: N802
    return params.PathClass(name)


def Header(name: str | None = None):  # noqa: N802
    return params.HeaderClass(name)
