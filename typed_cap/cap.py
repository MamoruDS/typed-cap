from __future__ import annotations
import inspect
import json
import sys
from typed_cap.types import (
    ArgNamed,
    ArgOption,
    ArgTypes,
    ArgsParserKeyError,
    ArgsParserMissingArgument,
    ArgsParserMissingValue,
    ArgsParserOptions,
    ArgsParserUndefinedParser,
    ArgsParserUnexpectedValue,
    BasicArgOption,
    CapArgKeyNotFound,
    CapInvalidAlias,
    CapInvalidDefaultValue,
    CapInvalidValue,
    CapUnknownArg,
    Unhandled,
    VALID_ALIAS_CANDIDATES,
)
from typed_cap.args_parser import args_parser
from typed_cap.cmt_param import parse_anno_cmt_params
from typed_cap.typing import (
    VALIDATOR,
    AnnoExtra,
    ValidVal,
    get_optional_candidates,
    get_queue_type,
    get_type_candidates,
    argstyping_parse,
    argstyping_parse_extra,
)
from typed_cap.utils import (
    RO,
    flatten,
    get_terminal_width,
    is_T_based,
    panic,
    split_by_length,
    unwrap_or,
)
from typed_cap.utils.code import (
    get_all_comments_parameters,
    get_annotations,
    get_docs_from_annotations,
)
from typed_cap.utils.color import Colors, fg
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    NoReturn,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    get_args,
)


ArgCallback = Callable[["Cap", List[List]], Union[NoReturn, List[List]]]


# _ArgOpt = ArgOption[ArgCallback]
_ArgOpt = ArgOption


class _ParsedVal(TypedDict):
    val: List[List[Any]]
    default_val: Optional[Any]
    queue_type: Optional[Literal["list", "tuple"]]


T = TypeVar("T", bound=Union[TypedDict, object])


class _GVCS(Generic[T]):
    _t_based: Union[Type[dict], Type[object]]
    _gvc: T

    def __init__(self, t: Union[Type[dict], Type[object]], val_ctr: T) -> None:
        self._t_based = t
        self._gvc = val_ctr

    def setVal(self, key: str, val: Any):
        if self._t_based is dict:
            self._gvc[key] = val  # type: ignore
        elif self._t_based is object:
            self._gvc.__setattr__(key, val)


class Parsed(Generic[T]):
    _argstype: Type[T]
    _args_obj: Optional[T]
    _args: List[str]
    _parsed_map: Dict[str, _ParsedVal]

    def __init__(
        self,
        argstype: Type[T],
        args: List[str],
        parsed_map: Dict[str, _ParsedVal],
        args_obj: Optional[T],
    ) -> None:
        self._argstype = argstype
        self._args = args
        self._parsed_map = parsed_map
        self._args_obj = args_obj

    @property
    def arguments(self) -> List[str]:
        return self._args

    @property
    def args(self) -> List[str]:
        return self.arguments

    @property
    def value(self) -> T:
        val: T
        gvc: _GVCS
        t_based = is_T_based(self._argstype)
        if t_based is dict:
            val = {}  # type: ignore
            gvc = _GVCS(dict, val)
        elif t_based is object:
            if self._args_obj is None:
                raise Unhandled("args_obj is None", "Parsed.value")
            val = self._args_obj
            gvc = _GVCS(object, val)
        else:
            raise Unhandled()

        for key, parsed in self._parsed_map.items():
            pv = parsed["val"]
            pv = flatten(pv)
            if len(pv) == 0:
                gvc.setVal(key, parsed["default_val"])
            elif parsed["queue_type"] == "list":
                gvc.setVal(key, flatten(pv))
            elif parsed["queue_type"] == "tuple":
                gvc.setVal(key, pv[-1])
            else:
                gvc.setVal(key, pv[-1])
        return val

    @property
    def val(self) -> T:
        return self.value

    def count(self, name: str) -> int:
        parsed = self._parsed_map.get(name)
        if parsed is not None:
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
        if c._about is not None:
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
            about = []
            if c._args[key]["about"] is not None:
                about.append(c._args[key]["about"])

            default_val = None
            if c._args[key]["val"] is None:
                if c._args[key]["cls_attr_val"] is not None:
                    default_val = str(c._args[key]["cls_attr_val"])
            else:
                default_val = str(c._args[key]["val"])
            if default_val is not None and c._args[key]["show_default"]:
                about.append(f"(default: {default_val})")

            about = split_by_length(
                " ".join(about),
                remain_width,
                add_hyphen=True,
                remove_leading_space=True,
            )

            if len(about) == 0:
                about = [""]
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
        if c._name is not None:
            print(f"{c._name} {ver}")
        else:
            print(ver)
    exit(0)


