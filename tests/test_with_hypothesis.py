"""Property-based tests for the crayons package."""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

# pylint: disable=confusing-consecutive-elif,line-too-long,missing-function-docstring
# pylint: disable=no-self-use,too-many-try-statements
# pylint: disable=use-implicit-booleaness-not-comparison-to-zero  # ridiculous length
# ruff: noqa: ANN401,C901,D102,D105,DOC201,DOC501,PLC2701,PLR6301

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from importlib.util import find_spec
from itertools import product
from os import environ
from sys import modules, stdout
from typing import TYPE_CHECKING, Any, Never, assert_never, cast, override

import pytest
from hypothesis import event, given, settings, strategies as st, target

from crayons import COLORS, enable, random, replace_colors, reset_replace_colors, yellow
from crayons._types import FORE_COLORS, STYLES
from crayons.crayons import (
    _ANSI_ESCAPE_REGEX,  # pyright: ignore[reportPrivateUsage]
    ColoredString,
    _ColorFunctions,  # pyright: ignore[reportPrivateUsage]
    _should_default_disable_color,  # pyright: ignore[reportPrivateUsage]
)

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
        Collection,
        Generator,
    )  # pragma: no cover
    from typing import Final, Literal, SupportsIndex  # pragma: no cover

    from hypothesis.strategies import (
        DataObject,  # pragms: no cover
        DrawFn,  # pragma: no cover
        SearchStrategy,  # prsgma: no cover
    )

    from crayons.crayons import ColorFunction

    type ArgsStrategy = SearchStrategy[
        tuple[()]
        | tuple[str | list[str], int | None, int | None]
        | tuple[int, str]
        | tuple[str | None, int]
        | tuple[str | None]
        | tuple[str]
        | tuple[str, str]
        | tuple[int]
        | tuple[list[str]]
        | tuple[str, str, int]
        | tuple[dict[int, int | None]]
    ]
    type CallableSliceType = Callable[
        [int | None, int | None, int | None],
        slice[int | None, int | None, int | None],
    ]
    type SliceType = slice[int | None, int | None, int | None]


BLACKLIST: Final[Collection[Literal["Cs"]]] = {"Cs"}
COLOR_STRATEGY: Final[SearchStrategy[str]] = st.sampled_from(
    list(FORE_COLORS.keys()),
)
TEXT_STRATEGY: Final[SearchStrategy[str]] = st.text(
    alphabet=st.characters(blacklist_categories=BLACKLIST, codec="utf-8"),
)
VALID_COLORS: Final[SearchStrategy[list[str]]] = st.sampled_from(
    cast("list[str]", sorted(COLORS)),
)


# Classes that intentionally violate StringInterpolatable
@dataclass  # type: ignore[misc]
class BadReturnType:  # type: ignore[explicit-any,misc]
    """Class with __str__ that returns non-str, violating StringInterpolatable."""

    val: Any  # type: ignore[explicit-any]

    @override
    def __str__(self) -> Any:  # type: ignore[explicit-any,misc]
        return self.val  # type: ignore[misc]


@dataclass
class ExtraArgStr:
    """Class with __str__ that takes extra arguments, violating StringInterpolatable."""

    val: str

    @override
    def __str__(self, extra: Any = None) -> str:  # type: ignore[explicit-any,misc]
        msg = "Failed to convert input to string."
        if not extra:  # type: ignore[misc]
            raise TypeError(msg)
        return self.val  # pragma: no cover


@dataclass
class RaisingStr:
    """Class with __str__ that raises an exception."""

    # pylint: disable=invalid-str-returned
    @override
    def __str__(self) -> Never:
        msg = "I always fail"
        raise ValueError(msg)


