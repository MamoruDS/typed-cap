import re
from typed_cap.types import (
    ArgNamed,
    ArgTypes,
    ArgsParserKeyError,
    ArgsParserMissingValue,
    ArgsParserOptions,
    ArgsParserUnexpectedValue,
    ArgsParserResults,
)
from typed_cap.utils import flatten, unwrap_or
from typing import Dict, List, NoReturn, Optional, Tuple, Union


def args_parser(
    argv: List[str],
    named_args: List[Tuple[ArgTypes, ArgNamed]],
    parse_options: Optional[ArgsParserOptions] = None,
) -> ArgsParserResults:
    argv = [a for a in argv]
    parsed: Dict = {"_": []}
    key: str
    reg = re.compile(
        r"^((-(?P<flags>[a-zA-Z0-9]{2,}))|(-(?P<alias>[a-zA-Z0-9]{1}))|(-{1,2}(?P<option>[a-zA-Z0-9|\-|_]+)))(=(?P<val>[^$|^\n]+))?"
    )

    _default_options: ArgsParserOptions = {}
    options: ArgsParserOptions = unwrap_or(parse_options, _default_options)
    named_flags: List[ArgNamed] = []
    named_options: List[ArgNamed] = []
    for at, an in named_args:
        if at == "flag":
            named_flags.append(an)
        elif at == "option":
            named_options.append(an)
        else:
            pass

    def is_valid_key(k: str, flg: bool = False, opt: bool = False) -> bool:
        _named_flags = named_flags if flg else []
        _named_options = named_options if opt else []
        return k in flatten([*_named_flags, *_named_options])  # type: ignore

    def get_flag_key(k: str) -> Optional[str]:
        for n, a in named_flags:
            if n == k or a == k:
                return n
        return None

    def get_option_key(k: str) -> Optional[str]:
        for n, a in named_options:
            print(f"n->{n}\na->{a}")
            if n == k or a == k:
                return n
        return None

    def raise_unknown_flag(key: str) -> Union[NoReturn, None]:
        if not (
            options.get("ignore_unknown", False)
            or options.get("ignore_unknown_flags", False)
        ):
            raise ArgsParserKeyError(key, "flag")

    def raise_unknown_option(key: str) -> Union[NoReturn, None]:
        if not (
            options.get("ignore_unknown", False)
            or options.get("ignore_unknown_options", False)
        ):
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

    parsed_args: ArgsParserResults = {
        "args": parsed.pop("_"),
        "options": dict(
            map(lambda it: (it[0], _extract(it[0], it[1])), parsed.items())
        ),
    }
    return parsed_args