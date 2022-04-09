from . import cmd, CFG
from typed_cap import Cap

CFG.cur = "object-based"


def test_default_obj_based():
    class T:
        silent: bool = False
        depth: int = -1

    cap = Cap(T)
    res = cap.parse(cmd(""))
    assert res.val.silent == False
    assert res.val.depth == -1


from .items.cap import *