# Strategy for generating invalid StringInterpolatable objects
@st.composite  # type: ignore[misc]
def invalid_stringables(draw: st.DrawFn) -> Any:  # type: ignore[explicit-any,misc]
    """Generate objects that intentionally violate StringInterpolatable."""
    kind = draw(st.integers(min_value=0, max_value=3))
    match kind:
        case 0:  # Returns non-str types
            val = draw(
                st.one_of(
                    st.none(),
                    st.integers(),
                    st.lists(st.integers()),
                    st.dictionaries(st.text(), st.integers()),
                ),
            )
            return BadReturnType(val)
        case 1:  # Takes extra arguments
            return ExtraArgStr(draw(st.text()))
        case 2:  # Raises exception
            return RaisingStr()
        case _:  # Dynamic bad class
            return type(  # type: ignore[misc]
                "DynamicBad",
                (),
                {"__str__": lambda _self: draw(st.integers())},  # type: ignore[misc] # pyright: ignore[reportUnknownLambdaType]
            )()


@contextmanager
def terminal_context() -> Generator[None]:
    """Context manager for terminal environment simulation."""
    original_isatty = stdout.isatty  # type: ignore[misc]
    original_env = dict(environ)
    original_disable = modules["crayons"].crayons.DISABLE_COLOR  # type: ignore[misc]

    # pylint: disable=too-many-try-statements
    try:
        stdout.isatty = lambda: True  # type: ignore[method-assign]
        enable()
        yield
    finally:
        stdout.isatty = original_isatty  # type: ignore[method-assign]
        environ.clear()
        environ.update(original_env)
        modules["crayons"].crayons.DISABLE_COLOR = original_disable  # type: ignore[misc]
        reset_replace_colors()


