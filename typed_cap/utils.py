import regex as re
from sys import stderr
from typed_cap.types import (
    ArgsParserKeyError,
    ArgsParserMissingValue,
    ArgsParserUnexpectedValue,
)
from typing import Any, Dict, List, NoReturn, Optional, TypedDict, Union


class ParsedArgs(TypedDict):
    args: List[str]
    options: Dict[str, List[Union[str, bool]]]


def args_parser(
    argv: List[str],
    flags: List[str],
    options: List[str],
    ignore_unknown: bool = False,
    ignore_unknown_flags: bool = False,
    ignore_unknown_options: bool = False,
) -> ParsedArgs:
    argv = [a for a in argv]
    parsed: Dict = {"_": []}
    key: str
    reg = re.compile(
        r"((-(?P<flags>[\w]{2,}))|(-(?P<alias>[\w]{1}))|(-{1,2}(?P<option>[a-zA-Z|-|_]+)))(=(?P<val>[^$|^\n]+))?"
    )

    def raise_unknown_flag(key: str) -> Union[NoReturn, None]:
        if not ignore_unknown and not ignore_unknown_flags:
            raise ArgsParserKeyError(key, "flag")

    def raise_unknown_option(key: str) -> Union[NoReturn, None]:
        if not ignore_unknown and not ignore_unknown_options:
            raise ArgsParserKeyError(key, "option")

    def is_next_a_value() -> bool:
        if len(argv) == 0:
            return False
        else:
            return reg.match(argv[0]) == None

    def safe_append(k: str, t: Union[str, bool]):
        if parsed.get(k) == None:
            parsed[k] = []
        parsed[k].append(t)

    while len(argv):
        arg = argv.pop(0)
        m = reg.match(arg)
        if m != None:
            opt: Optional[str]
            opt = m.group("flags")
            if opt != None:
                for f in opt:
                    if f not in flags:
                        raise_unknown_flag(f)
                    else:
                        safe_append(f, True)
                continue
            opt = m.group("alias")
            key = "_"  # checking potential unbound
            if opt != None:
                key = opt
            opt = m.group("option")
            if opt != None:
                key = opt
            val = m.group("val")
            if key == "_":
                raise Exception('unknown unbound issue for "key"')
            if val != None:
                """
                matched option with val (`-o=sth` or `--opt==sth`)
                """
                if key in flags:
                    raise ArgsParserUnexpectedValue(key, val)
                elif key not in options:
                    raise_unknown_option(key)
                else:
                    safe_append(key, val)
            else:
                """
                matched option or flag depends on whether the next argument is a "val"
                """
                if is_next_a_value():
                    if key in options:
                        safe_append(key, argv.pop(0))
                    else:
                        raise_unknown_option(key)
                else:
                    val = True
                    if key[:5] == "--no-":  # TODO:
                        val = False
                        key = key[5:]
                    if key in options:
                        raise ArgsParserMissingValue(key)
                    elif key in flags:
                        safe_append(key, val)
                    else:
                        raise_unknown_flag(key)
        else:
            safe_append("_", arg)

    def _extract(k: str, v: List[Union[str, bool]]) -> List[Union[str, bool]]:
        if not isinstance(v, list):
            raise Exception(f"val of {k} is not a list")
        return v

    parsed_args: ParsedArgs = {
        "args": parsed.pop("_"),
        "options": dict(
            map(lambda it: (it[0], _extract(it[0], it[1])), parsed.items())
        ),
    }
    return parsed_args


def flatten(a: List[List[Any]]) -> List[Any]:
    f = []
    for c in a:
        f = [*f, *c]
    return f


def panic(msg: str, exit_code: int = 1) -> NoReturn:
    stderr.write(msg + "\n")
    exit(exit_code)


def remove_comments(code: Union[str, List[str]]) -> List[str]:
    if isinstance(code, list):
        code = "\n".join(code)
    code = re.sub(r"#[^$|^\n]+", "", code, flags=re.MULTILINE)
    code = re.sub(r"\"\"\"[^(\"\"\")]+\"\"\"", "", code, flags=re.MULTILINE)
    if isinstance(code, str):
        lines = code.split("\n")
    else:
        lines = code
    res = []
    for l in lines:
        if l.lstrip() == "":
            continue
        res.append(l)
    return res
