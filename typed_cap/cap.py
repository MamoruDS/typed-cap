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

    def parse(self, args: List[str] = sys.argv[1:]) -> T:  # type: ignore
        out = utils.args_parser(args, [])
        for k, v in out.items():
            # TODO:
            pass