class TestColoredString:
    """Test suite for ColoredString class."""

    @given(color=st.sampled_from(sorted(COLORS)), text=st.text())  # type: ignore[misc]
    def test_valid_string_creation(self, color: str, text: str) -> None:  # type: ignore[misc]
        """Test ColoredString creation with valid strings."""
        with terminal_context():
            # Test both cases
            for case in (str.upper, str.lower):
                colored = ColoredString(case(color), text)
                if not isinstance(colored.s, str):  # pyright: ignore[reportUnnecessaryIsInstance]
                    raise TypeError  # pragma: no cover
                result = str(colored)
                if not isinstance(result, str):  # pyright: ignore[reportUnnecessaryIsInstance]
                    raise TypeError  # pragma: no cover
                # Color codes should be present since terminal is enabled
                if FORE_COLORS[color.upper()] not in result:
                    raise AssertionError  # pragma: no cover

    @given(text=invalid_stringables())  # type: ignore[misc]
    def test_invalid_string_types(self, text: Any) -> None:  # type: ignore[explicit-any,misc]
        """Test that invalid StringInterpolatable implementations fail appropriately."""
        with pytest.raises(
            (ValueError, TypeError),
            match=(r"I always fail|Failed to convert input to string."),
        ):
            _ = ColoredString("RED", text)  # type: ignore[misc]
        with pytest.raises(
            (KeyError, TypeError),
            match=(
                r"Invalid color name .* requested.|Failed to convert input to string."
            ),
        ):
            _ = ColoredString("INVALID_COLOR", "Does not matter")

    def test_invalid_color_replacement(self) -> None:
        """Test behavior with invalid color replacements."""
        with pytest.raises(KeyError), terminal_context():
            replace_colors({"RED": "INVALID_COLOR"})

    def test_ansi_regex_patterns(self) -> None:
        """Test ANSI escape code regex patterns."""
        # Valid pattern: two ANSI codes + content + two ANSI codes
        valid = (
            f"{FORE_COLORS['RED']}{STYLES['NORMAL']}"
            "text"
            f"{FORE_COLORS['RED']}{STYLES['NORMAL']}"
        )
        if not _ANSI_ESCAPE_REGEX.search(valid):
            raise AssertionError  # pragma: no cover

        # Invalid patterns
        invalid_patterns = [
            "\x1b[",  # Incomplete sequence
            "[31m",  # Missing escape
            "\x1b[31m",  # Single sequence
            f"{FORE_COLORS['RED']}text",  # Missing second sequence
        ]
        for pattern in invalid_patterns:
            if _ANSI_ESCAPE_REGEX.search(pattern):
                raise AssertionError  # pragma: no cover

    @given(text=st.text())  # type: ignore[misc]
    def test_random_colors(self, text: str) -> None:  # type: ignore[misc]
        """Test random color selection."""
        with terminal_context():
            # Default random should use full color set
            colored = random(text)
            if colored.color.lower() not in COLORS:
                raise AssertionError  # pragma: no cover
            if FORE_COLORS[colored.color] not in str(colored):
                raise AssertionError  # pragma: no cover

            # Test with specific colors
            subset = ["RED", "BLUE"]
            colored_subset = random(text, colors=[s.upper() for s in subset])
            if colored_subset.color not in subset:
                raise AssertionError  # pragma: no cover
            if FORE_COLORS[colored_subset.color] not in str(colored_subset):
                raise AssertionError  # pragma: no cover

            # Test with empty
            if not random("test", colors=[]):
                raise AssertionError  # pragma: no cover

            # Test with invalid
            if not random("test", colors=["INVALID_COLOR"]):
                raise AssertionError  # pragma: no cover

    def test_clint_force_color(self) -> None:
        """Test CLINT_FORCE_COLOR environment variable."""
        # Test with CLINT_FORCE_COLOR set
        environ["CLINT_FORCE_COLOR"] = "1"
        colored = ColoredString("RED", "test")
        if colored.always_color is False:
            raise AssertionError  # pragma: no cover

        # Clean up
        del environ["CLINT_FORCE_COLOR"]

    @given(  # type: ignore[misc]
        color=VALID_COLORS,
        text1=st.text(),
        text2=st.text(),
        multiplier=st.integers(min_value=0, max_value=10),
    )
    def test_string_operations(  # type: ignore[misc]
        self,
        color: str,
        text1: str,
        text2: str,
        multiplier: int,
    ) -> None:
        # Create our colored string instance
        colored = ColoredString(color.upper(), text1)

        # Test string representation
        # Note: color is always stored uppercase internally
        if repr(colored) != f"<{color.upper()}-string: '{text1}'>":
            raise AssertionError  # pragma: no cover

        # Test iteration - should match the color_str character by character
        if list(colored) != list(colored.color_str):
            raise AssertionError  # pragma: no cover

        # Test string concatenation in both directions
        if str(colored + text2) != str(colored.color_str) + text2:
            raise AssertionError  # pragma: no cover
        if str(text2 + colored) != text2 + str(colored.color_str):
            raise AssertionError  # pragma: no cover

        # Test multiplication with integer
        if str(colored * multiplier) != str(colored.color_str) * multiplier:
            raise AssertionError  # pragma: no cover

        if multiplier * colored != colored * multiplier:
            raise AssertionError  # pragma: no cover

        # Test multiplication with iterable
        expected = "".join(a + b for a, b in product(colored.color_str, [text2]))
        if str(colored * [text2]) != expected:
            raise AssertionError  # pragma: no cover

    @given(st.text(), st.integers(min_value=0, max_value=100))  # type: ignore[misc]
    def test_string_indexing(self, text: str, index: int) -> None:  # type: ignore[misc]
        """Test string indexing and slicing."""
        if not text:
            return

        colored = ColoredString("RED", text)

        # Test single index
        if index < len(text):
            sliced = colored[index]
            if not isinstance(sliced, ColoredString):
                raise TypeError  # pragma: no cover
            if sliced.s != text[index]:
                raise AssertionError  # pragma: no cover

        # Test slicing
        sliced = colored[0:2]
        if not isinstance(sliced, ColoredString):
            raise TypeError  # pragma: no cover
        if sliced.s != text[0:2]:
            raise AssertionError  # pragma: no cover

    def test_getattr_returns(self) -> None:
        """Test different return types from __getattr__."""
        colored = ColoredString("RED", "test,string")

        # Test split returning list
        split_result = colored.split(",")
        if not all(isinstance(x, ColoredString) for x in split_result):
            raise TypeError  # pragma: no cover

        # Test partition returning tuple
        part_result = colored.partition(",")
        if not all(isinstance(x, ColoredString) for x in part_result):
            raise TypeError  # pragma: no cover

        # Test encode returning bytes
        encoded = colored.encode()
        if not isinstance(encoded, bytes):
            raise TypeError  # pragma: no cover

        # Test methods returning set/frozenset
        text_with_dups = ColoredString("RED", "hello hello world")
        words = text_with_dups.split()
        word_set = set(words)
        if not all(isinstance(x, ColoredString) for x in word_set):
            raise TypeError  # pragma: no cover

    def test_replace_colors_error(self) -> None:
        """Test replace_colors with invalid input."""
        # Test with non-dict type
        invalid_type = ["RED", "BLUE"]
        replace_colors(invalid_type)  # type: ignore[arg-type]  # intentionally bad

        # Test with dict containing invalid color
        with pytest.raises(KeyError):
            replace_colors({"RED": "INVALID_COLOR"})

    @given(st.text())  # type: ignore[misc]
    def test_string_methods_chain(self, text: str) -> None:  # type: ignore[misc]
        """Test chaining of string methods."""
        if not text:
            return

        colored = ColoredString("RED", text)

        # Test method chaining
        result = colored.upper().lower()
        if not isinstance(result, ColoredString):
            raise TypeError  # pragma: no cover
        if result.s != text.upper().lower():
            raise AssertionError  # pragma: no cover

        # Test methods returning dict
        translation = colored.maketrans("a", "b")
        if not isinstance(translation, dict):
            raise TypeError  # pragma: no cover


