import regex as re
from typing import Dict, List, Union


def argparser(args: List[str]) -> Dict[str, List[str]]:
    args_dict: Dict[str, List[str]] = {"_": []}
    key: str = "_"
    for arg in args:
        reg = re.compile(
            r"^(?P<prefix>[-]{1,2})(?P<key>[^-|=]+)=?(?P<val>[^$]{0,})"
        )
        res = reg.match(arg)
        grp = {}
        if res != None:
            for gi in ["prefix", "key", "val"]:
                grp[str(gi)] = res.group(gi)
        if res != None:
            key = res.group("key") if res.group("key") != None else key
            if args_dict.get(key) == None:
                args_dict[key] = []
            if res.group("val"):
                args_dict[key].append(res.group("val"))
        else:
            args_dict[key].append(arg)
    return args_dict


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
