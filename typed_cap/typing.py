import json
import sys
from enum import EnumMeta
from types import GenericAlias
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from typing import (
    _GenericAlias,  # type: ignore
    _LiteralGenericAlias,  # type: ignore
    _TypedDictMeta,  # type: ignore
    _UnionGenericAlias,  # type: ignore
)

from .types import BasicArgOption, VALID_ALIAS_CANDIDATES
from .utils import RO, is_T_based, simple_eq, str_eq


CLS_Literal = _LiteralGenericAlias
CLS_None = type(None)
CLS_Queue = _GenericAlias
CLS_TypedDict = _TypedDictMeta
CLS_Union = _UnionGenericAlias

T = TypeVar("T")


class ValidRes(Generic[T]):
    _valid: bool
    _data: RO[T]
    _error: RO[Exception]

    def __init__(self) -> None:
        self._valid = False
        self._data = RO.NONE()
        self._error = RO.NONE()

    def some(self, val: T):
        self._data = RO.Some(val)

    def none(self):
        self._data = RO.NONE()

    def error(self, err: Exception):
        self._error = RO.Some(err)

    def valid(self):
        self._valid = True

    def is_valid(self) -> bool:
        return self._valid

    @property
    def data(self) -> RO[T]:
        return self._data

    @property
    def value(self) -> Optional[T]:
        return self._data.value

    def unwrap(self) -> Tuple[bool, Optional[T], RO[Exception]]:
        return self._valid, self._data.value, self._error

    def __str__(self) -> str:
        return json.dumps(
            {
                "valid": self._valid,
                "value": self._data.value,
                "error": self._error.value,
            },
            indent=4,
        )


ValidFunc = Callable[["ValidVal", Type[T], Any, bool], ValidRes[T]]


class AnnoExtra:
    about: Optional[str] = None
    alias: Optional[VALID_ALIAS_CANDIDATES] = None

    def __init__(
        self,
        about: Optional[str],
        alias: Optional[VALID_ALIAS_CANDIDATES],
    ) -> None:
        self.alias = alias
        self.about = about

    def to_helper(self) -> BasicArgOption:
        return {"about": self.about, "alias": self.alias}


class TypeInf(TypedDict):
    t: Any
    tt: Any
    c: Any
    v: ValidFunc