@st.composite  # type: ignore[misc]
def colored_string_strategy(draw: DrawFn) -> ColoredString:
    """Generate valid ColoredString instances."""
    color: Final[str] = draw(COLOR_STRATEGY)
    text: Final[str] = draw(TEXT_STRATEGY)
    always_color: Final[bool] = draw(st.booleans())
    bold: Final[bool] = draw(st.booleans())
    return ColoredString(color, text, always_color=always_color, bold=bold)


# Group all string methods by their argument patterns
METHOD_GROUPS: Final[dict[str, list[str]]] = {
    "no_args": [
        "capitalize",
        "casefold",
        "lower",
        "upper",
        "strip",
        "swapcase",
        "title",
        "isalpha",
        "isalnum",
        "isascii",
        "isdecimal",
        "isdigit",
        "isidentifier",
        "islower",
        "isnumeric",
        "isprintable",
        "isspace",
        "istitle",
        "isupper",
    ],
    "sub_start_end": [
        "count",
        "find",
        "index",
        "rfind",
        "rindex",
        "endswith",
        "startswith",
    ],
    "width_fill": ["center", "ljust", "rjust", "zfill"],
    "split_maxsplit": ["split", "rsplit"],
    "strip_chars": ["strip", "lstrip", "rstrip"],
    "prefix_suffix": ["removeprefix", "removesuffix"],
    "special": [
        "encode",
        "expandtabs",
        "format",
        "format_map",
        "join",
        "partition",
        "rpartition",
        "replace",
        "splitlines",
        "translate",
    ],
}


