import regex as re
from sys import stderr
from typed_cap.types import (
    ArgsParserKeyError,
    ArgsParserMissingValue,
    ArgsParserUnexpectedValue,
)
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NoReturn,
    Optional,
    Tuple,
    TypeVar,
    TypedDict,
    Union,
)


class ParsedArgs(TypedDict):
    args: List[str]
    options: Dict[str, List[Union[str, bool]]]


def args_parser(
    argv: List[str],
    flags: List[Tuple[str, Optional[str]]],
    options: List[Tuple[str, Optional[str]]],
    ignore_unknown: bool = False,
    ignore_unknown_flags: bool = False,
    ignore_unknown_options: bool = False,
) -> ParsedArgs:
    argv = [a for a in argv]
    parsed: Dict = {"_": []}
    key: str
    reg = re.compile(
        r"^((-(?P<flags>[a-zA-Z0-9]{2,}))|(-(?P<alias>[a-zA-Z0-9]{1}))|(-{1,2}(?P<option>[a-zA-Z0-9|\-|_]+)))(=(?P<val>[^$|^\n]+))?"
    )

    def is_valid_key(k: str, flg: bool = False, opt: bool = False) -> bool:
        _flags = flags if flg else []
        _options = options if opt else []
        return k in flatten([*_flags, *_options])  # type: ignore

    def get_flag_key(k: str) -> Optional[str]:
        for n, a in flags:
            if n == k or a == k:
                return n
        return None

    def get_option_key(k: str) -> Optional[str]:
        for n, a in options:
            if n == k or a == k:
                return n
        return None

    def raise_unknown_flag(key: str) -> Union[NoReturn, None]:
        if not (ignore_unknown or ignore_unknown_flags):
            raise ArgsParserKeyError(key, "flag")

    def raise_unknown_option(key: str) -> Union[NoReturn, None]:
        if not (ignore_unknown or ignore_unknown_options):
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
                    f_k = get_flag_key(f)
                    if f_k == None:
                        raise_unknown_flag(f)
                    else:
                        safe_append(f_k, True)
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
            if not is_valid_key(key, flg=True, opt=True):
                _key = re.sub(r"\-", "_", key)
                if is_valid_key(key, flg=True, opt=True):
                    key = _key
            if val != None:
                """
                matched option with val (`-o=sth` or `--opt==sth`)
                """
                if is_valid_key(key, flg=True):
                    raise ArgsParserUnexpectedValue(key, val)
                else:
                    opt = get_option_key(key)
                    if opt == None:
                        raise_unknown_option(key)
                    else:
                        safe_append(opt, val)
            else:
                """
                matched option or flag depends on whether the next argument is a "val"
                """
                if is_next_a_value():
                    flg = get_flag_key(key)
                    if flg != None:
                        safe_append(flg, True)
                    else:
                        opt = get_option_key(key)
                        if opt != None:
                            safe_append(opt, argv.pop(0))
                        else:
                            raise_unknown_option(key)
                else:
                    val = True
                    # TODO: add an option to enable this
                    # if key[:5] == "--no-":
                    #     val = False
                    #     key = key[5:]
                    if is_valid_key(key, opt=True):
                        raise ArgsParserMissingValue(key)
                    else:
                        flg = get_flag_key(key)
                        if flg != None:
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


def _to_color(text, code: str) -> str:
    return f"{code}{text}\x1b[0m"


def to_red(text) -> str:
    return _to_color(text, "\x1b[31m")


def to_green(text) -> str:
    return _to_color(text, "\x1b[32m")


def to_yellow(text) -> str:
    return _to_color(text, "\x1b[33m")


def to_blue(text) -> str:
    return _to_color(text, "\x1b[34m")


def flatten(a: List[List]) -> List:
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


D = TypeVar("D")


def unwrap_or(d: Optional[D], alt: D) -> D:
    if d == None:
        return alt
    else:
        return d