def helper_arg_help(
    cap: "Cap",
    name: str = "help",
    alias: Optional[VALID_ALIAS_CANDIDATES] = None,
):
    cap.add_argument(
        name,
        arg_type=Optional[bool],
        about="display the help text",
        alias=alias if alias is not None else "h",
        callback=_helper_help_cb,
        callback_priority=0,
        hide=True,
        prevent_overwrite=True,
        ignore_invalid_alias=False if alias is not None else True,
    )
    cap._preset_helper_used = True


def helper_arg_version(
    cap: "Cap",
    name: str = "version",
    alias: Optional[VALID_ALIAS_CANDIDATES] = None,
):
    cap.add_argument(
        name,
        arg_type=Optional[bool],
        about="print version info and exit",
        alias=alias if alias is not None else "V",
        callback=_helper_version_cb,
        callback_priority=2,
        hide=True,
        prevent_overwrite=True,
        ignore_invalid_alias=False if alias is not None else True,
    )
    cap._preset_helper_used = True


class _Helper_fn(Protocol):
    def __call__(
        self,
        cap: "Cap",
        name: str,
        alias: Optional[VALID_ALIAS_CANDIDATES] = None,
    ) -> None:
        ...


class _Helpers(TypedDict):
    arg_help: _Helper_fn
    arg_version: _Helper_fn


# TODO: remove this
helpers: _Helpers = {
    "arg_help": helper_arg_help,
    "arg_version": helper_arg_version,
}


def colorize_text_t_type(t: Type) -> str:
    tn = ""
    try:
        tn: str = t.__name__
    except AttributeError:
        tn = str(t)
    return str(fg(tn, Colors.Blue))


def colorize_text_t_option_name(key: str) -> str:
    return str(fg(key, Colors.Yellow))


def colorize_text_t_value(val: Any) -> str:
    try:
        return str(fg(val, Colors.Red))
    except Exception as err:
        print(err)
        return "[...]"
        # TODO:


