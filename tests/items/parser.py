import sys
from enum import Enum, IntEnum
from typing import List, Optional, Tuple, Union

import pytest

from typed_cap import Cap
from typed_cap.types import ArgsParserKeyError

from tests import CFG, cmd, get_profile


TEST_PROFILE = get_profile(CFG.cur)
B = TEST_PROFILE.based
G = TEST_PROFILE.val_getter


def test_flag():
    class T(B):
        silent: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("--silent"))
    assert G(res.args, "silent") == True

    res = cap.parse(cmd(""))
    assert G(res.args, "silent") is None


def test_flag_multi():
    class T(B):
        silent: Optional[bool]
        human_readable: Optional[bool]
        all: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("--silent --all"))
    assert G(res.args, "silent") == True
    assert G(res.args, "human_readable") is None
    assert G(res.args, "all") == True


def test_flag_alias_A():
    class T(B):
        silent: Optional[bool]
        human_readable: Optional[bool]
        all: Optional[bool]

    cap = Cap(T)
    cap.helper(
        {
            "silent": {"alias": "s"},
            "human_readable": {"alias": "h"},
            "all": {"alias": "a"},
        }
    )
    res = cap.parse(cmd("-s -a"))
    assert G(res.args, "silent") == True
    assert G(res.args, "human_readable") is None
    assert G(res.args, "all") == True


def test_flag_alias_B():
    class T(B):
        silent: Optional[bool]
        human_readable: Optional[bool]
        all: Optional[bool]

    cap = Cap(T)
    cap.helper(
        {
            "silent": {"alias": "s"},
            "human_readable": {"alias": "h"},
            "all": {"alias": "a"},
        }
    )
    res = cap.parse(cmd("-ah"))
    assert G(res.args, "silent") is None
    assert G(res.args, "human_readable") == True
    assert G(res.args, "all") == True


def test_option_str_A():
    class T(B):
        name: str

    cap = Cap(T)
    res = cap.parse(cmd("--name foo"))
    assert G(res.args, "name") == "foo"


def test_option_str_B():
    class T(B):
        name: str

    cap = Cap(T)
    res = cap.parse(cmd("--name=bar"))
    assert G(res.args, "name") == "bar"


def test_option_number_A():
    class T(B):
        age: int

    cap = Cap(T)
    res = cap.parse(cmd("--age=10"))
    assert G(res.args, "age") == 10


def test_option_number_B():
    class T(B):
        ratio: float

    cap = Cap(T)
    res = cap.parse(cmd("--ratio 3.14"))
    assert G(res.args, "ratio") == 3.14


def test_option_tuple_A():
    class T(B):
        member: Tuple[str, int]

    cap = Cap(T)
    res = cap.parse(cmd("--member foo,25"))
    assert G(res.args, "member") == ("foo", 25)


def test_option_tuple_B():
    class T(B):
        member: tuple[str, float]

    cap = Cap(T)
    res = cap.parse(cmd("--member bar,25"))
    assert G(res.args, "member") == ("bar", 25.0)


def test_option_list_A():
    class T(B):
        message: List[str]

    cap = Cap(T)
    res = cap.parse(cmd("--message foo,bar"))
    assert G(res.args, "message") == ["foo", "bar"]


def test_option_list_B():
    class T(B):
        message: list[str]

    cap = Cap(T)
    res = cap.parse(cmd("--message foo --message bar"))
    assert G(res.args, "message") == ["foo", "bar"]


# FIXME: global delimiter not working
# TODO: add local delimiter (for every arg)
def test_option_list_delimiter():
    class T(B):
        message: List[str]

    cap = Cap(T)
    cap.set_delimiter("\n")
    res = cap.parse(cmd("--message foo,bar"))
    assert G(res.args, "message") == ["foo,bar"]


# TODO: tuple length determining
def test_option_mix_A():
    class T(B):
        data: Tuple[List[str], float, bool]

    cap = Cap(T)
    res = cap.parse(cmd("--data=a,b,5,false"))
    assert G(res.args, "data") != (["a", "b"], 5.0, False)


# TODO: tuple length determining
def test_option_mix_B():
    class T(B):
        data: Tuple[float, bool, Tuple[str, int]]

    cap = Cap(T)
    res = cap.parse(cmd("--data=5,false,a,5"))
    assert G(res.args, "data") != (5.0, False, ("a", 5))


def test_option_enum_A():
    class CoinFlip(Enum):
        Head = 0
        Tail = 1

    class T(B):
        flip: CoinFlip

    cap = Cap(T)
    res = cap.parse(cmd("--flip head"))
    assert G(res.args, "flip") == CoinFlip.Head


def test_option_enum_B():
    class CoinFlip(IntEnum):
        Head = 0
        Tail = 1

    class T(B):
        flip: CoinFlip

    cap = Cap(T)
    cap._attributes["enum_on_value"] = True
    res = cap.parse(cmd("--flip 0"))
    assert G(res.args, "flip") == CoinFlip.Head


def test_option_enum_C():
    class CoinFlip(Enum):
        Head = "h"
        Tail = "t"

    class T(B):
        flip: CoinFlip

    cap = Cap(T)
    cap._attributes["enum_on_value"] = True
    res = cap.parse(cmd("--flip t"))
    assert G(res.args, "flip") == CoinFlip.Tail


# test for alt bool


def test_arguments_A():
    class T(B):
        all: Optional[bool]
        human_readable: Optional[bool]
        max_depth: Optional[int]

    cap = Cap(T)
    res = cap.parse(cmd("--all --human-readable --max-depth=1 /usr/bin"))
    assert G(res.args, "all") == True
    assert G(res.args, "human_readable") == True
    assert G(res.args, "max_depth") == 1
    assert res.argv == ["/usr/bin"]


# test for parser options


def test_arguments_B():
    class T(B):
        all: Optional[bool]
        human_readable: Optional[bool]
        max_depth: Optional[int]

    cap = Cap(T)
    cap.raw_exception(True)
    try:
        _ = cap.parse(
            cmd("--all --human-readable --max_depth=1 /usr/bin"),
            args_parser_options={
                "disable_hyphen_conversion": True,
            },
        )
    except ArgsParserKeyError as err:
        assert err.key == "human-readable"


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="requires Python 3.10 or higher"
)
def test_uniontypes_queue_list():
    class T(B):
        foo: list[int] | None
        bar: list[int] | None

    cap = Cap(T)
    res = cap.parse(cmd("--foo 5,6,10 --bar 1 --bar 2"))
    assert G(res.args, "foo") == [5, 6, 10]
    assert G(res.args, "bar") == [1, 2]


def test_default_none_union():
    class T(B):
        config: Union[str, None]

    cap = Cap(T)
    res = cap.parse(cmd(""))
    assert G(res.args, "config") == None


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="requires Python 3.10 or higher"
)
def test_default_none_uniontype():
    class T(B):
        config: str | None

    cap = Cap(T)
    res = cap.parse(cmd(""))
    assert G(res.args, "config") == None
