import regex as re
from typing import Dict, List, Optional, TypedDict, Union


class ParsedArgs(TypedDict):
    args: List[str]
    options: Dict[str, List[Union[str, bool]]]


def args_parser(argv: List[str], flags: List[str]) -> ParsedArgs:
    parsed: Dict = {"_": []}
    key: str = "_"
    reg = re.compile(
        r"((-(?P<flags>[\w]{2,}))|(-(?P<alias>[\w]{1}))|(-{1,2}(?P<option>[a-zA-Z|-|_]+)))(=(?P<val>[^$|^\n]+))?"
    )

    def safe_append(key: str, t: Union[str, bool]):
        if parsed.get(key) == None:
            parsed[key] = []
        parsed[key].append(t)

    for arg in argv:
        m = reg.match(arg)
        if m == None:
            safe_append(key, arg)
            key = "_"  # reset key to "_"
        else:
            opts: Optional[str]
            opts = m.group("flags")
            if opts != None:
                for f in opts:
                    if f not in flags:
                        raise Exception(f"{f} is NOT FLAG!")
                    safe_append(f, True)
                    continue
            opts = m.group("alias")
            if opts != None:
                key = opts
            opts = m.group("option")
            if opts != None:
                key = opts
            val = m.group("val")
            if key not in flags:
                if val != None:
                    safe_append(key, val)
                    key = "_"
            else:
                if val != None:
                    raise Exception(f"flag {f} should not catch values")
                if key[:5] == "--no-":  # default enabled?
                    safe_append(key, False)
                else:
                    safe_append(key, True)
                key = "_"

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
