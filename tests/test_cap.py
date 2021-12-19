import pytest
from . import cmd
from typed_cap import Cap
from typing import List, Optional, Tuple, TypedDict


def test_default():
    class T(TypedDict):
        silent: bool
        depth: int

    cap = Cap(T)
    cap.default_strict({"silent": False, "depth": -1})
    res = cap.parse(cmd(""))
    assert res.val["silent"] == False
    assert res.val["depth"] == -1


def test_count_A():
    class T(TypedDict):
        verbose: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd(""))
    assert res.count("verbose") == 0


def test_count_B():
    class T(TypedDict):
        name: str
        verbose: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("--verbose --name foo --verbose"))
    assert res.count("verbose") == 2


def test_count_alias_A():
    class T(TypedDict):
        verbose: Optional[bool]

    cap = Cap(T)
    cap.helper({"verbose": {"alias": "v"}})
    res = cap.parse(cmd("-v -v"))
    assert res.count("verbose") == 2


def test_count_alias_B():
    class T(TypedDict):
        verbose: Optional[bool]

    cap = Cap(T)
    cap.helper({"verbose": {"alias": "v"}})
    res = cap.parse(cmd("-vvv"))
    assert res.count("verbose") == 3
