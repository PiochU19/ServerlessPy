# import inspect
# from collections.abc import Callable
# from typing import TypedDict

# from pydantic import BaseModel
# from typing_extensions import Self


# class Dependency:
#     def __init__(self: Self, func: Callable) -> None:
#         self.func = func


# def is_dependency(arg) -> bool:
#     return isinstance(arg.param, Dependency)


# class DependencySchema(TypedDict):
#     arg_name: str
#     func: Callable
#     dependencies: dict[Callable, list["DependencySchema"]]


# class FunctionDependencies(BaseModel):
#     dependency_tree: dict[str, DependencySchema]


# def get_dependencies(func: Callable) -> FunctionDependencies:
#     dependencies = {}
#     for arg in inspect.signature(func).parameters.values():
#         if is_dependency(arg):
#             dependencies[arg.name] = DependencySchema(
#                 arg_name=arg.name,
#                 func=arg.default.func,
#                 dependencies=get_dependencies(arg.default.func).dependency_tree,
#             )

#     return FunctionDependencies(dependency_tree=dependencies)
