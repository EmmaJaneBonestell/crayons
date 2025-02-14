#!/bin/python
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ
"""Simple test of just running the README example. Better tests to come."""
# ruff: noqa: T201,T203

from __future__ import annotations

import crayons


def test_basic_functionality() -> None:
    """Basic functionality tests."""
    print(crayons.red("red string"))
    print(f"{crayons.red('red')} white {crayons.blue('blue')}")
    crayons.disable()
    print(f"{crayons.red('red')} white {crayons.blue('blue')}")
    print(f"non-string value {crayons.red(1234)!s}")
    crayons.enable()
    print(f"{crayons.red('red')} white {crayons.blue('blue')}")
    print(f"non-string value {crayons.red(1234)!s}")
    print(crayons.red("red string", bold=True))
    print(crayons.yellow("yellow string", bold=True))
    print(crayons.magenta("magenta string", bold=True))
    print(crayons.white("white string", bold=True))
    print(crayons.random("random color"))
    print(crayons.random("random and bold", bold=True))
    print(crayons.red("red"))
    print(crayons.green("green"))
    print(crayons.yellow("yellow"))
    print(crayons.blue("blue"))
    print(crayons.black("black", bold=True))

    print(crayons.magenta("magenta"))
    print(crayons.cyan("cyan"))
    print(crayons.white("white"))
    print(crayons.normal("normal"))
    print(crayons.clean(f"{crayons.red('red')} clean {crayons.blue('blue')}"))

    crayons.replace_colors({"magenta": "blue"})
    print(crayons.magenta("this is blue!"))
    crayons.reset_replace_colors()
    print(crayons.magenta("this is magenta again!"))

    print(crayons.lightblack_ex("Extension Code: light black"))
    print(crayons.lightblue_ex("Extension Code: light blue"))
    print(crayons.lightcyan_ex("Extension Code: light cyan"))
    print(crayons.lightgreen_ex("Extension Code: light green"))
    print(crayons.lightmagenta_ex("Extension Code: light magenta"))
    print(crayons.lightred_ex("Extension Code: light red"))
    print(crayons.lightwhite_ex("Extension Code: light white"))
    print(crayons.lightyellow_ex("Extension Code: light yellow"))


if __name__ in {"__main__", "test_crayons"}:
    test_basic_functionality()
