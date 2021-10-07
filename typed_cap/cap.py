import json
import re
import sys
import inspect
from inspect import getsource
from typed_cap.constants import SUPPORT_TYPES, ValidChar
from typed_cap.parser import Parser, ParserRegister, PRESET as PRESET_PARSERS
from typed_cap.types import (
    ArgsParserKeyError,
    ArgsParserMissingValue,
    ArgsParserUnexpectedValue,
    Unhandled,
)
from typed_cap.utils import (
    args_parser,
    flatten,
    panic,
    remove_comments,
    to_yellow,
    to_blue,
)
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    get_args,
)


class ArgOpt(TypedDict, total=False):
    about: str
    alias: ValidChar
    # optional: bool


ArgCallback = Callable[[List], None]


class _ArgOpt(TypedDict):
    val: Optional[Any]
    type: str
    about: Optional[str]
    alias: Optional[ValidChar]
    optional: bool
    cb: Optional[ArgCallback]
    cb_idx: int


class _ParsedVal(TypedDict):
    val: List[List[Any]]
    default_val: Optional[Any]
    is_list: bool


T = TypeVar("T", bound=TypedDict)


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
            pv = flatten(pv)
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
            panic(f'Parsed.count: cannot find option with name "{name}"')

    def __json__(self, indent: Optional[int]) -> str:
        j = {}
        j["arguments"] = self.arguments
        j["value"] = self.value
        return json.dumps(j, indent=indent)

    def toJSON(self, indent: Optional[int] = None) -> str:
        return self.__json__(indent=indent)


U = TypeVar("U", bound=Union[TypedDict, Dict[str, Any]])
K = TypeVar("K", bound=str)


