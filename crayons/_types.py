"""Constants and wrappers used for typehints and autocompletion."""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

# pylint: disable=missing-class-docstring,missing-function-docstring
# pylint: disable=too-many-public-methods
# ruff: noqa: A001,ANN401,CPY001,FBT001,N801,PLR0904
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Buffer
from sys import version_info
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Protocol,
    Self,
    SupportsIndex,
    assert_never,
    cast,
    overload,
    override,
    runtime_checkable,
)

from ._inherit_docs import inherit_docs

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Sequence


# pylint: disable=too-few-public-methods
@runtime_checkable
class StrInterpolable(Protocol):
    """Any object which may be interpolated as a `str` via the __str__ dunder-method.

    All objects have a __str__ method, because the base-class `object` does. So,
        this specifically represents an object that has not overridden __str__ to
        return a type other than `str` (e.g. None, NotImplemented, etc.).

    """

    @override
    def __str__(self) -> str: ...  # pragma: no cover


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

type ReadableBuffer = Buffer


class _FormatMapMapping(Protocol):  # pragma: no cover
    def __getitem__(self, key: str, /) -> Any: ...  # type: ignore[explicit-any]


class _TranslateTable(Protocol):  # pragma: no cover
    def __getitem__(self, key: int, /) -> str | int | None: ...


