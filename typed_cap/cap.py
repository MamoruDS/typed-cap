from __future__ import annotations
import json
import re
import sys
from inspect import getsource
from typed_cap.parser import Parser, ParserRegister, PRESET as PRESET_PARSERS
from typed_cap.types import (
    ArgOpt,
    ArgsParserKeyError,
    ArgsParserMissingArgument,
    ArgsParserMissingValue,
    ArgsParserUndefinedParser,
    ArgsParserUnexpectedValue,
    Unhandled,
    VALID_ALIAS_CANDIDATES,
)
from typed_cap.utils import (
    args_parser,
    flatten,
    get_terminal_width,
    panic,
    remove_comments,
    split_by_length,
    to_yellow,
    to_blue,
    unwrap_or,
)
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    NamedTuple,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
)


ArgCallback = Callable[["Cap", List[List]], Union[NoReturn, List[List]]]


class _ArgOpt(TypedDict):
    val: Optional[Any]
    type: str
    about: Optional[str]
    alias: Optional[VALID_ALIAS_CANDIDATES]
    optional: bool
    cb: Optional[ArgCallback]
    cb_idx: int
    hide: bool


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
                val[key] = pv if parsed["is_list"] else pv[-1]
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

CAP_ERR = Union[
    ArgsParserKeyError,
    ArgsParserMissingArgument,
    ArgsParserMissingValue,
    ArgsParserUndefinedParser,
    ArgsParserUnexpectedValue,
    Unhandled,
]


def _helper_help_cb(c: "Cap", v: List[List[bool]]) -> NoReturn:
    lns: List[Tuple[int, str]] = []
    INDENT_SIZE = 4
    if v[0][0]:
        if c._about != None:
            lns.append((0, c._about))
            lns.append((0, ""))
        lns.append((0, "OPTIONS:"))
        arg_lns: List[Tuple[str, str]] = []
        max_opt_len = 0
        for key, opt in c._args.items():
            alias = unwrap_or(opt["alias"], "   ")
            if len(alias) == 1:
                alias = f"-{alias},"
            ln = f"{alias}--{key}"
            max_opt_len = max(len(ln), max_opt_len)
            arg_lns.append((key, ln))

        MIN_ABOUT_WIDTH: int = 10
        MAX_WIDTH: int = 100
        prefix_width: int = max_opt_len + 4
        width = max(
            get_terminal_width(MAX_WIDTH) - 1 * INDENT_SIZE,
            prefix_width + MIN_ABOUT_WIDTH,
        )
        remain_width = width - prefix_width
        for key, ln in arg_lns:
            about = unwrap_or(c._args[key]["about"], "")
            about = split_by_length(about, remain_width)
            for i, abt in enumerate(about):
                if i == 0:
                    lns.append((1, ln.ljust(max_opt_len + 4) + abt))
                else:
                    lns.append((1, "".ljust(prefix_width) + abt))
        for indent, ln in lns:
            print("".ljust(indent * INDENT_SIZE) + ln)
    exit(0)


def _helper_version_cb(c: "Cap", v: List[List[bool]]) -> NoReturn:
    if v[0][0]:
        ver = unwrap_or(c._version, "unknown version")
        if c._name != None:
            print(f"{c._name} {ver}")
        else:
            print(ver)
    exit(0)


def helper_arg_help(
    cap: "Cap",
    name: str = "help",
    alias: Optional[VALID_ALIAS_CANDIDATES] = "h",
):
    cap.add_argument(
        name,
        type="bool",
        about="display the help text",
        alias=alias,
        optional=True,
        callback=_helper_help_cb,
        callback_priority=0,
        prevent_overwrite=True,
    )


def helper_arg_version(
    cap: "Cap",
    name: str = "version",
    alias: Optional[VALID_ALIAS_CANDIDATES] = "V",
):
    cap.add_argument(
        name,
        type="bool",
        about="print version info and exit",
        alias=alias,
        optional=True,
        callback=_helper_version_cb,
        callback_priority=2,
        prevent_overwrite=True,
    )


class _Helpers(TypedDict):
    arg_help: Callable[["Cap", str, Optional[VALID_ALIAS_CANDIDATES]], None]
    arg_version: Callable[["Cap", str, Optional[VALID_ALIAS_CANDIDATES]], None]


helpers: _Helpers = {
    "arg_help": helper_arg_help,
    "arg_version": helper_arg_version,
}


