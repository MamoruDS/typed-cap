from __future__ import annotations
import json
import sys
from typed_cap.types import (
    ArgNamed,
    ArgOpt,
    ArgTypes,
    ArgsParserKeyError,
    ArgsParserMissingArgument,
    ArgsParserMissingValue,
    ArgsParserOptions,
    ArgsParserUndefinedParser,
    ArgsParserUnexpectedValue,
    CapArgKeyNotFound,
    CapInvalidAlias,
    CapInvalidDefaultValue,
    CapInvalidValue,
    CapUnknownArg,
    Unhandled,
    VALID_ALIAS_CANDIDATES,
)
from typed_cap.args_parser import args_parser
from typed_cap.typing import (
    VALIDATOR,
    get_type_candidates,
    is_optional,
    is_queue,
    typpeddict_parse,
)
from typed_cap.utils import (
    flatten,
    get_terminal_width,
    panic,
    split_by_length,
    to_red,
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
    type: Type
    about: Optional[str]
    alias: Optional[VALID_ALIAS_CANDIDATES]
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
                val[key] = flatten(pv) if parsed["is_list"] else pv[-1]
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
    CapInvalidDefaultValue,
    CapInvalidValue,
    CapUnknownArg,
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
            about = split_by_length(
                about, remain_width, add_hyphen=True, remove_leading_space=True
            )
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
        arg_type=Optional[bool],
        about="display the help text",
        alias=alias,
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
        arg_type=Optional[bool],
        about="print version info and exit",
        alias=alias,
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


def colorize_text_t_type(t: Type) -> str:
    tn = ""
    try:
        tn = t.__name__
    except AttributeError:
        tn = str(t)
    return to_blue(tn)


def colorize_text_t_option_name(key: str) -> str:
    return to_yellow(key)


def colorize_text_t_value(val: Any) -> str:
    try:
        return to_red(str(val))
    except Exception as err:
        print(err)
        return "[...]"
        # TODO:


class Cap(Generic[K, T, U]):
    _argstype: Type[T]
    _args: Dict[str, _ArgOpt]
    _delimiter: Optional[str] = ","
    _about: Optional[str]
    _name: Optional[str]
    _version: Optional[str]
    _raw_err: bool

    def __init__(
        self,
        argstype: Type[T],
    ) -> None:
        self._argstype = argstype
        self._args = {}
        self._parse_argstype()
        self._about = None
        self._name = None
        self._version = None
        self._raw_err = False

    def _get_key(self, name: str) -> Union[NoReturn, str]:
        for key, opt in self._args.items():
            if key == name:
                return key
            if opt["alias"] == name:
                return key
        raise CapArgKeyNotFound(name)

    def _panic(self, msg: str, alt_title: str, err: CAP_ERR) -> NoReturn:
        if self._raw_err:
            raise err
        else:
            title = unwrap_or(self._name, alt_title)
            err_msg = f"{title}: {msg}\n\t{err.__class__.__name__}"
            panic(err_msg)

    def _parse_argstype(self):
        typed = typpeddict_parse(self._argstype)
        for key, t in typed.items():
            self._args[key] = {
                "val": None,
                "type": t,
                "about": None,
                "alias": None,
                "cb": None,
                "cb_idx": 0,
                "hide": False,
            }

    def add_argument(
        self,
        key: str,
        arg_type: Type,
        about: Optional[str] = None,
        alias: Optional[VALID_ALIAS_CANDIDATES] = None,
        default: Optional[Any] = None,
        callback: Optional[ArgCallback] = None,
        callback_priority: int = 1,
        prevent_overwrite: bool = False,
    ) -> Cap:
        if self._args.get(key) != None and prevent_overwrite:
            return self
        else:
            self._args[key] = {
                "val": default,
                "type": arg_type,
                "about": about,
                "alias": alias,
                "cb": callback,
                "cb_idx": callback_priority,
                "hide": True,
            }
            return self

    def set_delimiter(self, delimiter: Optional[str]) -> Cap:
        self._delimiter = delimiter
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
            try:
                t = self._args[arg]["type"]
                valid, _, _ = VALIDATOR.extract(t, val, cvt=False)
                if valid:
                    self._args[arg]["val"] = val
                else:
                    # raise CapInvalidDefaultValue(arg, t, val)
                    self._panic(
                        f"invalid default value {colorize_text_t_value(val)} for option {colorize_text_t_option_name(arg)}:{colorize_text_t_type(t)}",
                        "Cap.default_strict",
                        CapInvalidDefaultValue(arg, t, val),
                    )
            except KeyError as err:
                name = str(err)
                self._panic(
                    f"unknown named argument {colorize_text_t_option_name(name)}",
                    "Cap.default_strict",
                    CapUnknownArg(name, "default_strict"),
                )
            except Exception as err:
                raise Unhandled(
                    desc=f"unknown issue: {err}", loc="Cap.default_strict"
                )
        return self

    def helper(self, helpers: Dict[K, ArgOpt]) -> Cap:
        for arg, opt in helpers.items():
            try:
                self._args[arg] = {**self._args[arg], **opt}  # type: ignore[misc]
            except KeyError as err:
                name = str(err)
                self._panic(
                    f"unknown named argument {colorize_text_t_option_name(name)}",
                    "Cap.helper",
                    CapUnknownArg(name, "helper"),
                )
            except Exception as err:
                raise Unhandled(desc=f"unknown issue: {err}", loc="Cap.helper")
        return self

    def parse(
        self,
        argv: List[str] = sys.argv[1:],
        args_parser_options: Optional[ArgsParserOptions] = None,
    ) -> Parsed[T]:
        def _is_flag(t: Type) -> bool:
            if t == bool:
                return True
            try:
                can = get_type_candidates(t)
                return bool in can
            except Exception:
                return False

        named_args: List[Tuple[ArgTypes, ArgNamed]] = []
        for key, opt in self._args.items():
            named_args.append(
                (
                    "flag" if _is_flag(opt["type"]) else "option",
                    (key, opt["alias"]),
                )
            )

        try:
            out = args_parser(argv, named_args, args_parser_options)
        except ArgsParserKeyError as err:
            self._panic(
                f"unknown {err.key_type} {colorize_text_t_option_name(err.key)}",
                "Cap.parse",
                err,
            )
        except ArgsParserUnexpectedValue as err:
            key = self._get_key(err.key)
            prefix = "--"
            self._panic(
                f"the value for argument {colorize_text_t_option_name(prefix + key)} wasn't expected",
                "Cap.parse",
                err,
            )
        except ArgsParserMissingValue as err:
            key = self._get_key(err.key)
            prefix = "--"
            self._panic(
                f"the argument {colorize_text_t_option_name(prefix+key)} requires a value, which was not supplied",
                "Cap.parse",
                err,
            )

        parsed_map: Dict[str, _ParsedVal] = {}
        # extract process
        for name, val in out["options"].items():
            key = self._get_key(name)
            parsed = parsed_map.get(
                key,
                {
                    "val": [],
                    "default_val": None,
                    "is_list": False,
                },
            )
            opt = self._args[key]  # TODO:
            parsed["is_list"] = is_queue(opt["type"], allow_optional=True)
            for v in val:
                t = opt["type"]
                valid, v_got, err = VALIDATOR.extract(t, v, cvt=True)
                if valid:
                    parsed["val"].append([v_got])
                else:
                    self._panic(
                        f"invalid value {colorize_text_t_value(v)} for option {colorize_text_t_option_name(key)}:{colorize_text_t_type(t)}",
                        "Cap.default_strict",
                        CapInvalidValue(key, t, v),
                    )
            # # TODO: catch extract failed
            parsed_map[key] = parsed

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
                    parsed_map[key] = {
                        "val": [],
                        "default_val": opt[
                            "val"
                        ],  # TODO: checking typeof default value
                        "is_list": is_queue(opt["type"]),
                    }
                    if opt["val"] == None and not is_optional(opt["type"]):
                        self._panic(
                            f"option {colorize_text_t_option_name(key)}:{colorize_text_t_type(opt['type'])} is required but it is missing",
                            "Cap.parse",
                            ArgsParserMissingArgument(key, opt["type"]),
                        )

        return Parsed(out["args"], parsed_map)