# Taken and lightly modified from typeshed's builtin str class stubs.
@inherit_docs
class ColoredStringABC(ABC):
    def __init__(
        self,
        color: str,
        s: StrInterpolable,
        always_color: bool,
        bold: bool,
    ) -> None:
        self.s: StrInterpolable = s
        self.color: str = color
        self.always_color: bool = always_color
        self.bold: bool = bold

    @abstractmethod
    def _new(self, s: StrInterpolable) -> Self: ...  # pragma: no cover

    def capitalize(self) -> Self:
        return self._new(str(self.s).capitalize())

    def casefold(self) -> Self:
        return self._new(str(self.s).casefold())

    def center(
        self,
        width: SupportsIndex,
        fillchar: str = " ",
        /,
    ) -> Self:
        return self._new(str(self.s).center(width, fillchar))

    def count(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> int:
        return str(self.s).count(sub, start, end)

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        return str(self.s).encode(encoding, errors)

    def endswith(
        self,
        suffix: str | tuple[str, ...],
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> bool:
        return str(self.s).endswith(suffix, start, end)

    def expandtabs(self, tabsize: SupportsIndex = 8) -> Self:
        return self._new(str(self.s).expandtabs(tabsize))

    def find(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> int:
        return str(self.s).find(sub, start, end)

    def format(self, *args: object, **kwargs: object) -> Self:
        return self._new(str(self.s).format(args, kwargs))

    def format_map(self, mapping: _FormatMapMapping, /) -> Self:
        return self._new(str(self.s).format_map(mapping))

    def index(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> int:
        return str(self.s).index(sub, start, end)

    def isalpha(self) -> bool:
        return str(self.s).isalpha()

    def isalnum(self) -> bool:
        return str(self.s).isalnum()

    def isascii(self) -> bool:
        return str(self.s).isascii()

    def isdecimal(self) -> bool:
        return str(self.s).isdecimal()

    def isdigit(self) -> bool:
        return str(self.s).isdigit()

    def isidentifier(self) -> bool:
        return str(self.s).isidentifier()

    def islower(self) -> bool:
        return str(self.s).islower()

    def isnumeric(self) -> bool:
        return str(self.s).isnumeric()

    def isprintable(self) -> bool:
        return str(self.s).isprintable()

    def isspace(self) -> bool:
        return str(self.s).isspace()

    def istitle(self) -> bool:
        return str(self.s).istitle()

    def isupper(self) -> bool:
        return str(self.s).isupper()

    def join(self, iterable: Iterable[str], /) -> Self:
        return self._new(str(self.s).join(iterable))

    def ljust(self, width: SupportsIndex, fillchar: str = " ", /) -> Self:
        return self._new(str(self.s).ljust(width, fillchar))

    def lower(self) -> Self:
        return self._new(str(self.s).lower())

    def lstrip(self, chars: str | None = None, /) -> Self:
        return self._new(str(self.s).lstrip(chars))

    @staticmethod
    @overload
    def maketrans[_T](
        x: dict[int, _T] | dict[str, _T] | dict[str | int, _T],
        /,
    ) -> dict[int, _T]: ...  # pragma: no cover
    @staticmethod
    @overload
    def maketrans(x: str, y: str, /) -> dict[int, int]: ...  # pragma: no cover
    @staticmethod
    @overload
    def maketrans(
        x: str,
        y: str,
        z: str,
        /,
    ) -> dict[int, int | None]: ...  # pragma: no cover

    @staticmethod
    def maketrans[_T](
        x: dict[int, _T] | dict[str, _T] | dict[str | int, _T] | str,
        /,
        *args: str,
    ) -> dict[int, _T] | dict[int, int] | dict[int, int | None]:
        # If x is a dict, we're in the first overload case
        if isinstance(x, dict):
            return str.maketrans(x)
        # Otherwise we pass through all arguments to str.maketrans
        return str.maketrans(x, *args)

    def partition(
        self,
        sep: str,
        /,
    ) -> tuple[Self, Self, Self]:
        # mypy, as of 1.15.0, discards tuple length information in comprehensions.
        return cast(
            "tuple[Self, Self, Self]",
            tuple(
                cast(
                    "Generator[Self, None, None]",
                    (self._new(c) for c in str(self.s).partition(sep)),
                ),
            ),
        )

    if version_info >= (3, 13):  # pragma: no cover

        def replace(self, old: str, new: str, /, count: SupportsIndex = -1) -> Self:
            return self._new(str(self.s).replace(old, new, count))

    else:
        # Mypy complains, even though only one will be defined.
        def replace(  # type: ignore[misc]
            self,
            old: str,
            new: str,
            count: SupportsIndex = -1,
            /,
        ) -> Self:
            return self._new(str(self.s).replace(old, new, count))

    def removeprefix(self, prefix: str, /) -> Self:
        return self._new(str(self.s).removeprefix(prefix))

    def removesuffix(self, suffix: str, /) -> Self:
        return self._new(str(self.s).removesuffix(suffix))

    def rfind(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> int:
        return str(self.s).rfind(sub, start, end)

    def rindex(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> int:
        return str(self.s).rindex(sub, start, end)

    def rjust(self, width: SupportsIndex, fillchar: str = " ", /) -> Self:
        return self._new(str(self.s).rjust(width, fillchar))

    def rpartition(
        self,
        sep: str,
        /,
    ) -> tuple[Self, Self, Self]:
        return cast(
            "tuple[Self, Self, Self]",
            tuple(
                cast(
                    "Generator[Self, None, None]",
                    (self._new(c) for c in str(self.s).rpartition(sep)),
                ),
            ),
        )

    def rsplit(
        self,
        sep: str | None = None,
        maxsplit: SupportsIndex = -1,
    ) -> list[Self]:
        return [self._new(c) for c in str(self.s).rsplit(sep, maxsplit)]

    def rstrip(self, chars: str | None = None, /) -> Self:
        return self._new(str(self.s).rstrip(chars))

    def split(
        self,
        sep: str | None = None,
        maxsplit: SupportsIndex = -1,
    ) -> list[Self]:
        return [self._new(c) for c in str(self.s).split(sep, maxsplit)]

    def splitlines(self, keepends: bool = False) -> list[Self]:  # noqa: FBT002
        return [self._new(c) for c in str(self.s).splitlines(keepends)]

    def startswith(
        self,
        prefix: str | tuple[str, ...],
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
        /,
    ) -> bool:
        return str(self.s).startswith(prefix, start, end)

    def strip(self, chars: str | None = None, /) -> Self:
        return self._new(str(self.s).strip(chars))

    def swapcase(self) -> Self:
        return self._new(str(self.s).swapcase())

    def title(self) -> Self:
        return self._new(str(self.s).title())

    def translate(self, table: _TranslateTable, /) -> Self:
        return self._new(str(self.s).translate(table))

    def upper(self) -> Self:
        return self._new(str(self.s).upper())

    def zfill(self, width: SupportsIndex, /) -> Self:
        return self._new(str(self.s).zfill(width))

    # Incompatible with Sequence.__contains__
    def __contains__(self, key: StrInterpolable, /) -> bool:
        return str(self.s).__contains__(str(key))

    def __eq__(self, value: object, /) -> bool:
        match value:
            case ColoredStringABC():
                return (
                    self.always_color == value.always_color
                    and self.bold == value.bold
                    and self.color == value.color
                    and self.s == value.s
                )
            case str():
                return str(self.s).__eq__(value)
            case StrInterpolable():
                return str(self.s).__eq__(str(value))
            case _ as unreachable:  # pragma: no cover
                assert_never(unreachable)

    @overload
    def __gt__(self, value: ColoredStringABC, /) -> bool: ...  # pragma: no cover
    @overload
    def __gt__(self, value: StrInterpolable, /) -> bool: ...  # pragma: no cover

    def __gt__(self, value: StrInterpolable | ColoredStringABC, /) -> bool:
        match value:
            case ColoredStringABC():
                return str(self.s).__gt__(str(value.s))
            case str():
                return str(self.s).__gt__(value)
            case StrInterpolable():
                return str(self.s).__gt__(str(value))
            case _ as unreachable:  # pragma: no cover
                assert_never(unreachable)

    @overload
    def __ge__(self, value: ColoredStringABC, /) -> bool: ...  # pragma: no cover
    @overload
    def __ge__(self, value: StrInterpolable, /) -> bool: ...  # pragma: no cover

    def __ge__(self, value: StrInterpolable | ColoredStringABC, /) -> bool:
        match value:
            case ColoredStringABC() | str():
                return self.__gt__(value) or self.__eq__(str(value))
            case StrInterpolable():
                return self.__gt__(str(value)) or self.__eq__(str(value))
            case _ as unreachable:  # pragma: no cover
                assert_never(unreachable)

    @overload
    def __le__(self, value: ColoredStringABC, /) -> bool: ...  # pragma: no cover
    @overload
    def __le__(self, value: StrInterpolable, /) -> bool: ...  # pragma: no cover

    def __le__(self, value: StrInterpolable | ColoredStringABC, /) -> bool:
        match value:
            case ColoredStringABC() | str():
                return self.__lt__(value) or self.__eq__(str(value))
            case StrInterpolable():
                return self.__lt__(str(value)) or self.__eq__(str(value))
            case _ as unreachable:  # pragma: no cover
                assert_never(unreachable)

    @overload
    def __lt__(self, value: ColoredStringABC, /) -> bool: ...  # pragma: no cover
    @overload
    def __lt__(self, value: StrInterpolable, /) -> bool: ...  # pragma: no cover

    def __lt__(self, value: StrInterpolable | ColoredStringABC, /) -> bool:
        match value:
            case ColoredStringABC():
                return str(self.s).__lt__(str(value.s))
            case str():
                return str(self.s).__lt__(value)
            case StrInterpolable():
                return str(self.s).__lt__(str(value))
            case _ as unreachable:  # pragma: no cover
                assert_never(unreachable)

    def __mod__(self, value: Any, /) -> str:  # type: ignore[explicit-any]
        return str(self.s).__mod__(value)  # type: ignore[misc]

    def __getitem__(
        self,
        i: SupportsIndex | slice[int | None, int | None, int | None],
        /,
    ) -> Self | Sequence[Self]:
        return self._new(str(self.s).__getitem__(i))

    def __hash__(self) -> int:
        return hash((self.s, self.color, self.always_color, self.bold))
