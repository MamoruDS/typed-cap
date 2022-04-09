from . import cmd, CFG
from typed_cap import Cap
from typing import TypedDict

CFG.cur = "dict-based"


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
