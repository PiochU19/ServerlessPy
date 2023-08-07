import typing as t

TypeHint = t.TypeVar("TypeHint")


def is_type_required(type_hint: type[t.Any]) -> bool:
    """
    Returns bool value, whether argument's type hint is required:
    str, int, Union[str, int]...
    Or not required:
    Optional[str], str | None, Union[str, None]...
    """
    return t.get_origin(type_hint) is not t.Union and type(None) not in t.get_args(type_hint)


def get_type_from_optional(type_hint: type[t.Any]) -> type[t.Any]:
    return t.get_args(type_hint)[0]
