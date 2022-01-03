import pytest
from . import cmd
from typed_cap import Cap
from typed_cap.types import ArgsParserKeyError
from typing import List, Optional, Tuple, TypedDict


def test_flag():
    class T(TypedDict):
        silent: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("--silent"))
    assert res.val["silent"] == True

    res = cap.parse(cmd(""))
    assert res.val["silent"] == None


def test_flag_multi():
    class T(TypedDict):
        silent: Optional[bool]
        human_readable: Optional[bool]
        all: Optional[bool]

    cap = Cap(T)
    res = cap.parse(cmd("--silent --all"))
    assert res.val["silent"] == True
    assert res.val["human_readable"] == None
    assert res.val["all"] == True


def test_flag_alias_A():
    class T(TypedDict):
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
    assert res.val["silent"] == True
    assert res.val["human_readable"] == None
    assert res.val["all"] == True


def test_flag_alias_B():
    class T(TypedDict):
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
    assert res.val["silent"] == None
    assert res.val["human_readable"] == True
    assert res.val["all"] == True


def test_option_str_A():
    class T(TypedDict):
        name: str

    cap = Cap(T)
    res = cap.parse(cmd("--name foo"))
    assert res.val["name"] == "foo"


def test_option_str_B():
    class T(TypedDict):
        name: str

    cap = Cap(T)
    res = cap.parse(cmd("--name=bar"))
    assert res.val["name"] == "bar"


def test_option_number_A():
    class T(TypedDict):
        age: int

    cap = Cap(T)
    res = cap.parse(cmd("--age=10"))
    assert res.val["age"] == 10


def test_option_number_B():
    class T(TypedDict):
        ratio: float

    cap = Cap(T)
    res = cap.parse(cmd("--ratio 3.14"))
    assert res.val["ratio"] == 3.14


def test_option_tuple_A():
    class T(TypedDict):
        member: Tuple[str, int]

    cap = Cap(T)
    res = cap.parse(cmd("--member foo,25"))
    assert res.val["member"] == ("foo", 25)


def test_option_tuple_B():
    class T(TypedDict):
        member: tuple[str, float]

    cap = Cap(T)
    res = cap.parse(cmd("--member bar,25"))
    assert res.val["member"] == ("bar", 25.0)


def test_option_list_A():
    class T(TypedDict):
        message: List[str]

    cap = Cap(T)
    res = cap.parse(cmd("--message foo,bar"))
    assert res.val["message"] == ["foo", "bar"]


def test_option_list_B():
    class T(TypedDict):
        message: list[str]

    cap = Cap(T)
    res = cap.parse(cmd("--message foo --message bar"))
    assert res.val["message"] == ["foo", "bar"]


# FIXME: global delimiter not working
# TODO: add local delimiter (for every arg)
def test_option_list_delimiter():
    class T(TypedDict):
        message: List[str]

    cap = Cap(T)
    cap.set_delimiter("")
    res = cap.parse(cmd("--message foo,bar"))
    assert res.val["message"] == ["foo,bar"]


# TODO: tuple length determining
def test_option_mix_A():
    class T(TypedDict):
        data: Tuple[List[str], float, bool]

    cap = Cap(T)
    res = cap.parse(cmd("--data=a,b,5,false"))
    # FIXME:
    assert res.val["data"] != (["a", "b"], 5.0, False)


# TODO: tuple length determining
def test_option_mix_B():
    class T(TypedDict):
        data: Tuple[float, bool, Tuple[str, int]]

    cap = Cap(T)
    res = cap.parse(cmd("--data=5,false,a,5"))
    # FIXME:
    assert res.val["data"] != (5.0, False, ("a", 5))


# test for alt bool


def test_arguments_A():
    class T(TypedDict):
        all: Optional[bool]
        human_readable: Optional[bool]
        max_depth: Optional[int]

    cap = Cap(T)
    res = cap.parse(cmd("--all --human-readable --max-depth=1 /usr/bin"))
    assert res.val["all"] == True
    assert res.val["human_readable"] == True
    assert res.val["max_depth"] == 1
    assert res.args == ["/usr/bin"]


# test for parser options


def test_arguments_B():
    class T(TypedDict):
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
