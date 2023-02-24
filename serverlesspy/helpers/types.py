from typing import TypeVar, Union, get_args, get_origin

TypeHint = TypeVar("TypeHint")


def is_required(type_hint: type[TypeHint]) -> bool:
    """
    Returns bool value, whether argument's type hint is required:
    str, int, Union[str, int]...
    Or not required:
    Optional[str], str | None, Union[str, None]...
    """
    return get_origin(type_hint) is not Union and type(None) not in get_args(type_hint)
