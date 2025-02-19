"""Decorator to add doc-strings to wrapped functions."""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

from __future__ import annotations

from inspect import getmembers, isroutine
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import (
        BuiltinFunctionType,
        BuiltinMethodType,
        ClassMethodDescriptorType,
        FunctionType,
        GetSetDescriptorType,
        LambdaType,
        MethodDescriptorType,
        MethodType,
        MethodWrapperType,
        WrapperDescriptorType,
    )
    from typing import Final

    type ClassCallable = (
        BuiltinFunctionType
        | BuiltinMethodType
        | ClassMethodDescriptorType
        | FunctionType
        | GetSetDescriptorType
        | LambdaType
        | MethodType
        | MethodDescriptorType
        | MethodWrapperType
        | WrapperDescriptorType
    )


def inherit_docs[T](cls: type[T]) -> type[T]:
    """Class decorator that finds empty docstrings tries to copy equivalent from str.

    Returns:
        the decorated class
    """
    # Get all methods defined in the class
    methods: Final[Sequence[tuple[str, ClassCallable]]] = getmembers(
        cls,
        predicate=isroutine,
    )

    method_name: str
    method: ClassCallable
    for method_name, method in methods:
        if method.__doc__ is None:
            try:
                method.__doc__ = cast(
                    "MethodType",
                    getattr(str, method_name, None),
                ).__doc__
            except (AttributeError, NameError):  # pragma: no cover
                continue  # pragma: no cover

    return cls
