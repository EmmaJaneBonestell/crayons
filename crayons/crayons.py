"""A simple and elegant wrapper for colorama."""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

# pylint: disable=global-statement
# ruff: noqa: PLW0603
from __future__ import annotations

from collections import UserString
from collections.abc import Mapping, Sequence
from itertools import product
from os import environ
from random import randrange, seed as random_seed
from re import VERBOSE as RE_VERBOSE, compile as re_compile
from sys import stderr, stdout
from typing import (
    TYPE_CHECKING,
    Final,
    Protocol,
    SupportsIndex,
    cast,
    final,
    override,
    runtime_checkable,
)

from colorama import init as colorama_init

from ._types import FORE_COLORS, STYLES

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator
    from re import Match, Pattern
    from typing import Any

    from ._types import StringInterpolatable


COLORS: Final[frozenset[str]] = frozenset({
    "black",
    "blue",
    "cyan",
    "green",
    "lightblack_ex",
    "lightblue_ex",
    "lightcyan_ex",
    "lightgreen_ex",
    "lightmagenta_ex",
    "lightred_ex",
    "lightwhite_ex",
    "lightyellow_ex",
    "magenta",
    "red",
    "white",
    "yellow",
})

colorama_init()
REPLACE_COLORS: dict[str, str] = {}
random_seed()

DISABLE_COLOR: bool = "get_ipython" in dir() or environ.get("TERM", None) == "dumb"

_ANSI_ESCAPE_REGEX: Final[Pattern[str]] = re_compile(
    r"""(?:\x1b\[[0-9]+m){2} # the first two ANSI esc seqs
            (?:(?!\x1b)+.*)+     # anything not starting with esc seq
            (?:\x1b\[[0-9]+m){2} # the last two ANSI esc seqs""",
    RE_VERBOSE,
)


