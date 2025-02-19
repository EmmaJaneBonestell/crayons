"""A simple and elegant wrapper for colorama.

Attributes:
    DISABLE_COLOR (bool): Autodetected color support of terminal.
        Manually overridable with `enable()` and `disable()`.
"""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

# pylint: disable=consider-using-assignment-expr,global-statement
# ruff: noqa: PLW0603
from __future__ import annotations

from collections import UserString
from collections.abc import Mapping, Sequence
from contextlib import suppress
from inspect import currentframe
from itertools import product
from os import environ
from random import randrange, seed as random_seed
from re import VERBOSE as RE_VERBOSE, compile as re_compile
from sys import stderr, stdout
from typing import (
    TYPE_CHECKING,
    Final,
    Protocol,
    Self,
    SupportsIndex,
    cast,
    final,
    override,
    runtime_checkable,
)

from colorama import init as colorama_init

from ._types import FORE_COLORS, STYLES, ColoredStringABC

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator
    from re import Match, Pattern
    from types import FrameType
    from typing import Any

    from ._types import StrInterpolable


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
DISABLE_COLOR: bool
REPLACE_COLORS: dict[str, str] = {}
random_seed()


def _should_default_disable_color() -> bool:
    cur_frame: Final[FrameType | None] = currentframe()
    if cur_frame:
        bk_frame: FrameType | None = cur_frame.f_back
        if bk_frame:
            if "get_ipython" in bk_frame.f_globals:  # type: ignore[misc]
                return True
            this_module_name: Final[str] = bk_frame.f_globals.get(  # type: ignore[misc]
                "__name__",
                "",
            )
            # Skip past our own module's frames to get to caller's context
            while (
                bk_frame
                and bk_frame.f_globals.get("__name__", "")  # type: ignore[misc]
                == this_module_name
            ):
                bk_frame = bk_frame.f_back
                if not bk_frame:  # pragma: no cover
                    return False
            return (
                "get_ipython" in bk_frame.f_globals  # type: ignore[misc]
                or environ.get("TERM", None) == "dumb"
            )
    return False  # pragma: no cover


def __getattr__(name: str) -> bool:
    if name == "DISABLE_COLOR":
        try:
            return DISABLE_COLOR
        except NameError:  # pragma: no cover
            return _should_default_disable_color()
    msg: Final[str] = (
        "DISABLE_COLOR is the only module-level attribute set in crayons. "
        "It is exposed for backwards compatibility."
    )
    raise AttributeError(msg)


_ANSI_ESCAPE_REGEX: Final[Pattern[str]] = re_compile(
    r"""(?:\x1b\[[0-9]+m){2} # the first two ANSI esc seqs
            (?:(?!\x1b)+.*)+     # anything not starting with esc seq
            (?:\x1b\[[0-9]+m){2} # the last two ANSI esc seqs""",
    RE_VERBOSE,
)

_STRIP: Final[Pattern[str]] = re_compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")