class Cap(Generic[K, T, U]):
    _argstype: Type[T]
    _args: Dict[str, _ArgOpt]
    _delimiter: Optional[str] = ","
    _parser_register: ParserRegister
    _about: Optional[str]
    _name: Optional[str]
    _version: Optional[str]
    _raw_err: bool

    def __init__(
        self,
        argstype: Type[T],
    ) -> None:
        self._argstype = argstype
        self._parser_register = PRESET_PARSERS
        self._parse_argstype()
        self._about = None
        self._name = None
        self._version = None
        self._raw_err = False

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

    def _panic(self, msg: str, alt_title: str, err: CAP_ERR) -> NoReturn:
        if self._raw_err:
            raise err
        else:
            title = unwrap_or(self._name, alt_title)
            err_msg = f"{title}: {msg}"
            panic(err_msg)

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
                raise Exception(
                    "failed to parse given types in TypedDict"
                )  # TODO:
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
                "hide": False,
            }

    def add_argument(
        self,
        key: str,
        type: Union[str, Type[str], Type[int], Type[float], Type[bool]],
        about: Optional[str] = None,
        alias: Optional[VALID_ALIAS_CANDIDATES] = None,
        optional: bool = False,
        default: Optional[Any] = None,
        callback: Optional[ArgCallback] = None,
        callback_priority: int = 1,
        prevent_overwrite: bool = False,
    ) -> Cap:
        if self._args.get(key) != None and prevent_overwrite:
            return self
        else:
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
                "hide": True,
            }
            return self

    def set_delimiter(self, delimiter: Optional[str]) -> Cap:
        self._delimiter = delimiter
        return self

    def set_parser(
        self, type_name: str, parser: Parser, allow_list: bool
    ) -> Cap:
        self._parser_register.__setitem__(
            type_name, {"parser": parser, "allow_list": allow_list}
        )
        return self

    def set_callback(
        self, key: str, callback: ArgCallback, priority: int = 1
    ) -> Cap:
        if self._args.get(key) != None:
            self._args[key]["cb"] = callback
            self._args[key]["cb_idx"] = priority
        else:
            raise KeyError(
                f"'{key}' haven't been defined as an argument in Cap"
            )
        return self

    def raw_exception(self, tog: bool) -> Cap:
        self._raw_err = tog
        return self

    def name(self, text: str) -> Cap:
        self._name = text
        return self

    def about(self, text: str, add_helper: bool = False) -> Cap:
        self._about = text
        if add_helper:
            helper_arg_help(self)
        return self

    def version(self, text: str, add_helper: bool = False) -> Cap:
        self._version = text
        if add_helper:
            helper_arg_version(self)
        return self

    def default(self, value: U) -> Cap:
        return self.default_strict(value)  # type: ignore[arg-type]

    def default_strict(self, value: T) -> Cap:
        for arg, val in value.items():
            self._args[arg]["val"] = val
        return self

    def helper(self, helpers: Dict[K, ArgOpt]) -> Cap:
        for arg, opt in helpers.items():
            self._args[arg] = {**self._args[arg], **opt}  # type: ignore[misc]
        return self

    def parse(
        self,
        args: List[str] = sys.argv[1:],
        ignore_unknown: bool = False,
        ignore_unknown_flags: bool = False,
        ignore_unknown_options: bool = False,
    ) -> Parsed[T]:

        flags: List[Tuple[str, Optional[str]]] = []
        options: List[Tuple[str, Optional[str]]] = []
        for key, opt in self._args.items():
            if opt["type"] == "bool":
                flags.append((key, opt["alias"]))
            else:
                options.append((key, opt["alias"]))

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
            self._panic(
                f"unknown {err.key_type} '{err.key}'", "Cap.parse", err
            )
        except ArgsParserUnexpectedValue as err:
            key = self._get_key(err.key)
            prefix = "--"
            self._panic(
                f"the value for argument '{to_yellow(prefix + key)}' wasn't expected",
                "Cap.parse",
                err,
            )
        except ArgsParserMissingValue as err:
            key = self._get_key(err.key)
            prefix = "--"
            self._panic(
                f"the argument '{to_yellow(prefix+key)}' requires a value, which was not supplied",
                "Cap.parse",
                err,
            )

        parsed_map: Dict[str, _ParsedVal] = {}
        for key, val in out["options"].items():
            opt = self._args[self._get_key(key)]  # TODO:
            is_list, t = self._extract_list_type(opt["type"])
            _val: List[List[Any]] = []
            for v in val:
                if isinstance(v, bool):
                    _val.append([v])
                    continue
                parser_inf = self._parser_register.get(t)
                if parser_inf == None:
                    self._panic(
                        f"cannot handle type {to_blue(t)} because it has not been registered yet",
                        "Cap.parse",
                        ArgsParserUndefinedParser(t),
                    )
                else:
                    _val.append(
                        parser_inf["parser"](
                            v,
                            is_list and parser_inf["allow_list"],
                            self._delimiter,
                        )
                    )
            parsed_map[self._get_key(key)] = {  # TODO:
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
                continue
            else:
                if len(parsed["val"]) >= 0:
                    try:
                        arg = self._args[key]
                        cb = arg["cb"]
                        if cb != None:
                            parsed_map[key]["val"] = cb(self, parsed["val"])
                    except KeyError:
                        continue

        # assign default value to empty field
        for key, opt in self._args.items():
            if opt["hide"]:
                if parsed_map.get(key) != None:
                    parsed_map.pop(key)
            else:
                if parsed_map.get(key) == None:
                    is_list, t = self._extract_list_type(opt["type"])
                    if opt["val"] == None and not opt["optional"]:
                        self._panic(
                            f"option '{to_yellow(key)}':{to_blue(opt['type'])} is required but it is missing",
                            "Cap.parse",
                            ArgsParserMissingArgument(key, opt["type"]),
                        )
                    parsed_map[key] = {
                        "val": [],
                        "is_list": is_list,
                        "default_val": opt["val"],
                    }

        return Parsed(out["args"], parsed_map)
