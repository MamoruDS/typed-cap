import regex as re
from typing import Dict, List, Optional


def argparser(argv: List[str]) -> Dict[str, List[str]]:
    args: Dict[str, List[str]] = {"?": []}
    key: str = "?"
    for arg in argv:
        reg = re.compile(
            r"^(?P<prefix>[-]{1,2})(?P<key>[^-|=]+)=?(?P<val>[^$]{0,})"
        )
        res = reg.match(arg)
        grp = {}
        if res != None:
            for gi in ["prefix", "key", "val"]:
                grp[str(gi)] = res.group(gi)
        if res != None:
            key = (
                res.group("key")
                if res.group("key") != None
                else key
            )
            if args.get(key) == None:
                args[key] = []
            if res.group("val"):
                args[key].append(res.group("val"))
        else:
            args[key].append(arg)
    return args