class Cap(Generic[K, T, U]):
    _attributes: Dict[str, Any]
    _argstype: Type[T]
    _args: Dict[str, _ArgOpt]
    _about: Optional[str]
    _delimiter: RO[str]
    _name: Optional[str]
    _version: Optional[str]
    _raw_err: bool
    _preset_helper_used: bool
    # cap options
    stop_at_type: Optional[type]
    _add_helper_help: bool

    @staticmethod
    def helpers() -> _Helpers:
        return helpers

    def __init__(
        self,
        argstype: Type[T],
        stop_at_type: Optional[type] = None,
        use_cls_doc_as_about: bool = True,
        use_anno_doc_as_about: bool = True,
        use_anno_cmt_params: bool = True,
        add_helper_help: bool = True,
    ) -> None:
        self._attributes = {}
        self._argstype = argstype
        self._args = {}
        self._about = None
        self._delimiter: RO[str] = RO.Some(",")
        self._name = None
        self._version = None
        self._raw_err = False
        self._preset_helper_used = False
        #
        self.stop_at_type = stop_at_type
        #
        self._parse_argstype()
        self._parse_anno_details()

        if use_cls_doc_as_about:
            self._about = inspect.getdoc(self._argstype)

        if use_anno_doc_as_about:
            for name, opt in self._args.items():
                self._args[name]["about"] = unwrap_or(opt["about"], opt["doc"])

        if use_anno_cmt_params:
            named_params = parse_anno_cmt_params(self._args)
            for name, params in named_params.items():
                #
                alias = params.get("alias", None)
                if alias is not None:
                    self._set_alias(name, alias)
                #
                show_default = params.get("show_default", None)
                if show_default is not None:
                    self._args[name]["show_default"] = show_default
                #
                delimiter = params.get("delimiter", None)
                if delimiter is not None:
                    self._args[name]["local_delimiter"] = delimiter
                #
                self._attributes["enum_on_value"] = params.get(
                    "enum_on_value", False
                )

        self._add_helper_help = add_helper_help

    def _get_key(self, name: str) -> Union[NoReturn, str]:
        for key, opt in self._args.items():
            if key == name:
                return key
            if opt["alias"] == name:
                return key
        raise CapArgKeyNotFound(name)

    def _set_alias(
        self, key: str, alias: Optional[str]
    ) -> Union[NoReturn, None]:
        opt = self._args.get(key)
        if opt is None:
            raise CapArgKeyNotFound(key)
        else:
            if alias is not None:
                # if alias not in get_args(VALID_ALIAS_CANDIDATES):
                #     raise CapInvalidAlias(key, alias)
                try:
                    self._get_key(alias)
                    raise CapInvalidAlias(key, alias)
                except CapArgKeyNotFound:
                    self._args[key] = {**opt, **{"alias": alias}}  # type: ignore
            else:
                self._args[key] = {**opt, **{"alias": None}}  # type: ignore

    def _panic(self, msg: str, alt_title: str, err: CAP_ERR) -> NoReturn:
        if self._raw_err:
            raise err
        else:
            title = unwrap_or(self._name, alt_title)
            err_msg = f"{title}: {msg}\n\t{err.__class__.__name__}"
            panic(err_msg)

    def _parse_anno_details(self):
        annos = get_annotations(self._argstype, stop_at=self.stop_at_type)
        named_doc = get_docs_from_annotations(annos)
        named_cmt_params = get_all_comments_parameters(annos)
        for name, doc in named_doc.items():
            self._args[name]["doc"] = doc
        for name, cmt_params in named_cmt_params.items():
            self._args[name]["cmt_params"] = cmt_params

    def _parse_argstype(self):
        typed: Dict[str, Type]
        extra: Optional[Dict[str, AnnoExtra]] = None
        if sys.version_info.minor < 9:
            typed = argstyping_parse(self._argstype)
        else:
            typed, extra = argstyping_parse_extra(self._argstype)

        for key, t in typed.items():
            attr_val = None
            try:
                attr_val = self._argstype.__getattribute__(self._argstype, key)  # type: ignore
            except AttributeError:
                ...
            except TypeError:
                # TypeError: descriptor '__getattribute__' requires a 'dict' object but received a '_TypedDictMeta'
                ...
            self.add_argument(
                key,
                arg_type=t,
                callback_priority=0,
                hide=False,
                cls_attr_val=attr_val,
                prevent_overwrite=False,
                ignore_invalid_alias=False,
            )
        if extra is not None:
            _ext: Dict[K, AnnoExtra] = extra  # type: ignore
            self.helper({k: v.to_helper() for k, v in _ext.items()})

    def add_argument(
        self,
        key: str,
        arg_type: Type,
        about: Optional[str] = None,
        alias: Optional[VALID_ALIAS_CANDIDATES] = None,
        default: Optional[Any] = None,
        callback: Optional[ArgCallback] = None,
        callback_priority: int = 1,
        hide: bool = False,
        doc: Optional[str] = None,
        show_default: bool = True,
        cls_attr_val: Optional[Any] = None,
        prevent_overwrite: bool = False,
        ignore_invalid_alias: bool = False,
    ) -> Cap:
        if self._args.get(key) is not None and prevent_overwrite:
            # TODO: sending any message?
            return self
        self._args[key] = {
            "val": default,
            "type": arg_type,
            "about": about,
            "alias": None,
            "cb": callback,
            "cb_idx": callback_priority,
            "hide": hide,
            "doc": doc,
            "cmt_params": {},
            "show_default": show_default,
            "cls_attr_val": cls_attr_val,
            "local_delimiter": RO.NONE(),
        }
        if alias is not None:
            try:
                self._set_alias(key, alias)
            except CapInvalidAlias as err:
                if not ignore_invalid_alias:
                    raise err
        return self

    def set_delimiter(self, delimiter: str) -> Cap:
        # TODO: re support
        if len(delimiter) == 0:
            raise ValueError(
                "Invalid delimiter; length of delimiter:<str> larger than 0"
            )
        self._delimiter = RO.Some(delimiter)
        return self

    def set_callback(
        self, key: str, callback: ArgCallback, priority: int = 1
    ) -> Cap:
        if self._args.get(key) is not None:
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
        if is_T_based(self._argstype) is object:
            # TODO: TBD: should default be available for object-based?
            print(
                "[warn] `default` has been ignore since cap using an object-based argstype"
            )
        else:
            for arg, val in value.items():  # type: ignore
                try:
                    t = self._args[arg]["type"]
                    valid, _, _ = VALIDATOR.extract(t, val, cvt=False).unwrap()
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
                        desc=f"unknown issue: {err.__class__.__name__}",
                        loc="Cap.default_strict",
                    )
        return self

    def helper(self, helpers: Dict[K, BasicArgOption]) -> Cap:
        if self._preset_helper_used:
            print(
                "[warn] detected call of `Cap.helper` after call of preset helpers"
            )
        for arg, opt in helpers.items():  # type: ignore
            try:
                try:
                    opt: Dict[str, str]
                    alias = opt.pop("alias")
                    self._set_alias(arg, alias)
                except KeyError:
                    ...
                self._args[arg] = {**self._args[arg], **opt}  # type: ignore[misc]

            except KeyError as err:
                name = str(err)
                self._panic(
                    f"unknown named argument {colorize_text_t_option_name(name)}",
                    "Cap.helper",
                    CapUnknownArg(name, "helper"),
                )
            except CapInvalidAlias as err:
                raise err
            except Exception as err:
                raise Unhandled(
                    desc=f"unknown issue: {err.__class__.__name__}",
                    loc="Cap.helper",
                )
        return self

    def _before_parse(self):
        if self._add_helper_help:
            if self._args.get("help") is None:
                self.helpers()["arg_help"](self, "help")

    def parse(
        self,
        argv: List[str] = sys.argv[1:],
        args_parser_options: Optional[ArgsParserOptions] = None,
        validator: Optional[ValidVal] = None,
    ) -> Parsed[T]:
        self._before_parse()

        if validator is None:
            validator = VALIDATOR

        validator.delimiter = self._delimiter
        validator.attributes = self._attributes

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
            parsed: _ParsedVal = parsed_map.get(
                key,
                {
                    "val": [],
                    "default_val": None,
                    "queue_type": None,
                },
            )
            opt = self._args[key]  # TODO:
            parsed["queue_type"] = get_queue_type(
                opt["type"], allow_optional=True
            )
            for v in val:
                t = opt["type"]
                temp_delimiter = opt["local_delimiter"]
                valid, v_got, err = validator.extract(
                    t,
                    v,
                    cvt=True,
                    temp_delimiter=temp_delimiter,
                    leave_scope=True,
                ).unwrap()

                # TODO: catch extract failed
                if valid:
                    parsed["val"].append([v_got])
                else:
                    self._panic(
                        f"invalid value {colorize_text_t_value(v)} for option {colorize_text_t_option_name(key)}:{colorize_text_t_type(t)}",
                        "Cap.default_strict",
                        CapInvalidValue(key, t, v),
                    )
            parsed_map[key] = parsed

        # callbacks
        cb_list: List[Tuple[str, int]] = []
        for key, opt in self._args.items():
            if opt["cb"] is not None:
                cb_list.append((key, opt["cb_idx"]))
        cb_list = sorted(cb_list, key=lambda x: x[1])
        cb_list.reverse()
        for key, _ in cb_list:
            _p = parsed_map.get(key)
            if _p is None:
                continue
            else:
                parsed = _p
                if len(parsed["val"]) >= 0:
                    try:
                        arg = self._args[key]
                        cb = arg["cb"]
                        if cb is not None:
                            parsed_map[key]["val"] = cb(self, parsed["val"])
                    except KeyError:
                        continue

        # assign default value to empty field
        args_obj: Optional[T] = None
        T_based = is_T_based(self._argstype)
        if T_based is object:
            args_obj = self._argstype()  # type: ignore
        for key, opt in self._args.items():
            if opt["hide"]:
                if parsed_map.get(key) is not None:
                    parsed_map.pop(key)
            else:
                if parsed_map.get(key) is None:
                    parsed_map[key] = {
                        "val": [],
                        "default_val": opt[
                            "val"
                        ],  # TODO: checking typeof default value
                        "queue_type": get_queue_type(
                            opt["type"], allow_optional=True
                        ),
                    }
                    if (
                        parsed_map[key]["default_val"] is None
                        and T_based is object
                        and args_obj is not None
                    ):
                        try:
                            parsed_map[key][
                                "default_val"
                            ] = args_obj.__getattribute__(key)
                        except AttributeError:
                            ...
                    if (
                        parsed_map[key]["default_val"] is None
                        and get_optional_candidates(opt["type"]) is None
                    ):
                        self._panic(
                            f"option {colorize_text_t_option_name(key)}:{colorize_text_t_type(opt['type'])} is required but it is missing",
                            "Cap.parse",
                            ArgsParserMissingArgument(key, opt["type"]),
                        )

        return Parsed(self._argstype, out["args"], parsed_map, args_obj)
