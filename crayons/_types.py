"""Typehints for crayons."""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

from __future__ import annotations

from typing import Final, Protocol, override, runtime_checkable


# pylint: disable=too-few-public-methods
@runtime_checkable
class StringInterpolatable(Protocol):
    """Any object which may be interpolated as a `str` via the __str__ dunder-method.

    All objects have a __str__ method, because the base-class `object` does. So,
        this specifically represents an object that has not overriden __str__ to
        return a type other than `str` (e.g. None, NotImplemented, etc.).

    Not `@runtime_checkable`, because that does not validate type hints.
    """

    @override
    def __str__(self) -> str: ...


# Valid ANSI color names and their corresponding codes.
FORE_COLORS: Final[dict[str, str]] = {
    "BLACK": "\x1b[30m",
    "RED": "\x1b[31m",
    "GREEN": "\x1b[32m",
    "YELLOW": "\x1b[33m",
    "BLUE": "\x1b[34m",
    "MAGENTA": "\x1b[35m",
    "CYAN": "\x1b[36m",
    "WHITE": "\x1b[37m",
    "RESET": "\x1b[39m",
    "LIGHTBLACK_EX": "\x1b[90m",
    "LIGHTRED_EX": "\x1b[91m",
    "LIGHTGREEN_EX": "\x1b[92m",
    "LIGHTYELLOW_EX": "\x1b[93m",
    "LIGHTBLUE_EX": "\x1b[94m",
    "LIGHTMAGENTA_EX": "\x1b[95m",
    "LIGHTCYAN_EX": "\x1b[96m",
    "LIGHTWHITE_EX": "\x1b[97m",
}

# Valid ANSI style names and their corresponding codes.
STYLES: Final[dict[str, str]] = {
    "BRIGHT": "\x1b[1m",
    "DIM": "\x1b[2m",
    "NORMAL": "\x1b[22m",
    "RESET_ALL": "\x1b[0m",
}
