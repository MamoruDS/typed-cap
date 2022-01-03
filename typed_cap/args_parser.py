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
from typed_cap.utils import unwrap_or
from typing import (
    Dict,
    List,
    NoReturn,
    Optional,
    Tuple,
    Union,
)


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

    def get_valid_key(k: str) -> Tuple[str, bool, bool]:
        key = k
        is_flag = False
        is_option = False
        #
        _key = get_flag_key(k)
        if _key != None:
            key = _key
            is_flag = True
        #
        _key = get_option_key(k)
        if _key != None:
            key = _key
            is_option = True
        return key, is_flag, is_option

    def _get_generic_key(k: str, valids: List[ArgNamed]) -> Optional[str]:
        if not options.get("disable_hyphen_conversion", False):
            # FIXME: checking potential repeated option names
            k = k.replace("-", "_")
        for n, a in valids:
            if n == k or a == k:
                return n
        return None

    def get_flag_key(k: str) -> Optional[str]:
        return _get_generic_key(k, named_flags)

    def get_option_key(k: str) -> Optional[str]:
        return _get_generic_key(k, named_options)

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
                raise Exception(f"unknown unbound issue for '{key}'")
            if val != None:
                """
                matched option with val (`-o=sth` or `--opt==sth`)
                """
                v_key, is_flg, is_opt = get_valid_key(key)
                if not (is_flg or is_opt):
                    raise_unknown_option(key)
                if is_flg:
                    raise ArgsParserUnexpectedValue(v_key, val)
                if is_opt:
                    safe_append(v_key, val)
            else:
                """
                matched option or flag depends on whether the next argument is a "val"
                """
                v_key, is_flg, is_opt = get_valid_key(key)
                if not (is_flg or is_opt):
                    raise_unknown_option(key)
                if is_next_a_value():
                    if is_flg:
                        # TODO: more description here: why assign `True`
                        safe_append(v_key, True)
                    if is_opt:
                        safe_append(v_key, argv.pop(0))
                else:
                    if is_flg:
                        # TODO: add an option to enable this
                        # if key[:5] == "--no-":
                        #     val = False
                        #     key = key[5:]
                        safe_append(v_key, True)
                    if is_opt:
                        raise ArgsParserMissingValue(v_key)
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