# Argument strategies for each method group
# pylint: disable=too-many-branches,too-many-return-statements
def get_args_strategy(method_name: str) -> ArgsStrategy:  # noqa: PLR0911,PLR0912
    """Generate appropriate arguments for a given method."""
    if method_name in METHOD_GROUPS["no_args"]:
        return st.tuples()

    if method_name in METHOD_GROUPS["sub_start_end"]:
        sub: SearchStrategy[str | list[str]] = (
            TEXT_STRATEGY
            if method_name not in {"endswith", "startswith"}
            else st.one_of(TEXT_STRATEGY, st.lists(TEXT_STRATEGY).map(tuple))  # type: ignore[arg-type]
        )
        return cast(
            "SearchStrategy[tuple[str | list[str], int | None, int | None]]",
            st.tuples(
                sub,
                cast(
                    "SearchStrategy[int | None]",
                    st.integers(min_value=0, max_value=1023) | st.none(),
                ),
                cast(
                    "SearchStrategy[int | None]",
                    st.integers(min_value=0, max_value=1023) | st.none(),
                ),
            ),
        )

    if method_name in METHOD_GROUPS["width_fill"]:
        return cast(
            "SearchStrategy[tuple[int, str]]",
            st.tuples(
                st.integers(min_value=0, max_value=1023),
                st.text(min_size=1, max_size=1)
                if method_name != "zfill"
                else cast("SearchStrategy[str]", st.just(" ")),
            ),
        )

    if method_name in METHOD_GROUPS["split_maxsplit"]:
        return cast(
            "SearchStrategy[tuple[str | None, int]]",
            st.tuples(
                cast("SearchStrategy[str | None]", st.none() | TEXT_STRATEGY),
                st.integers(min_value=-1, max_value=1023),
            ),
        )

    if method_name in METHOD_GROUPS["strip_chars"]:
        return cast(
            "SearchStrategy[tuple[str | None]]",
            st.tuples(cast("SearchStrategy[str | None]", st.none() | TEXT_STRATEGY)),
        )

    if method_name in METHOD_GROUPS["prefix_suffix"]:
        return cast("SearchStrategy[tuple[str]]", st.tuples(TEXT_STRATEGY))

    if method_name == "encode":
        return cast(
            "SearchStrategy[tuple[str, str]]",
            st.tuples(
                cast(
                    "SearchStrategy[str]",
                    st.sampled_from(cast("list[str]", ["utf-8", "ascii"])),
                ),
                cast(
                    "SearchStrategy[str]",
                    st.sampled_from(cast("list[str]", ["strict", "ignore", "replace"])),
                ),
            ),
        )

    if method_name == "expandtabs":
        return cast(
            "SearchStrategy[tuple[int]]",
            st.tuples(st.integers(min_value=0, max_value=1023)),
        )

    if method_name in {"format", "format_map"}:
        # Generate simple format strings and matching args/kwargs
        format_str: SearchStrategy[str] = st.text(
            alphabet=st.characters(blacklist_categories=BLACKLIST),
        )
        return cast("SearchStrategy[tuple[str]]", st.tuples(format_str))

    if method_name == "join":
        return cast(
            "SearchStrategy[tuple[list[str]]]",
            st.tuples(cast("SearchStrategy[list[str]]", st.lists(TEXT_STRATEGY))),
        )

    if method_name in {"partition", "rpartition"}:
        return cast("SearchStrategy[tuple[str]]", st.tuples(TEXT_STRATEGY))

    if method_name == "replace":
        return cast(
            "SearchStrategy[tuple[str, str, int]]",
            st.tuples(
                TEXT_STRATEGY,
                TEXT_STRATEGY,
                st.integers(min_value=-1, max_value=1023),
            ),
        )

    if method_name == "splitlines":
        return cast("SearchStrategy[tuple[bool]]", st.tuples(st.booleans()))

    if method_name == "translate":
        # Generate a simple translation table
        return cast(
            "SearchStrategy[tuple[dict[int, int | None]]]",
            st.tuples(
                cast(
                    "SearchStrategy[dict[int, int | None]]",
                    st.dictionaries(
                        keys=st.integers(min_value=0, max_value=1023),
                        values=cast(
                            "SearchStrategy[int | None]",
                            st.integers(min_value=0, max_value=1023) | st.none(),
                        ),
                    ),
                ),
            ),
        )

    return st.tuples()  # pragma: no coverage  # default


