import typing
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypedDict,
    Union,
    get_args,
    get_origin,
)

from typing import (
    _GenericAlias,  # type: ignore
    _LiteralGenericAlias,  # type: ignore
    _UnionGenericAlias,  # type: ignore
)

CLS_Literal: Type = _LiteralGenericAlias
CLS_None: Type = type(None)
CLS_Union: Type = _UnionGenericAlias
CLS_Queue: Type = _GenericAlias


VALID_RES = Tuple[bool, Optional[Any], Optional[Exception]]


class TypeInf(TypedDict):
    t: Any
    c: Any
    v: Callable[[Type, Any, bool], VALID_RES]


def class_of(obj: Any) -> Optional[Any]:
    try:
        return obj.__class__
    except AttributeError:
        return None
    except Exception as e:
        raise e


def _valid_none(t: CLS_None, val: Any, _: bool) -> VALID_RES:
    b = False
    v = None
    if type(val) == t:
        v = val
        b = True
    return b, v, None


def _valid_int(t: Any, val: Any, cvt: bool) -> VALID_RES:
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


def _valid_float(_: Any, val: Any, cvt: bool) -> VALID_RES:
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


def _valid_str(_: Any, val: Any, cvt: bool) -> VALID_RES:
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


def _valid_union(t: CLS_Union, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    opts = get_args(t)
    for opt in opts:
        res = validation(opt, val, cvt)
        if res[0]:
            return res
    return b, v, e


def _valid_queue(t: CLS_Queue, val: Any, cvt: bool) -> VALID_RES:
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
                res = validation(opt, ele, cvt)
                if res[0]:
                    arr.append(res[1])
                else:
                    arr = None

        elif loc_type == list:
            arr = []
            opt = opts[0]
            for ele in elements:
                res = validation(opt, ele, cvt)
                if res[0]:
                    arr.append(res[1])
                else:
                    arr = None

        if arr != None:
            b = True
            v = arr
            if loc_type == tuple:
                v = tuple(v)
    return b, v, e


def _valid_literal(t: CLS_Literal, val: Any, cvt: bool) -> VALID_RES:
    b = False
    v = None
    e = None
    candidates = get_args(t)
    if cvt:
        for can in candidates:
            cvt_res = validation(type(can), val, cvt)
            if cvt_res[0]:
                v = cvt_res[1]
                b = True
    else:
        if val in candidates:
            v = val
            b = True
    return b, v, e


TYPE_VALIDATION: Dict[str, TypeInf] = {
    "int": {"t": int, "c": None, "v": _valid_int},
    "float": {"t": float, "c": None, "v": _valid_float},
    "str": {"t": str, "c": None, "v": _valid_str},
    "none": {
        "t": CLS_None,
        "c": CLS_None,
        "v": _valid_none,
    },
    "union": {
        "t": None,
        "c": CLS_Union,
        "v": _valid_union,
    },
    "queue": {
        "t": CLS_Queue,
        "c": CLS_Queue,
        "v": _valid_queue,
    },
    "literal": {
        "t": CLS_Literal,
        "c": CLS_Literal,
        "v": _valid_literal,
    },
}


def validation(t: Type, val: Any, cvt: bool):
    REG = TYPE_VALIDATION
    res: Optional[VALID_RES] = None
    if type(t) == str:
        if REG.get(t) != None:
            res = REG[t]["v"](REG[t]["t"], val, cvt)
    else:
        for _, t_inf in REG.items():
            if t == t_inf["t"] or class_of(t) == t_inf["c"]:
                res = t_inf["v"](t, val, cvt)
            else:
                continue
    if res == None:
        print(f"> t.__class__: {t.__class__}")
        print(f"> type(t): {type(t)}")
        raise Exception("not found")
    else:
        return res
