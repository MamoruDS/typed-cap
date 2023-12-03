from . import cmd, CFG
from typed_cap import Cap
from typing import TypedDict

CFG.cur = "dict-based"


def test_unpack():
    class T(TypedDict):
        verbose: bool

    cap = Cap(T)
    parsed = cap.parse(cmd("--verbose foo"))
    argv, args = parsed.unpack()
    assert isinstance(argv, list)
    assert isinstance(args, dict)


def test_default_dict_based():
    class T(TypedDict):
        silent: bool
        depth: int

    cap = Cap(T)
    cap.default_strict({"silent": False, "depth": -1})
    res = cap.parse(cmd(""))
    assert res.val["silent"] == False
    assert res.val["depth"] == -1


from .items.cap import *
