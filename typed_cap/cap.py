import re
import sys
from inspect import getsource
from typed_cap import utils
from typed_cap.constants import SUPPORT_TYPES, ValidChar
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    get_args,
)

T = TypeVar("T", bound=TypedDict)
U = TypeVar("U", bound=Union[TypedDict, Dict[str, Any]])
K = TypeVar("K", bound=str)


class ArgOpt(TypedDict, total=False):
    about: str
    alias: ValidChar
    # optional: bool


class _ArgOpt(TypedDict):
    val: Optional[Any]
    type: str
    about: Optional[str]
    alias: Optional[ValidChar]
    optional: bool


class Cap(Generic[K, T, U]):
    _argstype: Type[T]
    _args: Dict[str, _ArgOpt]

    def __init__(
        self,
        argstype: Type[T],
    ) -> None:
        self._argstype = argstype
        self._parse_argstype()

    def _parse_argstype(self):
        types = utils.remove_comments(getsource(self._argstype))[1:]
        self._args = {}
        reg = re.compile(r"^(optional)\[(?P<type>.+)\]$")
        for t in types:
            t = t.split(":")
            if len(t) != 2:
                if len(t) == 1:
                    if t[0].lstrip() == "":
                        continue
                    if t[0].lstrip()[:4] == "pass":
                        continue
                raise Exception  # TODO:
            t = [x.lstrip() for x in t]
            t = [x.rstrip() for x in t]
            key, t = t
            opt: bool = False
            t = t.lower()
            m = reg.match(t)
            if m != None:
                opt = True
                t = m.group("type")
            if t not in get_args(SUPPORT_TYPES):
                raise Exception(f'"{t}" is not supported')  # TODO:
            self._args[key] = {
                "val": None,
                "type": t,
                "about": None,
                "alias": None,
                "optional": opt,
            }

    def default(self, value: U):
        return self.default_strict(value)  # type: ignore[arg-type]

    def default_strict(self, value: T):
        for arg, val in value.items():
            self._args[arg]["val"] = val

    def helper(self, helpers: Dict[K, ArgOpt]):
        for arg, opt in helpers.items():
            self._args[arg] = {**self._args[arg], **opt}  # type: ignore[misc]

    def parse(self, args: List[str] = sys.argv[1:]) -> T:
        def find_key(name: str) -> str:
            for key, opt in self._args.items():
                if key == name:
                    return key
                if opt["alias"] == name:
                    return key
            raise Exception  # TODO:

        def extract_list_type(t: str) -> Tuple[bool, str]:
            if t == "list":
                return True, "str"
            reg = re.compile(r"^(list\[(?P<type>\w+)\])$")
            m = reg.match(t)
            if m != None:
                return True, m.group("type")
            else:
                return False, t

        flags = []
        for key, opt in self._args.items():
            if opt["type"] == "bool":
                flags.append(key)
                if opt["alias"] != None:
                    flags.append(opt["alias"])

        out = utils.args_parser(args, flags)

        for key, val in out["options"].items():
            opt = self._args[find_key(key)]
            is_list, t = extract_list_type(opt["type"])
            _val: List[Any]
            if is_list:
                _val = val
            else:
                _val = val[:1]
            for i, v in enumerate(val):
                if t == "str":
                    _val[i] = v
                if t == "int":
                    _val[i] = int(v)
                if t == "float":
                    _val[i] = float(v)
                if t == "bool":
                    _val[i] = bool(v)
            if is_list:
                self._args[find_key(key)]["val"] = val
            else:
                self._args[find_key(key)]["val"] = val[0]

        res: Dict[str, Any] = {"_": out["args"]}
        for key, opt in self._args.items():
            if key == "_":
                continue
            res[key] = opt["val"]
            if res[key] == None and not opt["optional"]:
                # TODO:
                raise Exception(f"missing option: {key}")
        return res  # type: ignore
