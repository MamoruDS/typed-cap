import json
import re
import sys
from inspect import getsource
from typed_cap import utils
from typed_cap.constants import SUPPORT_TYPES, ValidChar
from typed_cap.parser import Parser, ParserRegister, PRESET as PRESET_PARSERS
from typed_cap.types import ArgsParserKeyError
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


class _ParsedVal(TypedDict):
    val: List[Any]
    default_val: Optional[Any]
    is_list: bool


class Parsed(Generic[T]):
    _args: List[str]
    _parsed_map: Dict[str, _ParsedVal]

    def __init__(
        self, args: List[str], parsed_map: Dict[str, _ParsedVal]
    ) -> None:
        self._args = args
        self._parsed_map = parsed_map

    @property
    def arguments(self) -> List[str]:
        return self._args

    @property
    def args(self) -> List[str]:
        return self.arguments

    @property
    def value(self) -> T:
        val = {}
        for key, parsed in self._parsed_map.items():
            pv = parsed["val"]
            pv = utils.flatten(pv)
            if len(pv) == 0:
                val[key] = parsed["default_val"]
            else:
                val[key] = pv if parsed["is_list"] else pv[0]
        return val  # type: ignore

    @property
    def val(self) -> T:
        return self.value

    def count(self, name: str) -> int:
        parsed = self._parsed_map.get(name)
        if parsed != None:
            return len(parsed["val"])
        else:
            utils.panic(f'Parsed.count: cannot find option with name "{name}"')

    def __json__(self, indent: Optional[int]) -> str:
        j = {}
        j["arguments"] = self.arguments
        j["value"] = self.value
        return json.dumps(j, indent=indent)

    def toJSON(self, indent: Optional[int] = None) -> str:
        return self.__json__(indent=indent)


class Cap(Generic[K, T, U]):
    _argstype: Type[T]
    _args: Dict[str, _ArgOpt]
    _delimiter: str = ","
    _parser_register: ParserRegister

    def __init__(
        self,
        argstype: Type[T],
    ) -> None:
        self._argstype = argstype
        self._parser_register = PRESET_PARSERS
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
            # TODO: SUPPORT_TYPES should be removed
            if t not in get_args(SUPPORT_TYPES):
                raise Exception(f'"{t}" is not supported')  # TODO:
            self._args[key] = {
                "val": None,
                "type": t,
                "about": None,
                "alias": None,
                "optional": opt,
            }

    def set_delimiter(self, delimiter: str):
        self._delimiter = delimiter

    def set_parser(self, type_name: str, parser: Parser, allow_list: bool):
        self._parser_register.__setitem__(
            type_name, {"parser": parser, "allow_list": allow_list}
        )

    def default(self, value: U):
        return self.default_strict(value)  # type: ignore[arg-type]

    def default_strict(self, value: T):
        for arg, val in value.items():
            self._args[arg]["val"] = val

    def helper(self, helpers: Dict[K, ArgOpt]):
        for arg, opt in helpers.items():
            self._args[arg] = {**self._args[arg], **opt}  # type: ignore[misc]

    def parse(
        self,
        args: List[str] = sys.argv[1:],
        ignore_unknown: bool = False,
    ) -> Parsed[T]:
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
        options = []
        for key, opt in self._args.items():
            if opt["type"] == "bool":
                flags.append(key)
                if opt["alias"] != None:
                    flags.append(opt["alias"])
            else:
                options.append(key)
                if opt["alias"] != None:
                    options.append(opt["alias"])

        try:
            out = utils.args_parser(args, flags, options)
        except ArgsParserKeyError as key_error:
            utils.panic("Cap.parse: " + f"unknown option '{key_error.key}'")

        parsed_map: Dict[str, _ParsedVal] = {}
        for key, val in out["options"].items():
            opt = self._args[find_key(key)]
            is_list, t = extract_list_type(opt["type"])
            _val: List[List[Any]] = []
            for v in val:
                if isinstance(v, bool):
                    _val.append([v])
                    continue
                parser_inf = self._parser_register.get(t)
                if parser_inf == None:
                    utils.panic(
                        "Cap.parse: "
                        + f"cannot handle type {t} because it has not been registered yet"
                    )
                else:
                    _val.append(
                        parser_inf["parser"](
                            v,
                            is_list and parser_inf["allow_list"],
                            self._delimiter,
                        )
                    )
            parsed_map[find_key(key)] = {
                "val": _val,
                "is_list": is_list,
                "default_val": None,
            }
        # assign default value to empty field
        for key, opt in self._args.items():
            if parsed_map.get(key) == None:
                is_list, t = extract_list_type(opt["type"])
                if opt["val"] == None and not opt["optional"]:
                    utils.panic(
                        "Cap.parse: "
                        + f'option "{key}":{opt["type"]} is required but it is missing'
                    )
                    pass
                parsed_map[key] = {
                    "val": [],
                    "is_list": is_list,
                    "default_val": opt["val"],
                }

        return Parsed(out["args"], parsed_map)