@settings(max_examples=1000, deadline=None)  # type: ignore[misc]
@given(colored_string_strategy(), st.data())  # type: ignore[misc]
def test_all_string_methods(colored_str: ColoredString, data: DataObject) -> None:  # type: ignore[misc]
    """Test all string methods of ColoredString."""
    # Get a flat list of all methods
    all_methods: list[str] = [m for methods in METHOD_GROUPS.values() for m in methods]

    # Choose a method to test
    method_name: str = data.draw(st.sampled_from(all_methods))
    event(f"testing method: {method_name}")
    target(all_methods.index(method_name), label=f"method index: {method_name}")

    # Get the method from both str and ColoredString
    str_method: Callable = getattr(str, method_name)  # type: ignore[type-arg]
    colored_method: Callable = getattr(colored_str, method_name)  # type: ignore[type-arg]

    # Draw appropriate arguments for this method
    args = data.draw(get_args_strategy(method_name))

    try:
        # Apply the method to both str and ColoredString
        str_result = str_method(str(colored_str.s), *args)  # type: ignore[misc]
        colored_result = colored_method(*args)  # type: ignore[misc]

        # Verify results
        if isinstance(str_result, str):  # type: ignore[misc]
            if not isinstance(colored_result, ColoredString):  # type: ignore[misc]
                raise TypeError  # noqa: TRY301  # pragma: no cover
            if str(colored_result.s) != str_result:
                raise AssertionError  # pragma: no cover
            if colored_result.color != colored_str.color:
                raise AssertionError  # pragma: no cover
            if colored_result.always_color != colored_str.always_color:
                raise AssertionError  # pragma: no cover
            if colored_result.bold != colored_str.bold:
                raise AssertionError  # pragma: no cover
        elif colored_result != str_result:  # type: ignore[misc]
            raise AssertionError  # pragma: no cover

    except (ValueError, TypeError) as e:
        with pytest.raises(type(e)):
            colored_method(*args)


# Test all comparison operators
@given(colored_string_strategy(), colored_string_strategy())  # type: ignore[misc]
# pragma: no cover
def test_comparisons(cs1: ColoredString, cs2: ColoredString) -> None:  # type: ignore[misc]
    """Test ColoredString comparison operations."""
    str1, str2 = str(cs1.s), str(cs2.s)
    if (cs1 < cs2) is not (str1 < str2):
        msg_lt: Final[str] = "Less than comparison failed"
        raise AssertionError(msg_lt)
    if (cs1 > cs2) is not (str1 > str2):
        msg_gt: Final[str] = "Greater than comparison failed"
        raise AssertionError(msg_gt)
    if (cs1 <= cs2) is not ((cs1 < cs2) or (cs1 == str(cs2))):
        msg_le: Final[str] = "Less than or equal comparison failed"
        raise AssertionError(msg_le)
    if (cs1 >= cs2) is not ((cs1 > cs2) or (cs1 == str(cs2))):
        msg_ge: Final[str] = "Greater than or equal comparison failed"
        raise AssertionError(msg_ge)
    if (cs1 != cs2) is (cs1 == cs2):
        msg_eq: Final[str] = "Equality/inequality comparison failed"
        raise AssertionError(msg_eq)


def test_lt_gt() -> None:
    """Coverage of equality comparator branches."""

    # pylint: disable=invalid-str-returned,too-few-public-methods
    class BadStr:
        """Invalid type."""

        def __str__(self) -> None:  # type: ignore[override]
            return  # noqa: PLE0307

    cs: Final[ColoredString] = ColoredString("RED", "b")
    if cs > "c":
        raise AssertionError  # pragma: no cover
    if cs < "a":
        raise AssertionError  # pragma: no cover
    with pytest.raises(TypeError, match="__str__ returned non-string"):
        _ = cs < BadStr()  # type: ignore[misc,operator]
    with pytest.raises(TypeError, match="__str__ returned non-string"):
        _ = cs > BadStr()  # type: ignore[misc,operator]


# Test contains operator
@given(colored_string_strategy(), TEXT_STRATEGY)  # type: ignore[misc]
def test_contains(colored_str: ColoredString, substr: str) -> None:  # type: ignore[misc]
    """Test the __contains__ method."""
    if (substr in colored_str) != (substr in str(colored_str.s)):
        raise AssertionError  # pragma: no cover


def _not_zero(x: int) -> bool:
    return x != 0