@final
class ColoredString(ColoredStringABC):
    """Maintains colored output strings and normal string manipulation."""

    __slots__: Final[tuple[str, str, str, str]] = ("always_color", "bold", "color", "s")

    @final
    def __init__(
        self,
        color: str,
        s: StrInterpolable,
        always_color: bool = False,  # noqa: FBT001, FBT002
        bold: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """Init a ColoredString.

        Raises:
            KeyError: when an invalid/unsupported color name is passed
            TypeError: when color could not be turned into a str
        """
        not_str_msg: Final[str] = "Failed to convert input to string.\n"
        keyerr_msg: Final[str] = rf"Invalid color name ({color}) requested.\\n"
        if color.upper() not in FORE_COLORS:
            raise KeyError(keyerr_msg)
        # pylint: disable=too-many-try-statements
        try:
            if not isinstance(s.__str__(), str):
                raise TypeError(not_str_msg)  # noqa: TRY301
        except (NotImplementedError, AttributeError, TypeError) as e:
            raise TypeError(not_str_msg) from e

        # Protocol runtime_checkable does not validate return type, hence the above.
        self.s: StrInterpolable = (
            str(s, encoding="utf-8") if isinstance(s, bytes) else s
        )

        self.color: str = REPLACE_COLORS.get(color, color)
        self.always_color: bool = always_color
        self.bold: bool = bold
        if environ.get("CLINT_FORCE_COLOR", None):
            self.always_color = True

        super().__init__(
            color=self.color,
            s=self.s,
            always_color=self.always_color,
            bold=self.bold,
        )

    @final
    def __getattr__(
        self,
        att: str,
    ) -> StrInterpolable | Collection[StrInterpolable]:  # noqa: C901,RUF100
        # pylint: disable=too-many-return-statements
        def func_help(  # type: ignore[explicit-any] # noqa: PLR0911
            *args: Any,  # noqa: ANN401
            **kwargs: Any,  # noqa: ANN401
        ) -> StrInterpolable | Collection[StrInterpolable]:
            """Create ColoredString instances.

            Returns:
                the ColoredString interpolation.
            """

            # pylint: disable=unused-argument  # matching signature
            def ret_none(  # type: ignore[explicit-any]
                *args: Any,  # noqa: ANN401,ARG001
                **kwargs: Any,  # noqa: ANN401,ARG001
            ) -> None:
                return None

            result: StrInterpolable | Collection[StrInterpolable] = getattr(
                self.s,
                att,
                ret_none,  # type: ignore[misc]
            )(*args, **kwargs)  # type: ignore[misc]
            # The casts are for pyright, which seems to have trouble
            # inferring the generic subtype.
            match result:
                case str() | UserString():
                    return self._new(result)
                case bytearray() | bytes():
                    return result
                case tuple():
                    return tuple(
                        self._new(x)
                        for x in cast(
                            "tuple[StrInterpolable, StrInterpolable, StrInterpolable]",
                            result,
                        )
                    )
                case list() | Sequence():
                    return [
                        self._new(x) for x in cast("Sequence[StrInterpolable]", result)
                    ]
                case frozenset():
                    return frozenset({
                        self._new(x) for x in cast("frozenset[StrInterpolable]", result)
                    })
                case set():
                    return {self._new(x) for x in cast("set[StrInterpolable]", result)}
                case dict() | Mapping():
                    return {
                        self._new(k): self._new(v)
                        for (k, v) in cast(
                            "Mapping[StrInterpolable, StrInterpolable]",
                            result,
                        ).items()
                    }
                case _:
                    return result

        # mypy incorrectly warns about an inferred Callable containing an Any here;
        # StrInterpolable subsumes any such Callable.
        return func_help  # type: ignore[misc]

    @property
    @final
    def color_str(self) -> str:
        """Colorama instantiating wrapper."""

        def format_match(match: Match[str]) -> str:
            return (
                f"{match.group()}{FORE_COLORS[self.color.upper()]}"
                f"{STYLES[style]}"
            )  # pragma: no cover

        style: Final[str] = "BRIGHT" if self.bold else "NORMAL"
        c: Final[str] = (
            f"{FORE_COLORS[self.color.upper()]}{STYLES[style]}"
            f"{_ANSI_ESCAPE_REGEX.sub(format_match, str(self.s))}"
            f"{STYLES['NORMAL']}{FORE_COLORS['RESET']}"
        )

        # mypy is insane and thinks isatty() is "Any | bool".
        return (
            c
            if self.always_color
            or (
                stdout.isatty()  # type: ignore[misc]
                and not __getattr__("DISABLE_COLOR")
            )
            else str(self.s)
        )

    @final
    def __len__(self) -> int:
        return len(str(self.s))

    @override
    @final
    def __repr__(self) -> str:
        return f"<{self.color}-string: '{self.s}'>"

    @override
    @final
    def __str__(self) -> str:
        return self.color_str

    @final
    def __iter__(self) -> Iterator[str]:
        return iter(self.color_str)

    @final
    def __add__(self, other: StrInterpolable) -> str:
        return str(self.color_str) + str(other)

    @final
    def __radd__(self, other: StrInterpolable) -> str:
        return str(other) + str(self.color_str)

    @final
    def __mul__(self, other: SupportsIndex | Iterable[StrInterpolable]) -> Self:
        """Provide standard str*int, and also cartesian multiplication for iterables.

        Returns:
            `self.color_str` repeated n/`other` times, or, for Iterable `other`,
            returns a joined `str` of `product(self.color_str, other)`.

        Examples:
            >>> print(crayons.red("ABC") * 3)
            "ABCABCABC"
            >>> print(crayons.red("ABC") * ["D", "E", "F", "G"])
            "ADAEAFAGBDBEBFBGCDCECFCG"
        """
        return self._new(
            ""
            if not self.color_str or not other
            else self.color_str * other
            if isinstance(other, int | SupportsIndex)
            else "".join(a + str(b) for a, b in product(self.color_str, other)),
        )

    @final
    def __rmul__(self, other: SupportsIndex | Iterable[StrInterpolable]) -> Self:
        return self._new(
            ""
            if not self.color_str or not other
            else self.color_str * other
            if isinstance(other, int | SupportsIndex)
            else "".join(a + str(b) for a, b in product(self.color_str, other)),
        )

    __rmul__.__doc__ = __mul__.__doc__

    @final
    def _new(self, s: StrInterpolable) -> ColoredString:
        return ColoredString(
            color=self.color,
            s=s,
            always_color=self.always_color,
            bold=self.bold,
        )


# pylint: disable=too-few-public-methods
@runtime_checkable
class ColorFunction(Protocol):
    """Callback protocol for the color function creating factory method."""

    def __call__(
        self,
        s: StrInterpolable,
        *,
        always: bool = False,
        bold: bool = False,
    ) -> ColoredString: ...  # pragma: no cover


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
        """Create a color function for the specified color.

        Args:
            color (str): The uppercase color name (e.g., "RED", "BLUE")
            is_reset (bool): Whether this is the reset/normal function.

        Returns:
            The named colorizing function.
        """

        def color_func(
            s: StrInterpolable,
            *,
            always: bool = False,
            bold: bool = False,
        ) -> ColoredString:
            """Create a ColorString that maintains string compatibility witj str.

            Wraps the input in ANSI escape codes to display it in color when printed to
                a compatible terminal. The resulting ColoredString maintains normal
                string behavior for operations like len(), concatenation, etc.

            Args:
                s (StrInterpolable): str or ``str()``-convertible value.
                always (bool): Force ANSI escape output even if:
                    a) stdout is not a terminal
                    b) the terminal is detected to not support it
                    c) it is disabled globally (e.g., ``DISABLE_COLOR``)
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

            Wraps the input in ANSI reset codes to display it in the terminal's default
                color scheme (or lack-thereof) when printed.
            The resulting ColoredString maintains normal string behavior for operations
                like len(), concatenation, etc.

            Args:
                s (StrInterpolable): str or ``str()``-convertible value to be reset
                always (bool): Force color output even if:
                    a) stdout is not a terminal
                    b) the terminal is detected to not support color output
                    c) color is disabled globally (e.g., ``DISABLE_COLOR``)
                bold (bool): If True, makes the text bold/bright.

            Returns:
                A string-like object that will display in the terminal's default color.

            Examples:
                >>> print(red("Error") + normal(" - details"))  # Only "Error" is red
                >>> print(normal("Regular text"))  # Prints with terminal default
                >>> normal("Reset:") + " normal text"  # Concatenation works
            """
        # Replace generic color terms with specific ones in the docstring
        elif color_func.__doc__:  # pragma: no cover
            color_func.__doc__ = color_func.__doc__.replace("color", color_name)

        return color_func

    # Create color-specific functions
    # pylint: disable=invalid-name
    black: Final[ColorFunction] = _make_color_function("BLACK")
    blue: Final[ColorFunction] = _make_color_function("BLUE")
    cyan: Final[ColorFunction] = _make_color_function("CYAN")
    green: Final[ColorFunction] = _make_color_function("GREEN")
    magenta: Final[ColorFunction] = _make_color_function("MAGENTA")
    red: Final[ColorFunction] = _make_color_function("RED")
    white: Final[ColorFunction] = _make_color_function("WHITE")
    yellow: Final[ColorFunction] = _make_color_function("YELLOW")
    lightblack_ex: Final[ColorFunction] = _make_color_function("LIGHTBLACK_EX")
    lightblue_ex: Final[ColorFunction] = _make_color_function("LIGHTBLUE_EX")
    lightcyan_ex: Final[ColorFunction] = _make_color_function("LIGHTCYAN_EX")
    lightgreen_ex: Final[ColorFunction] = _make_color_function("LIGHTGREEN_EX")
    lightmagenta_ex: Final[ColorFunction] = _make_color_function("LIGHTMAGENTA_EX")
    lightred_ex: Final[ColorFunction] = _make_color_function("LIGHTRED_EX")
    lightwhite_ex: Final[ColorFunction] = _make_color_function("LIGHTWHITE_EX")
    lightyellow_ex: Final[ColorFunction] = _make_color_function("LIGHTYELLOW_EX")
    normal: Final[ColorFunction] = _make_color_function("RESET", is_reset=True)


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


def clean(s: str) -> str:
    """Regex substitution helper.

    Args:
        s (str): the str to process.

    Returns:
        ``s`` with anything matching the ``_STRIP`` pattern removed from it.
    """
    return _STRIP.sub("", s)


def random(
    s: StrInterpolable,
    always: bool = False,  # noqa: FBT001, FBT002
    bold: bool = False,  # noqa: FBT001, FBT002
    colors: Iterable[str] | Sequence[str] = COLORS,
) -> ColoredString:
    """Select a color at random from `COLORS` or a subset of `COLORS`.

    Returns:
        Random instance of ColoredString from `colors`.
    """
    supported_colors: Final[list[str]] = list(
        {clr.lower() for clr in colors}.intersection(COLORS) or COLORS,
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
    """Enable colors."""
    global DISABLE_COLOR

    DISABLE_COLOR = False  # pyright: ignore[reportConstantRedefinition]


def replace_colors(replace_dict: dict[str, str]) -> None:
    """Replace colors to customize the look under a specific background.

    Raises:
       KeyError: when any `replace_dict` key is an unsupported color name
    """
    global REPLACE_COLORS
    # Kept for partial backwards compatibility where non-dicts were not
    # strictly rejected; does nothing instead of raising an error.
    if not isinstance(replace_dict, dict):
        no_effect_msg: Final[str] = (  # type: ignore[unreachable]
            "Warning: replace_colors had no effect, because the replace_dict "
            f"parameter ({type(replace_dict)}) should be a dict[str, str].\n"
        )
        _: int = stderr.write(no_effect_msg)
        return

    # Find the first value that is invalid, or default to a falsey, empty
    # string when all are valid.
    with suppress(StopIteration):
        invalid: Final[str] = next(
            (val for val in replace_dict.values() if val.upper() not in FORE_COLORS),
            "",  # default
        )

    if invalid:
        msg: Final[str] = f"Invalid color name ({invalid}) requested for replacement.\n"
        raise KeyError(msg)

    REPLACE_COLORS = {  # pyright: ignore[reportConstantRedefinition]
        k.upper(): v.upper() for k, v in replace_dict.items()
    }


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
    "random",
    "red",
    "replace_colors",
    "reset_replace_colors",
    "white",
    "yellow",
]
