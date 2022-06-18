from inspect import isclass
from typed_cap.types import BasicArgOption, VALID_ALIAS_CANDIDATES
from typed_cap.utils import is_T_based, RO
from types import GenericAlias
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
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
)

from typing import (
    _GenericAlias,  # type: ignore
    _LiteralGenericAlias,  # type: ignore
    _TypedDictMeta,  # type: ignore
    _UnionGenericAlias,  # type: ignore
)


CLS_Literal: Type = _LiteralGenericAlias
CLS_None: Type = type(None)
CLS_Queue: Type = _GenericAlias
CLS_TypedDict: Type = _TypedDictMeta
CLS_Union: Type = _UnionGenericAlias


VALID_RES = Tuple[bool, Optional[Any], Optional[Exception]]


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
    v: Callable[["ValidVal", Type, Any, bool], VALID_RES]


class ValidVal:
    validators: Dict[str, TypeInf]
    _delimiter: RO[str]

    # temp only
    _temp_delimiter: RO[str]

    def __init__(self, validators: Dict[str, TypeInf]) -> None:
        self.validators = validators
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
    def delimiter(self) -> RO[str]:
        if self._temp_delimiter.is_some():
            return self._temp_delimiter
        else:
            return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: RO[str]) -> None:
        self._delimiter = delimiter

    def extract(
        self,
        t: Type,
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ) -> VALID_RES:
        # apply all temporal settings
        if temp_delimiter.is_some():
            self._temp_delimiter = temp_delimiter

        REG = self.validators
        res: Optional[VALID_RES] = None
        if type(t) == str:
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


def _valid_none(_vv: ValidVal, t: CLS_None, val: Any, _cvt: bool) -> VALID_RES:
    b = False
    v = None
    if type(val) == t:
        v = val
        b = True
    return b, v, None


def _valid_bool(_vv: ValidVal, _t: Any, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    if cvt:
        if val in [
            0,
            "false",
            "False",
        ]:  # TODO: custom valid values
            v = False
            b = True
        elif val in [
            1,
            "true",
            "True",
        ]:  # TODO: custom valid values
            v = True
            b = True
    else:
        if type(val) == bool:
            v = val
            b = True
    return b, v, None


def _valid_int(_vv: ValidVal, _t: Any, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    if cvt:
        try:
            v = int(val)
            b = True
        except Exception as err:
            e = err
    else:
        if type(val) == int:
            v = val
            b = True
    return b, v, e


def _valid_float(_vv: ValidVal, _t: Any, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    if cvt:
        try:
            v = float(val)
            b = True
        except Exception as err:
            e = err
    else:
        if type(val) == float:
            v = val
            b = True
    return b, v, e


def _valid_str(_vv: ValidVal, _t: Any, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    if cvt:
        try:
            v = str(val)
            b = True
        except Exception as err:
            e = err
    else:
        if type(val) == str:
            v = val
            b = True
    return b, v, e


def _valid_union(vv: ValidVal, t: CLS_Union, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    opts = get_args(t)
    for opt in opts:
        res = vv.extract(opt, val, cvt)
        if res[0]:
            return res
    return b, v, e


def _valid_queue(vv: ValidVal, t: CLS_Queue, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    loc_type = get_origin(t)
    if type(val) == loc_type:
        elements: Union[Tuple, List] = val  # type: ignore
        opts = get_args(t)
        arr = []
        if loc_type == tuple and len(opts) == len(elements):
            for opt, ele in zip(opts, elements):
                res = vv.extract(opt, ele, cvt)
                if res[0]:
                    arr.append(res[1])
                else:
                    arr = None

        elif loc_type == list:
            arr = []
            opt = opts[0]
            for ele in elements:
                res = vv.extract(opt, ele, cvt)
                if res[0]:
                    arr.append(res[1])
                else:
                    arr = None

        if arr is not None:
            b = True
            v = arr
            if loc_type == tuple:
                v = tuple(v)
    elif cvt and type(val) == str and vv.delimiter.is_some():
        # TODO: vv.delimiter is always "has some"
        arr = val.split(vv.delimiter.value)
        if loc_type == tuple:
            arr = tuple(arr)
        return vv.extract(t, arr, cvt)
    return b, v, e


def _valid_literal(
    vv: ValidVal, t: CLS_Literal, val: Any, cvt: bool
) -> VALID_RES:
    b = False
    v = None
    e = None
    candidates = get_args(t)
    if cvt:
        for can in candidates:
            cvt_res = vv.extract(type(can), val, cvt)
            if cvt_res[0]:
                v = cvt_res[1]
                b = True
    else:
        if val in candidates:
            v = val
            b = True
    return b, v, e


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
    }
)


def get_optional_candidates(t: Type) -> Optional[Tuple]:
    try:
        can = list(get_type_candidates(t))
        idx = can.index(CLS_None)
        can.pop(idx)
        return tuple(can)
    except Exception:
        pass
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
            pass
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


def argstyping_parse(t: Type) -> Dict[str, Type]:
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


def argstyping_parse_extra(t: Type):
    key_dict = get_type_hints(t, include_extras=True)
    extra: Dict[str, AnnoExtra] = {}
    for key, anno in key_dict.items():
        if get_origin(anno) is not Annotated:
            pass
        else:
            _, *anno_args = get_args(anno)
            if isinstance(anno_args[0], AnnoExtra):
                extra[key] = anno_args[0]
            else:
                pass
                # TODO: warning or error msg?
    return argstyping_parse(t), extra