# Test getitem (indexing and slicing)
@given(  # type: ignore[misc]
    colored_string_strategy(),
    cast(
        "SearchStrategy[int] | SearchStrategy[SliceType]",
        st.one_of(
            st.integers(),
            cast(
                "SearchStrategy[SliceType]",
                st.builds(
                    cast("CallableSliceType", slice),
                    cast("SearchStrategy[int | None]", st.integers() | st.none()),
                    cast("SearchStrategy[int | None]", st.integers() | st.none()),
                    cast(
                        "SearchStrategy[int | None]",
                        st.integers().filter(_not_zero) | st.none(),
                    ),
                ),
            ),
        ),
    ),
)
def test_getitem(colored_str: ColoredString, index: SupportsIndex) -> None:  # type: ignore[misc]
    """Test string indexing and slicing."""
    try:
        result = colored_str[index]
        str_result = str(colored_str.s)[index]

        if isinstance(str_result, str):
            if not isinstance(result, ColoredString):
                raise TypeError  # pragma: no cover
            if str(result.s) != str_result:
                raise AssertionError  # pragma: no cover
            if result.color != colored_str.color:
                raise AssertionError  # pragma: no cover
        elif result != str_result:  # type: ignore[unreachable]  # pragma: no cover
            assert_never(result)
    except IndexError:
        with pytest.raises(IndexError):
            _ = str(colored_str.s)[index]


# Test string modulo operator
@given(colored_string_strategy(), st.text())  # type: ignore[misc]
def test_modulo(colored_str: ColoredString, value: str) -> None:  # type: ignore[misc]
    """Test the __mod__ operator."""
    try:
        result = colored_str % value
        str_result = str(colored_str.s) % value  # pragma: no cover
        if result != str_result:  # pragma: no cover
            raise ValueError  # noqa: TRY301  # pragma: no cover
    except (ValueError, TypeError):
        with pytest.raises((ValueError, TypeError)):
            _ = str(colored_str.s) % value


# Test hash operation
@given(colored_string_strategy())  # type: ignore[misc]
def test_hash(colored_str: ColoredString) -> None:  # type: ignore[misc]
    """Test that hash is consistent with the object's content."""
    # Same content should hash the same
    clone = ColoredString(
        colored_str.color,
        colored_str.s,
        colored_str.always_color,
        colored_str.bold,
    )
    if hash(colored_str) != hash(clone):
        raise AssertionError  # pragma: no cover

    # Different content should hash differently
    if colored_str.s:  # Only test if we have a non-empty string
        different = ColoredString(
            colored_str.color,
            str(colored_str.s) + "x",
            colored_str.always_color,
            colored_str.bold,
        )
        if hash(colored_str) == hash(different):
            raise AssertionError  # pragma: no cover


# pylint: disable=protected-access
def test_private_factory_coverage() -> None:
    """Quick tests, mostly for coverage."""
    yellow_test: Final[ColorFunction] = _ColorFunctions._make_color_function(  # noqa: SLF001
        "YELLOW",
    )
    normal_test: Final[ColorFunction] = _ColorFunctions._make_color_function(  # noqa: SLF001
        "RESET",
        is_reset=True,
    )
    if yellow_test("test") != yellow("test"):
        raise AssertionError  # pragma: no coverage
    if normal_test("normal") == yellow("normal"):
        raise AssertionError  # pragma: no coverage


# pylint: disable=import-outside-toplevel
def test_bad_module_attribute() -> None:
    """Test assertion for accessing non-existent module-level attribute."""
    import crayons.crayons as cc  # noqa: PLC0415

    with pytest.raises(
        AttributeError,
        match=(
            r"DISABLE_COLOR is the only module-level attribute set in crayons. "
            "It is exposed for backwards compatibility."
        ),
    ):
        _ = cc.BAD_ATTRIBUTE


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        (
            {97: 98},  # Dictionary mapping 'a' to 'b'
            str.maketrans({97: 98}),
        ),
        (
            {ord("a"): ord("b")},  # More readable version of the same test
            str.maketrans({ord("a"): ord("b")}),
        ),
    ],
)
# pylint: disable=consider-using-assignment-expr
def test_maketrans_dict(
    test_input: dict[int, int] | dict[str, int] | dict[str | int, int],
    expected: dict[int, int],
) -> None:
    """Test the dictionary overload of maketrans."""
    result: Final[dict[int, int] | dict[str, int] | dict[str | int, int]] = (
        ColoredString.maketrans(test_input)
    )
    if result != expected:
        msg: Final[str] = f"maketrans failed for input {test_input}"  # pragma: no cover
        raise AssertionError(msg)  # pragma: no cover


