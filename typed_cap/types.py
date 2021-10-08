from typing import Literal, Optional, TypedDict


VALID_ALIAS_CANDIDATES = Literal[
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
]


class ArgOpt(TypedDict, total=False):
    about: str
    alias: VALID_ALIAS_CANDIDATES


class ArgsParserKeyError(Exception):
    key: str
    key_type: str

    def __init__(
        self,
        key: str,
        key_type: Literal["option", "flag"],
        *args: object,
    ) -> None:
        self.key = key
        self.key_type = key_type
        super().__init__(f"unknown {self.key_type} '{self.key}'", *args)


class ArgsParserMissingArgument(Exception):
    key: str
    type_name: str

    def __init__(self, key: str, type_name: str, *args: object) -> None:
        self.key = key
        self.type_name = type_name
        super().__init__(*args)


class ArgsParserMissingValue(Exception):
    key: str

    def __init__(self, key: str, *args: object) -> None:
        self.key = key
        super().__init__(*args)


class ArgsParserUndefinedParser(Exception):
    type_name: str

    def __init__(self, type_name: str, *args: object) -> None:
        self.type_name = type_name
        super().__init__(*args)


class ArgsParserUnexpectedValue(Exception):
    key: str
    value: str

    def __init__(self, key: str, value: str, *args: object) -> None:
        self.key = key
        self.value = value
        super().__init__(*args)


class Unhandled(Exception):
    msg: str
    desc: Optional[str]
    loc: Optional[str]

    def __init__(
        self, desc: Optional[str] = None, loc: Optional[str] = None
    ) -> None:
        self.desc = desc
        self.loc = loc
        if loc == None:
            loc = ""
        else:
            loc = f" in `{loc}`"
        if desc == None:
            desc = ""
        else:
            desc = "\n\t" + desc
        self.msg = "Cap: unhandled error" + loc + desc
        super().__init__(self.msg)
