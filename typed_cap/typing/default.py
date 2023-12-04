import sys
from enum import EnumMeta, Enum
from types import GenericAlias
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from .valid import ValidVal, ValidRes, Unit
from .types import LiteralTType, NoneType, QueueTType, UnionTType


def _valid_none(_vv: ValidVal, t: NoneType, val: Any, _cvt: bool):
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


def _valid_union(vv: ValidVal, t: UnionTType, val: Any, cvt: bool):
    v = ValidRes[UnionTType]()
    opts = get_args(t)
    for opt in opts:
        v_got = vv.extract(opt, val, cvt)
        if v_got.is_valid():
            return v_got
    return v


def _valid_queue(vv: ValidVal, t: QueueTType, val: Any, cvt: bool):
    v = ValidRes[QueueTType]()
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
        arr = val.split(vv.delimiter.unwrap())
        if loc_type == tuple:
            arr = tuple(arr)
        return vv.extract(t, arr, cvt)
    return v


def _valid_literal(vv: ValidVal, t: LiteralTType, val: Any, cvt: bool):
    v = ValidRes[LiteralTType]()
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
    v = ValidRes[Enum]()
    try:
        # eval member on value or name
        on_val = vv.attributes.get("enum_on_value", False)
        for meb in list(t):  # type: ignore
            meb: Enum
            if on_val:
                v_got = vv.extract(type(meb.value), val, cvt=True)
                if v_got.value == meb.value:
                    v.some(meb)
                    v.valid()
            else:
                v_got = vv.extract(str, val, cvt=True)
                if v_got.valid and v_got.value.lower() == meb.name.lower():
                    v.some(meb)
                    v.valid()
    except Exception as err:
        v.error(err)
    return v


PREDEFINED_UNITS: Dict[str, Unit] = {
    "bool": Unit(
        exact=bool,
        type_of=None,
        class_of=None,
        valid_fn=_valid_bool,
    ),
    "int": Unit(
        exact=int,
        type_of=None,
        class_of=None,
        valid_fn=_valid_int,
    ),
    "float": Unit(
        exact=float,
        type_of=None,
        class_of=None,
        valid_fn=_valid_float,
    ),
    "str": Unit(
        exact=str,
        type_of=None,
        class_of=None,
        valid_fn=_valid_str,
    ),
    "none": Unit(
        exact=NoneType,
        type_of=None,
        class_of=NoneType,
        valid_fn=_valid_none,
    ),
    "union": Unit(
        exact=None,
        type_of=None,
        class_of=UnionTType,
        valid_fn=_valid_union,
    ),
    "queue": Unit(
        exact=QueueTType,
        type_of=GenericAlias,
        class_of=QueueTType,
        valid_fn=_valid_queue,
    ),
    "literal": Unit(
        exact=LiteralTType,
        type_of=None,
        class_of=LiteralTType,
        valid_fn=_valid_literal,
    ),
    "enum": Unit(
        exact=None,
        type_of=EnumMeta,
        class_of=EnumMeta,
        valid_fn=_valid_enum,
    ),
}

if sys.version_info >= (3, 10):
    from types import UnionType

    def _valid_uniontype(vv: ValidVal, t: UnionType, val: Any, cvt: bool):
        v = ValidRes[UnionType]()
        opts = get_args(t)
        for opt in opts:
            v_got = vv.extract(opt, val, cvt)
            if v_got.is_valid():
                return v_got
        return v

    PREDEFINED_UNITS.update(
        {
            "uniontype": Unit(
                exact=None,
                type_of=None,
                class_of=UnionType,
                valid_fn=_valid_uniontype,
            ),
        }
    )

VALIDATOR = ValidVal(PREDEFINED_UNITS)