def test_zfill_coverage() -> None:
    """Test zfill with various inputs to ensure full coverage."""
    # Test basic zfill functionality
    colored: Final[ColoredString] = ColoredString("RED", "42")

    # Test with width smaller than string length
    result_one: Final[ColoredString] = colored.zfill(1)
    if str(result_one.s) != "42":
        raise AssertionError  # pragma: no cover

    # Test with width larger than string length
    result_four: Final[ColoredString] = colored.zfill(4)
    if str(result_four.s) != "0042":
        raise AssertionError  # pragma: no cover

    # Test with negative width
    result_nfour: Final[ColoredString] = colored.zfill(-1)
    if str(result_nfour.s) != "42":
        raise AssertionError  # pragma: no cover


@pytest.mark.parametrize(
    ("color", "text", "width", "expected"),
    [
        ("RED", "123", 5, "00123"),
        ("BLUE", "-123", 6, "-00123"),
        ("GREEN", "+123", 6, "+00123"),
        ("YELLOW", "123", 2, "123"),  # Width too small
        ("CYAN", "", 3, "000"),  # Empty string
    ],
)
def test_zfill_comprehensive(
    color: str,
    text: str,
    width: int,
    expected: str,
) -> None:
    """Comprehensive test of zfill functionality."""
    colored: Final[ColoredString] = ColoredString(color, text)
    result: Final[ColoredString] = colored.zfill(width)
    if str(result.s) != expected:
        raise AssertionError  # pragma: no cover
    if result.color != color:  # Ensure color is preserved
        raise AssertionError  # pragma: no cover
    if result.always_color != colored.always_color:  # Ensure always_color is preserved
        raise AssertionError  # pragma: no cover
    if result.bold != colored.bold:  # Ensure bold is preserved
        raise AssertionError  # pragma: no cover


def test_check_color_support_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test color support detection through environment variables."""
    monkeypatch.setenv("TERM", "dumb")
    if _should_default_disable_color() is False:
        raise AssertionError  # pragma: no cover

    monkeypatch.setenv("TERM", "xterm-256color")
    if _should_default_disable_color() is True:
        raise AssertionError  # pragma: no cover

    monkeypatch.delenv("TERM", raising=False)
    if _should_default_disable_color() is True:
        raise AssertionError  # pragma: no cover


@pytest.mark.skipif(
    find_spec("IPython") is None,
    reason="This test requires IPython to run.",
)
def test_check_color_support_ipython() -> None:
    """Test color support detection in IPython."""
    from IPython.terminal.interactiveshell import (  # noqa: PLC0415
        TerminalInteractiveShell,
    )

    if TYPE_CHECKING:
        # pylint: disable=unused-import
        from IPython.core.interactiveshell import (  # noqa: PLC0415
            ExecutionResult,
        )

    # pylint: disable=consider-using-assignment-expr
    shell: Final[TerminalInteractiveShell] = TerminalInteractiveShell.instance()  # type: ignore[misc]
    if shell is not None:
        raw_cell: Final[str] = (
            "from sys import exit as sys_exit\n"
            "from crayons.crayons import _should_default_disable_color\n\n"
            "if _should_default_disable_color() is False:\n"
            "    sys_exit(1)\n"
        )
        ret: Final[ExecutionResult] = shell.run_cell(raw_cell, silent=True)  # type: ignore[no-untyped-call]
        shell.clear_instance()
        if cast("bool", ret.success):
            print("Success")
            return
        raise AssertionError  # pragma: no cover
    raise RuntimeError  # pragma: no cover


if __name__ in {"__main__", "test_with_hypothesis"}:
    raise SystemExit(pytest.main([__file__]))  # pragma: no cover
