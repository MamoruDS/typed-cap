from tests import CFG, cmd, get_profile
from typed_cap import Cap
from typing import Optional


TEST_PROFILE = get_profile(CFG.cur)
B = TEST_PROFILE.based
G = TEST_PROFILE.val_getter


def test_count_A():
    class T(B):
        verbose: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd(""))
    assert res.count("verbose") == 0


def test_count_B():
    class T(B):
        name: str
        verbose: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("--verbose --name foo --verbose"))
    assert res.count("verbose") == 2


def test_count_alias_A():
    class T(B):
        verbose: Optional[bool]

    cap = Cap(T)
    cap.helper({"verbose": {"alias": "v"}})
    res = cap.parse(cmd("-v -v"))
    assert res.count("verbose") == 2


def test_count_alias_B():
    class T(B):
        verbose: Optional[bool]

    cap = Cap(T)
    cap.helper({"verbose": {"alias": "v"}})
    res = cap.parse(cmd("-vvv"))
    assert res.count("verbose") == 3


def test_extends_typeddict():
    class T1(B):
        silent: Optional[bool]

    class T2(T1):
        depth: int

    cap = Cap(T2)
    res = cap.parse(cmd("--depth=-1"))
    assert G(res.val, "silent") == None
    assert G(res.val, "depth") == -1
