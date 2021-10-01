import regex as re
from typing import Dict, List, Optional, TypedDict, Union


class ParsedArgs(TypedDict):
    args: List[str]
    options: Dict[str, Union[str, bool]]


def args_parser(argv: List[str], flags: List[str]) -> ParsedArgs:
    parsed: Dict = {"_": []}
    key: str = "_"
    reg = re.compile(
        r"((-(?P<flags>[\w]{2,}))|(-(?P<alias>[\w]{1}))|(-{1,2}(?P<option>[a-zA-Z|-|_]+)))(=(?P<val>[^$|^\n]+))?"
    )
    for arg in argv:
        m = reg.match(arg)
        if m == None:
            parsed[key].append(arg)
            key = "_"  # reset key to "_"
        else:
            opts: Optional[str]
            # flags
            opts = m.group("flags")
            if opts != None:
                for f in opts:
                    if f not in flags:
                        raise Exception(f"{f} is NOT FLAG!")
                    parsed[f] = [True]
                    continue
            # options (and alias
            opts = m.group("alias")
            if opts != None:
                key = opts
            opts = m.group("option")
            if opts != None:
                key = opts
            val = m.group("val")
            if key not in flags:
                if val != None:
                    parsed[key] = [val]
                    key = "_"
                else:
                    parsed[key] = []
            else:
                if val != None:
                    raise Exception(f"flag {f} should not catch values")
                if key[:5] == "--no-":
                    parsed[key] = [False]
                else:
                    parsed[key] = [True]

    def _extract(k: str, v: List[Union[str, bool]]) -> Union[str, bool]:
        if not isinstance(v, list):
            raise Exception(f"val of {k} is not a list")
        if len(v) != 1:
            raise Exception(f"internal issue: unexpected length of {k}")
        return v[0]

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
