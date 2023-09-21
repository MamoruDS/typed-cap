from typing import Optional

from typed_cap import Cap

from tests import CFG, cmd, get_profile


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


def test_extends():
    class T1(B):
        silent: Optional[bool]

    class T2(T1):
        depth: int

    cap = Cap(T2)
    res = cap.parse(cmd("--depth=-1"))
    assert G(res.args, "silent") == None
    assert G(res.args, "depth") == -1


def test_cls_doc_as_about():
    class T(B):
        """
        some description
        """

        verbose: Optional[bool]

    cap = Cap(T)
    assert cap._about == "some description"


def test_anno_doc_as_about():
    class T(B):
        anno: Optional[bool]
        """
        anno doc for testing
        """

    cap = Cap(T)
    assert cap._args["anno"].about == "anno doc for testing"