class ValidVal:
    attributes: Dict[str, Any]
    _validators: Dict[str, TypeInf]
    _delimiter: RO[str]

    # temp only
    _temp_delimiter: RO[str]

    def __init__(self, validators: Dict[str, TypeInf]) -> None:
        self.attributes = {}
        self._validators = validators
        self._delimiter = RO.Some(",")
        self._temp_delimiter = RO.NONE()

    def _class_of(self, obj: Any) -> Optional[Any]:
        try:
            return obj.__class__
        except AttributeError:
            return None
        except Exception as e:
            raise e

    @property
    def validators(self) -> Dict[str, TypeInf]:
        return self._validators

    @property
    def delimiter(self) -> RO[str]:
        if self._temp_delimiter.is_some():
            return self._temp_delimiter
        else:
            return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: RO[str]) -> None:
        self._delimiter = delimiter

    @overload
    def extract(
        self,
        t: str,
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes:
        ...

    @overload
    def extract(
        self,
        t: Type[T],
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes[T]:
        ...

    def extract(
        self,
        t: Union[Type[T], str],
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ):
        # apply all temporal settings
        if temp_delimiter.is_some():
            self._temp_delimiter = temp_delimiter

        REG = self.validators
        res: Optional[ValidRes[T]] = None
        if isinstance(t, str):
            if REG.get(t) is not None:
                res = REG[t]["v"](self, REG[t]["t"], val, cvt)
        else:
            for _, t_inf in REG.items():
                if (
                    t == t_inf["t"]
                    or type(t) == t_inf["tt"]
                    or self._class_of(t) == t_inf["c"]
                ):
                    res = t_inf["v"](self, t, val, cvt)
                else:
                    continue

        # remove all temporal settings
        if leave_scope:
            self._temp_delimiter = RO.NONE()

        if res is None:
            # TODO:
            print(f"\t> t.__class__: {t.__class__}")
            print(f"\t> type(t): {type(t)}")
            print(f"\t> t: {t}")
            raise Exception("not found")
        else:
            return res


def annotation_extra(
    alias: Optional[VALID_ALIAS_CANDIDATES] = None,
    about: Optional[str] = None,
) -> AnnoExtra:
    return AnnoExtra(about, alias)


def _valid_none(_vv: ValidVal, t: CLS_None, val: Any, _cvt: bool):
    v = ValidRes[None]()
    if type(val) == t:
        v.some(None)
        v.valid()
    return v


def _valid_bool(_vv: ValidVal, _t: Any, val: Any, cvt: bool):
    v = ValidRes[bool]()
    if cvt:
        if val in [
            0,
            "false",
            "False",
        ]:  # TODO: custom valid values
            v.some(False)
            v.valid()
        elif val in [
            1,
            "true",
            "True",
        ]:  # TODO: custom valid values
            v.some(True)
            v.valid()
    else:
        if isinstance(val, bool):
            v.some(val)
            v.valid()
    return v


def _valid_int(_vv: ValidVal, _t: Any, val: Any, cvt: bool):
    v = ValidRes[int]()
    if cvt:
        try:
            v.some(int(val))
            v.valid()
        except Exception as err:
            v.error(err)
    else:
        if isinstance(val, int):
            v.some(val)
            v.valid()
    return v


def _valid_float(_vv: ValidVal, _t: Any, val: Any, cvt: bool):
    v = ValidRes[float]()
    if cvt:
        try:
            v.some(float(val))
            v.valid()
        except Exception as err:
            v.error(err)
    else:
        if isinstance(val, float):
            v.some(val)
            v.valid()
    return v


def _valid_str(_vv: ValidVal, _t: Any, val: Any, cvt: bool):
    v = ValidRes[str]()
    if cvt:
        try:
            v.some(str(val))
            v.valid()
        except Exception as err:
            v.error(err)
    else:
        if isinstance(val, str):
            v.some(val)
            v.valid()
    return v


def _valid_union(vv: ValidVal, t: CLS_Union, val: Any, cvt: bool):
    v = ValidRes[CLS_Union]()
    opts = get_args(t)
    for opt in opts:
        v_got = vv.extract(opt, val, cvt)
        if v_got.is_valid():
            return v_got
    return v


def _valid_queue(vv: ValidVal, t: CLS_Queue, val: Any, cvt: bool):
    v = ValidRes[CLS_Queue]()
    loc_type = get_origin(t)
    if type(val) == loc_type:
        elements: Union[Tuple, List] = val
        opts = get_args(t)
        arr = []
        if loc_type == tuple and len(opts) == len(elements):
            for opt, ele in zip(opts, elements):
                v_got = vv.extract(opt, ele, cvt)
                if v_got.is_valid():
                    arr.append(v_got.value)
                else:
                    arr = None
                    break

        elif loc_type == list:
            arr = []
            opt = opts[0]
            for ele in elements:
                v_got = vv.extract(opt, ele, cvt)
                if v_got.is_valid():
                    arr.append(v_got.value)
                else:
                    arr = None
                    break

        if arr is not None:
            v.valid()
            if loc_type == tuple:
                arr = tuple(arr)
            v.some(arr)
    elif cvt and isinstance(val, str) and vv.delimiter.is_some():
        # TODO: vv.delimiter is always "has some"
        arr = val.split(vv.delimiter.value)
        if loc_type == tuple:
            arr = tuple(arr)
        return vv.extract(t, arr, cvt)
    return v


def _valid_literal(vv: ValidVal, t: CLS_Literal, val: Any, cvt: bool):
    v = ValidRes[CLS_Literal]()
    candidates = get_args(t)
    if cvt:
        for can in candidates:
            cvt_res = vv.extract(type(can), val, cvt)
            if cvt_res.is_valid():
                v._data = cvt_res._data
                v.valid()
    else:
        if val in candidates:
            v.some(val)
            v.valid()
    return v


def _valid_enum(vv: ValidVal, t: EnumMeta, val: Any, _cvt: bool):
    v = ValidRes[EnumMeta]()
    try:
        on_val = vv.attributes.get("enum_on_value", False)
        cs = False  # case sensitive
        ms = list(t)  # type: ignore
        for m in ms:
            if on_val:
                v_got = vv.extract(type(m.value), val, cvt=True)
                if simple_eq(v_got.value, m.value):
                    v.some(m)
                    v.valid()
            else:
                v_got = vv.extract(str, val, cvt=True)
                if v_got.valid and str_eq(v_got.value, m.name, cs):
                    v.some(m)
                    v.valid()
    except Exception as err:
        v.error(err)
    return v


VALIDATOR = ValidVal(
    {
        "bool": {
            "t": bool,
            "tt": None,
            "c": None,
            "v": _valid_bool,
        },
        "int": {
            "t": int,
            "tt": None,
            "c": None,
            "v": _valid_int,
        },
        "float": {
            "t": float,
            "tt": None,
            "c": None,
            "v": _valid_float,
        },
        "str": {
            "t": str,
            "tt": None,
            "c": None,
            "v": _valid_str,
        },
        "none": {
            "t": CLS_None,
            "tt": None,
            "c": CLS_None,
            "v": _valid_none,
        },
        "union": {
            "t": None,
            "tt": None,
            "c": CLS_Union,
            "v": _valid_union,
        },
        "queue": {
            "t": CLS_Queue,
            "tt": GenericAlias,
            "c": CLS_Queue,
            "v": _valid_queue,
        },
        "literal": {
            "t": CLS_Literal,
            "tt": None,
            "c": CLS_Literal,
            "v": _valid_literal,
        },
        "enum": {
            "t": None,
            "tt": EnumMeta,
            "c": EnumMeta,
            "v": _valid_enum,
        },
    }
)


if sys.version_info.minor >= 10:
    from types import UnionType

    def _valid_uniontype(vv: ValidVal, t: UnionType, val: Any, cvt: bool):
        v = ValidRes[UnionType]()
        opts = get_args(t)
        for opt in opts:
            v_got = vv.extract(opt, val, cvt)
            if v_got.is_valid():
                return v_got
        return v

    VALIDATOR.validators.update(
        {
            "uniontype": {
                "t": None,
                "tt": None,
                "c": UnionType,
                "v": _valid_uniontype,
            }
        }
    )


def get_optional_candidates(t: Type) -> Optional[Tuple]:
    try:
        can = list(get_type_candidates(t))
        idx = can.index(CLS_None)
        can.pop(idx)
        return tuple(can)
    except Exception:
        ...
    return None


def get_queue_type(
    t: Type, allow_optional: bool = False
) -> Optional[Literal["list", "tuple"]]:
    if t in [tuple, list]:
        return t.__name__
    ot = get_origin(t)
    if ot in [tuple, list]:
        return ot.__name__  # type: ignore
    elif ot == Union and allow_optional:
        can = get_optional_candidates(t)
        if can is not None and len(can) == 1:
            _t = can[0]
            return get_queue_type(_t)
        else:
            ...
    return None


OT = TypeVar("OT")
# FIXME: Geneirc for Union???
# OT = TypeVar('OT', bound=CLS_Union)

# FIXME: incorrect hinting:
# ```
# can = get_type_candidates(Optional[int])
# -> (variable) can: Tuple[ Type[int] | None]
# ```


def get_type_candidates(t: Type[OT]) -> Tuple[Type[OT]]:
    """
    `<T extends Union>(t: Union<T>): T | NoneType`

    Examples
    ----------
    >>> get_type_candidates(Optional[int])
    (<class 'int'>, <class 'NoneType'>)
    """
    if t.__class__ == CLS_Union:
        can = get_args(t)
        return can  # type: ignore
    else:
        raise Exception()  # TODO:


def argstyping_parse(t: Type[T]) -> Dict[str, Type[T]]:
    if is_T_based(t) not in [dict, object]:
        raise Exception(
            "t should a `typing.TypedDict` or a `class` for parsing"
        )  # TODO:
    key_dict: Dict[str, Type] = get_type_hints(t)
    typed: Dict[str, Type] = dict(((k, CLS_None) for k in key_dict.keys()))

    def get_t(key: str, required: bool) -> Type:
        raw_t = key_dict[key]
        if required:
            return raw_t
        else:
            return Optional[raw_t]

    keys_req: Iterable[str]
    keys_opt: Iterable[str]
    if type(t) is CLS_TypedDict:
        keys_req = t.__required_keys__  # type: ignore FrozenSet[str]
        keys_opt = t.__optional_keys__  # type: ignore FrozenSet[str]
    else:
        keys_req = key_dict.keys()
        keys_opt = []
    for key in keys_req:
        typed[key] = get_t(key, True)
    for key in keys_opt:
        typed[key] = get_t(key, False)
    return typed


def argstyping_parse_extra(t: Type[T]):
    key_dict = get_type_hints(t, include_extras=True)
    extra: Dict[str, AnnoExtra] = {}
    for key, anno in key_dict.items():
        if get_origin(anno) is not Annotated:
            ...
        else:
            _, *anno_args = get_args(anno)
            if isinstance(anno_args[0], AnnoExtra):
                extra[key] = anno_args[0]
            else:
                ...
                # TODO: warning or error msg?
    return argstyping_parse(t), extra
