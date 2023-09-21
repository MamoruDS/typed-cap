from enum import Enum
from typing import List, Optional

from typed_cap import Cap

from tests import CFG, cmd, get_profile


TEST_PROFILE = get_profile(CFG.cur)
B = TEST_PROFILE.based
G = TEST_PROFILE.val_getter


def test_cmt_param_alias():
    class T(B):
        # @alias=v
        verbose: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("-v"))
    assert res.count("verbose") == 1


# def test_cmt_param_show_default():
#     ...


def test_cmt_param_hide_default():
    class T(B):
        # @alias=d @hide_default
        max_depth: int

    cap = Cap(T)
    assert cap._args["max_depth"].show_default == False


def test_cmt_param_delimiter():
    class T(B):
        # @delimiter=|
        videos: List[str]

    cap = Cap(T)
    res = cap.parse(cmd("--videos agility1|ant3"))
    assert G(res.args, "videos") == ["agility1", "ant3"]


def test_cmt_param_none_delimiter():
    class T(B):
        # @none_delimiter
        message: List[str]

    cap = Cap(T)
    res = cap.parse(cmd("--message foo,bar"))
    assert G(res.args, "message") == ["foo,bar"]


def test_cmt_param_enum_on_val():
    class CoinFlip(Enum):
        head = 0
        tail = 1

    class T(B):
        # @enum_on_value
        flip: CoinFlip

    cap = Cap(T)
    res = cap.parse(cmd("--flip 1"))
    assert G(res.args, "flip") == CoinFlip.tail