class Cap(Generic[K, T, U]):
    _argstype: Type[T]
    _args: Dict[str, _ArgOpt]
    _delimiter: Optional[str] = ","
    _parser_register: ParserRegister
    _about: str = ""
    _name: str = ""
    _version: str = ""

    def __init__(
        self,
        argstype: Type[T],
    ) -> None:
        self._argstype = argstype
        self._parser_register = PRESET_PARSERS
        self._parse_argstype()

    def _get_key(
        self, name: str
    ) -> Union[NoReturn, str,]:
        for key, opt in self._args.items():
            if key == name:
                return key
            if opt["alias"] == name:
                return key
        panic(f"key '{name}' not found")

    def _extract_list_type(self, t: str) -> Tuple[bool, str]:
        if t == "list":
            return True, "str"
        reg = re.compile(r"^(list\[(?P<type>\w+)\])$")
        m = reg.match(t)
        if m != None:
            return True, m.group("type")
        else:
            return False, t

    def _parse_argstype(self):
        types = remove_comments(getsource(self._argstype))[1:]
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
            self._args[key] = {
                "val": None,
                "type": t,
                "about": None,
                "alias": None,
                "optional": opt,
                "cb": None,
                "cb_idx": 0,
            }

    def add_argument(
        self,
        key: str,
        type: Union[str, Type[str], Type[int], Type[float], Type[bool]],
        about: Optional[str] = None,
        alias: Optional[ValidChar] = None,
        optional: bool = False,
        default: Optional[Any] = None,
        callback: Optional[ArgCallback] = None,
        callback_priority: int = 1,
        prevent_overwrite: bool = False,
    ):
        if self._args.get(key) != None and prevent_overwrite:
            return
        t: str
        if isinstance(type, str):
            t = type
        else:
            if type == str:
                t = "str"
            elif type == int:
                t = "int"
            elif type == float:
                t = "float"
            elif type == bool:
                t = "bool"
            else:
                raise Unhandled(
                    desc="cannot convert given type to string",
                    loc="Cap.add_argument",
                )
        self._args[key] = {
            "val": default,
            "type": t,
            "about": about,
            "alias": alias,
            "optional": optional,
            "cb": callback,
            "cb_idx": callback_priority,
        }

    def set_delimiter(self, delimiter: Optional[str]):
        self._delimiter = delimiter

    def set_parser(self, type_name: str, parser: Parser, allow_list: bool):
        self._parser_register.__setitem__(
            type_name, {"parser": parser, "allow_list": allow_list}
        )

    def set_callback(self, key: str, callback: ArgCallback, priority: int = 1):
        if self._args.get(key) != None:
            self._args[key]["cb"] = callback
            self._args[key]["cb_idx"] = priority
        else:
            raise KeyError(
                f"'{key}' haven't been defined as an argument in Cap"
            )

    def name(self, text: str):
        self._name = text

    def about(self, text: str):
        self._about = text

    def version(self, text: str):
        self._version = text

        def cb(v: List[bool]):
            if self._name:
                print(f"{self._name} {self._version}")
            else:
                print(self._version)
            exit(0)

        self.add_argument(
            "version",
            type="bool",
            about="print version info and exit",
            alias="V",
            optional=True,
            callback=cb,
            callback_priority=2,
            prevent_overwrite=True,
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
        ignore_unknown_flags: bool = False,
        ignore_unknown_options: bool = False,
    ) -> Parsed[T]:

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
            out = args_parser(
                args,
                flags,
                options,
                ignore_unknown=ignore_unknown,
                ignore_unknown_flags=ignore_unknown_flags,
                ignore_unknown_options=ignore_unknown_options,
            )
        except ArgsParserKeyError as err:
            panic("Cap.parse: " + f"unknown {err.key_type} '{err.key}'")
        except ArgsParserUnexpectedValue as err:
            key = self._get_key(err.key)
            # prefix = '-' if is_alias else '--'
            prefix = "--"
            panic(
                "Cap.parse: "
                + f"the value for argument '{to_yellow(prefix + key)}' wasn't expected"
            )
        except ArgsParserMissingValue as err:
            key = self._get_key(err.key)
            prefix = "--"
            panic(
                "Cap.parse: "
                + f"the argument '{to_yellow(prefix+key)}' requires a value, which was not supplied"
            )

        parsed_map: Dict[str, _ParsedVal] = {}
        for key, val in out["options"].items():
            opt = self._args[self._get_key(key)]
            is_list, t = self._extract_list_type(opt["type"])
            _val: List[List[Any]] = []
            for v in val:
                if isinstance(v, bool):
                    _val.append([v])
                    continue
                parser_inf = self._parser_register.get(t)
                if parser_inf == None:
                    panic(
                        "Cap.parse: "
                        + f"cannot handle type {to_blue(t)} because it has not been registered yet"
                    )
                else:
                    _val.append(
                        parser_inf["parser"](
                            v,
                            is_list and parser_inf["allow_list"],
                            self._delimiter,
                        )
                    )
            parsed_map[self._get_key(key)] = {
                "val": _val,
                "is_list": is_list,
                "default_val": None,
            }

        # callbacks
        cb_list: List[Tuple[str, int]] = []
        for key, opt in self._args.items():
            if opt["cb"] != None:
                cb_list.append((key, opt["cb_idx"]))
        cb_list = sorted(cb_list, key=lambda x: x[1])
        cb_list.reverse()
        for key, _ in cb_list:
            parsed = parsed_map.get(key)
            if parsed == None:
                raise Unhandled(
                    desc="getting `None` from `parsed` by using key with valid `cb`",
                    loc="Cap.parse",
                )
            else:
                if len(parsed["val"]) >= 0:
                    try:
                        arg = self._args[key]
                        cb = arg["cb"]
                        if cb != None:
                            cb(parsed["val"])
                    except KeyError:
                        continue

        # assign default value to empty field
        for key, opt in self._args.items():
            if parsed_map.get(key) == None:
                is_list, t = self._extract_list_type(opt["type"])
                if opt["val"] == None and not opt["optional"]:
                    panic(
                        "Cap.parse: "
                        + f"option '{to_yellow(key)}':{to_blue(opt['type'])} is required but it is missing"
                    )
                parsed_map[key] = {
                    "val": [],
                    "is_list": is_list,
                    "default_val": opt["val"],
                }
        return Parsed(out["args"], parsed_map)
