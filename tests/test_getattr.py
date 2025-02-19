"""Test __getattr__ accesses."""

# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ
# mypy: disable-error-code="misc,operator"
# ruff: noqa: DOC501
from __future__ import annotations

from collections import UserString
from typing import TYPE_CHECKING

import crayons
from crayons.crayons import ColoredString

if TYPE_CHECKING:
    from typing import Final


# Attribute lookups for custom types are supported, but, mypy is not
# great with idrntifying them as potential Callables.
# pylint: disable=no-self-use,too-many-branches,too-many-statements
def test_colored_string_collection_returns() -> None:  # noqa: C901,PLR0912,PLR0915
    """Test handling custom methods."""

    class TestString(UserString):
        """Subclsss methods for __getattr__ lookups."""

        def __init__(self, s: str) -> None:
            super().__init__(seq=s)
            self.s = s

        def get_bytes(self) -> bytes:
            """Return bytes to test bytes/bytearray case."""
            return self.s.encode("utf-8")

        def get_bytearray(self) -> bytearray:
            """Return bytearray to test bytes/bytearray case."""
            return bytearray(self.s.encode("utf-8"))

        def get_sequence(self) -> list[str]:
            """Return a custom sequence to test list/Sequence case."""
            return list(self.s)

        def get_frozenset(self) -> frozenset[str]:
            """Return frozenset to test frozenset case."""
            return frozenset(self.s.split())

        def get_set(self) -> set[str]:
            """Return set to test set case."""
            return set(self.s.split())

        def get_tuple(self) -> tuple[str, ...]:
            """Return tuple to test tuple case."""
            return tuple(self.s.split())

        def get_dict(self) -> dict[str, int]:
            """Return dict to test dict/Mapping case."""
            return {c: ord(c) for c in self.data}

        def get_object(self) -> object:  # noqa: PLR6301
            """Return plain object to test default case."""
            return object()

        def returns_none(self) -> None:  # noqa: PLR6301
            """Return None to test ret_none case."""
            return

        def get_userstring(self) -> UserString:
            """Return UserString to test str | UserString case directly."""
            return UserString(self.s.upper())

    test_str = TestString("a b c")
    c = crayons.red(test_str)

    bytes_result = c.get_bytes()
    bytearray_result = c.get_bytearray()
    seq_result = c.get_sequence()
    frozenset_result = c.get_frozenset()
    set_result = c.get_set()
    tuple_result = c.get_tuple()
    dict_result = c.get_dict()
    object_result = c.get_object()
    none_result = c.returns_none()
    nonexistent_result = c.nonexistent_method()
    userstring_result = c.get_userstring()

    if not isinstance(bytes_result, bytes):
        raise TypeError  # pragma: no cover
    if bytes_result != b"a b c":
        raise AssertionError  # pragma: no cover

    if not isinstance(bytearray_result, bytearray):
        raise TypeError  # pragma: no cover
    if bytearray_result != bytearray(b"a b c"):
        raise AssertionError  # pragma: no cover

    if not isinstance(seq_result, list):
        raise TypeError  # pragma: no cover
    if [s.s for s in seq_result] != list("a b c"):
        raise AssertionError  # pragma: no cover

    if not isinstance(frozenset_result, frozenset):
        raise TypeError  # pragma: no cover
    if frozenset({s.s for s in frozenset_result}) != frozenset({"a", "b", "c"}):
        raise AssertionError  # pragma: no cover

    if not isinstance(set_result, set):
        raise TypeError  # pragma: no cover
    if {s.s for s in set_result} != {"a", "b", "c"}:
        raise AssertionError  # pragma: no cover

    if not isinstance(tuple_result, tuple):
        raise TypeError  # pragma: no cover
    if tuple(s.s for s in tuple_result) != ("a", "b", "c"):
        raise AssertionError  # pragma: no cover

    if not isinstance(dict_result, dict):
        raise TypeError  # pragma: no cover
    if {k.s: int(v.s) for k, v in dict_result.items()} != {
        "a": 97,
        "b": 98,
        "c": 99,
        " ": 32,
    }:
        raise AssertionError  # pragma: no cover

    if not isinstance(object_result, object):
        raise TypeError  # pragma: no cover

    if none_result is not None:
        raise AssertionError  # pragma: no cover
    if nonexistent_result is not None:
        raise AssertionError  # pragma: no cover

    if not isinstance(userstring_result, ColoredString):
        raise TypeError  # pragma: no cover
    if str(userstring_result.s) != "A B C":
        raise AssertionError  # pragma: no cover


# pylint: disable=unnecessary-negation
def test_str_interpolable_comparisons() -> None:  # noqa: C901,PLR0912
    """Test the full range of comparison operations with StrInterpolable objects."""

    # pylint: disable=too-few-public-methods
    class CustomInterpolable:
        """Simple StrInterpolable implementation for testing comparisons."""

        def __init__(self, value: str) -> None:
            self.value: Final[str] = value

        def __str__(self) -> str:
            return self.value

    # Create test objects for different comparison scenarios
    cs: Final[ColoredString] = ColoredString("RED", "test")
    custom_equal: Final[CustomInterpolable] = CustomInterpolable("test")
    custom_less: Final[CustomInterpolable] = CustomInterpolable("abc")
    custom_greater: Final[CustomInterpolable] = CustomInterpolable("xyz")

    if cs != custom_equal:
        raise AssertionError  # pragma: no cover
    if cs == CustomInterpolable("different"):
        raise AssertionError  # pragma: no cover

    if not cs < custom_greater:
        raise AssertionError  # pragma: no cover
    if cs < custom_equal:
        raise AssertionError  # pragma: no cover
    if cs < custom_less:
        raise AssertionError  # pragma: no cover

    if not cs > custom_less:
        raise AssertionError  # pragma: no cover
    if cs > custom_equal:
        raise AssertionError  # pragma: no cover
    if cs > custom_greater:
        raise AssertionError  # pragma: no cover

    if not cs <= custom_greater:
        raise AssertionError  # pragma: no cover
    if not cs <= custom_equal:
        raise AssertionError  # pragma: no cover
    if cs <= custom_less:
        raise AssertionError  # pragma: no cover

    if not cs >= custom_less:
        raise AssertionError  # pragma: no cover
    if not cs >= custom_equal:
        raise AssertionError  # pragma: no cover
    if cs >= custom_greater:
        raise AssertionError  # pragma: no cover