@final
class ColoredString:
    """Enhanced string for __len__ operations on Colored output."""

    __slots__ = ("always_color", "bold", "color", "s")

    def __init__(
        self,
        color: str,
        s: StringInterpolatable,
        always_color: bool = False,  # noqa: FBT001, FBT002
        bold: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        super().__init__()
        self.s: str = str(s, encoding="utf-8") if isinstance(s, bytes) else str(s)
        self.color: str = REPLACE_COLORS.get(color, color)
        self.always_color: bool = always_color
        self.bold: bool = bold
        if environ.get("CLINT_FORCE_COLOR", None):
            self.always_color = True

    def __getattr__(
        self,
        att: str,
    ) -> StringInterpolatable | Collection[StringInterpolatable]:  # noqa: C901,RUF100
        # pylint: disable=too-many-return-statements
        def func_help(  # type: ignore[explicit-any] # noqa: PLR0911
            *args: Any,  # noqa: ANN401
            **kwargs: Any,  # noqa: ANN401
        ) -> StringInterpolatable | Collection[StringInterpolatable]:
            """Helper for creating ColoredString.

            Returns:
                the ColoredString interpolation.
            """
            result: StringInterpolatable | Collection[StringInterpolatable] = getattr(
                self.s,
                att,
            )(*args, **kwargs)  # type: ignore[misc]
            # The casts are for pyright, which seems to have trouble
            # inferring the generic subtype.
            match result:
                case str() | UserString():
                    return self._new(result)
                case bytes():
                    return self._new(result.decode("utf-8"))
                case list() | Sequence():
                    return [
                        self._new(x)
                        for x in cast("Sequence[StringInterpolatable]", result)
                    ]
                case frozenset():
                    return frozenset({
                        self._new(x)
                        for x in cast("frozenset[StringInterpolatable]", result)
                    })
                case set():
                    return {
                        self._new(x) for x in cast("set[StringInterpolatable]", result)
                    }
                case tuple():
                    return tuple(
                        self._new(x)
                        for x in cast("tuple[StringInterpolatable, ...]", result)
                    )
                case dict() | Mapping():
                    return {
                        self._new(k): self._new(v)
                        for (k, v) in cast(
                            "Mapping[StringInterpolatable, StringInterpolatable]",
                            result,
                        ).items()
                    }
                case _:
                    return result

        # mypy incorrectly warns about an inferred Callable containing an Any here;
        # StringInterpolatable subsumes any such Callable.
        return func_help  # type: ignore[misc]

    @property
    def color_str(self) -> str:
        """Colorama instantisting wrapper."""

        def format_match(match: Match[str]) -> str:
            return f"{match.group()}{FORE_COLORS[self.color]}{STYLES[style]}"

        style: Final[str] = "BRIGHT" if self.bold else "NORMAL"
        c: Final[str] = (
            f"{FORE_COLORS[self.color]}{STYLES[style]}"
            f"{_ANSI_ESCAPE_REGEX.sub(format_match, self.s)}"
            f"{STYLES['NORMAL']}{FORE_COLORS['RESET']}"
        )

        # mypy is insane and thinks isatty() is "Any | bool".
        return (
            c
            if self.always_color
            or (
                stdout.isatty() and not DISABLE_COLOR  # type: ignore[misc]
            )
            else self.s
        )

    def __len__(self) -> int:
        return len(self.s)

    @override
    def __repr__(self) -> str:
        return f"<{self.color}-string: '{self.s}'>"

    @override
    def __str__(self) -> str:
        return self.color_str

    def __iter__(self) -> Iterator[str]:
        return iter(self.color_str)

    def __add__(self, other: StringInterpolatable) -> str:
        return str(self.color_str) + str(other)

    def __radd__(self, other: StringInterpolatable) -> str:
        return str(other) + str(self.color_str)

    def __mul__(self, other: SupportsIndex | Iterable[StringInterpolatable]) -> str:
        return (
            self.color_str * other
            if isinstance(other, int | SupportsIndex)
            else (str(*product(self.color_str, other)))
        )

    # Integer like types do not always subclass python's `int`, so not all
    # `slice`s are `int`; e.g. numpy, pandas.
    def __getitem__[I](self, i: SupportsIndex | slice[I, I, I]) -> ColoredString:
        """Handle string indexing and slicing operations.

        Args:
            i (I): the index or slice to get.

        Returns:
            ColoredString of the given index or slice.
        """
        return self._new(self.s[i])

    def _new(self, s: StringInterpolatable) -> ColoredString:
        return ColoredString(self.color, s)


# pylint: disable=too-few-public-methods
@runtime_checkable
class ColorFunction(Protocol):
    """Callback protocol for the color function creating factory method."""

    def __call__(
        self,
        s: StringInterpolatable,
        *,
        always: bool = False,
        bold: bool = False,
    ) -> ColoredString: ...


# pylint: disable=too-few-public-methods
@final
class _ColorFunctions:
    """Factory for terminal color formatting functions.

    This class provides a way to generate color functions with consistent behavior
    and documentation. Each color function wraps text in ANSI escape codes while
    maintaining normal string-like behavior.
    """

    @final
    @staticmethod
    def _make_color_function(
        color: str,
        *,  # Force keyword arguments for clarity
        is_reset: bool = False,
    ) -> ColorFunction:
        """Creates a color function for the specified color.

        Args:
            color (str): The uppercase color name (e.g., "RED", "BLUE")
            is_reset (bool): Whether this is the reset/normal function.

        Returns:
            The named colorizing function.
        """

        def color_func(
            s: StringInterpolatable,
            *,
            always: bool = False,
            bold: bool = False,
        ) -> ColoredString:
            """Creates a colored string that maintains string-like behavior.

            Wraps the input in ANSI escape codes to display it in color when printed to
                a compatible terminal. The resulting ColoredString maintains normal
                string behavior for operations like len(), concatenation, etc.

            Args:
                s (StringInterpolatable): str or ``str()``-convertible value to be
                    colorized.
                always (bool): Force color output even if:
                    a) stdout is not a terminal
                    b) the terminal is detected to not support color output
                    c) color is disabled globally (e.g., ``DISABLE_COLOR``)
                bold (bool): If True, makes the text bold/bright.

            Returns:
                A string-like object that will display in color when printed.

            Examples:
                >>> print(color_func("Text"))  # Prints in color
                >>> print(color_func("Notice!", bold=True))  # Prints in bold
                >>> color_func("Status:") + " normal"  # Concatenation works
            """
            return ColoredString(color, s, always_color=always, bold=bold)

        # Customize the function's identity and documentation
        color_name = "normal" if is_reset else color.lower()
        color_func.__name__ = color_name

        # Special case documentation for the normal/reset function
        if is_reset:
            color_func.__doc__ = """Creates a normalizing/resetting string function.

            Wraps the input in ANSI reset codes to display it in the termimal's default
                color scheme (or lack-thereof) when printed.
            The resulting ColoredString maintains normal string behavior for operations
                like len(), concatenation, etc.

            Args:
                s (StringInterpolatable): str or ``str()``-convertible value to be reset
                always (bool): Force color output even if:
                    a) stdout is not a terminal
                    b) the terminal is detected to not support color output
                    c) color is disabled globally (e.g., ``DISABLE_COLOR``)
                bold (bool): If True, makes the text bold/bright.

            Returns:
                A string-like object that will display in the terminal's default color.

            Examples:
                >>> print(red("Error") + normal(" - details"))  # Only "Error" is red
                >>> print(normal("Regular text"))  # Prints in default color
                >>> normal("Reset:") + " normal text"  # Concatenation works
            """
        # Replace generic color terms with specific ones in the docstring
        elif color_func.__doc__ is not None:
            color_func.__doc__ = color_func.__doc__.replace("color", color_name)
            color_func.__doc__ = color_func.__doc__.replace("COLOR", color)

        return color_func

    # Create color-specific functions
    black = _make_color_function("BLACK")
    blue = _make_color_function("BLUE")
    cyan = _make_color_function("CYAN")
    green = _make_color_function("GREEN")
    magenta = _make_color_function("MAGENTA")
    red = _make_color_function("RED")
    white = _make_color_function("WHITE")
    yellow = _make_color_function("YELLOW")
    lightblack_ex = _make_color_function("LIGHTBLACK_EX")
    lightblue_ex = _make_color_function("LIGHTBLUE_EX")
    lightcyan_ex = _make_color_function("LIGHTCYAN_EX")
    lightgreen_ex = _make_color_function("LIGHTGREEN_EX")
    lightmagenta_ex = _make_color_function("LIGHTMAGENTA_EX")
    lightred_ex = _make_color_function("LIGHTRED_EX")
    lightwhite_ex = _make_color_function("LIGHTWHITE_EX")
    lightyellow_ex = _make_color_function("LIGHTYELLOW_EX")
    normal = _make_color_function("RESET", is_reset=True)


black: ColorFunction = _ColorFunctions.black
blue: ColorFunction = _ColorFunctions.blue
cyan: ColorFunction = _ColorFunctions.cyan
green: ColorFunction = _ColorFunctions.green
magenta: ColorFunction = _ColorFunctions.magenta
red: ColorFunction = _ColorFunctions.red
white: ColorFunction = _ColorFunctions.white
yellow: ColorFunction = _ColorFunctions.yellow
lightblack_ex: ColorFunction = _ColorFunctions.lightblack_ex
lightblue_ex: ColorFunction = _ColorFunctions.lightblue_ex
lightcyan_ex: ColorFunction = _ColorFunctions.lightcyan_ex
lightgreen_ex: ColorFunction = _ColorFunctions.lightgreen_ex
lightmagenta_ex: ColorFunction = _ColorFunctions.lightmagenta_ex
lightred_ex: ColorFunction = _ColorFunctions.lightred_ex
lightwhite_ex: ColorFunction = _ColorFunctions.lightwhite_ex
lightyellow_ex: ColorFunction = _ColorFunctions.lightyellow_ex
normal: ColorFunction = _ColorFunctions.normal


_STRIP: Pattern[str] = re_compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")


def clean(s: str) -> str:
    """Regex substitution helper.

    Args:
        s (str): the str to process.

    Returns:
        ``s`` with anything matching the ``_STRIP`` pattern removed from it.
    """
    return _STRIP.sub("", s)


def random(
    s: StringInterpolatable,
    always: bool = False,  # noqa: FBT001, FBT002
    bold: bool = False,  # noqa: FBT001, FBT002
    colors: Iterable[str] | Sequence[str] = COLORS,
) -> ColoredString:
    """Selects a color at random from `COLORS` or a subset of `COLORS`.

    Returns:
        Random instance of ColoredString from `colors`.
    """
    supported_colors: Final[list[str]] = list(
        set(colors).intersection(COLORS) or COLORS,
    )
    random_color: Final[str] = (
        supported_colors[
            randrange(  # noqa: S311
                start=0,
                stop=len(supported_colors),
                step=1,
            )
        ]
    ).upper()
    return ColoredString(
        random_color,
        s,
        always_color=always,
        bold=bold,
    )


def disable() -> None:
    """Disables colors."""
    global DISABLE_COLOR

    DISABLE_COLOR = True  # pyright: ignore[reportConstantRedefinition]


def enable() -> None:
    """Enables colors."""
    global DISABLE_COLOR

    DISABLE_COLOR = False  # pyright: ignore[reportConstantRedefinition]


def replace_colors(replace_dict: dict[str, str]) -> None:
    """Replace colors to customize the look under a specific background."""
    global REPLACE_COLORS

    try:
        REPLACE_COLORS = {  # pyright: ignore[reportConstantRedefinition]
            k.upper(): v.upper() for k, v in replace_dict.items()
        }
    except AttributeError:
        _: int = stderr.write(
            "Warning: replace_colors had no effect, because the replace_dict "
            f"parameter ({type(replace_dict)}) should be a dict[str, str].\n",
        )


def reset_replace_colors() -> None:
    """Reinitialize ``REPLACE_COLORS`` to an empty dict."""
    global REPLACE_COLORS

    REPLACE_COLORS = {}  # pyright: ignore[reportConstantRedefinition]


__all__ = [
    "COLORS",
    "black",
    "blue",
    "clean",
    "cyan",
    "disable",
    "enable",
    "green",
    "lightblack_ex",
    "lightblue_ex",
    "lightcyan_ex",
    "lightgreen_ex",
    "lightmagenta_ex",
    "lightred_ex",
    "lightwhite_ex",
    "lightyellow_ex",
    "magenta",
    "normal",
    "normal",
    "random",
    "red",
    "replace_colors",
    "reset_replace_colors",
    "white",
    "yellow",
]
