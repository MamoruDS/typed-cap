import inspect
from enum import Enum, auto
from typing import (
    Dict,
    Iterable,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from .types import NoneType, TypedDictTType, UnionTType


T = TypeVar("T")

NoneType = type(None)


class BasedType(Enum):
    NONE = 0
    DICT = auto()
    OBJECT = auto()
    UNKNOWN = auto()


# FIXME: potential issues
def get_based(x) -> BasedType:
    if not inspect.isclass(x):
        return BasedType.NONE
    if type(x) is TypedDictTType:
        return BasedType.DICT
    b = x.__base__
    while True:
        if b is dict:
            return BasedType.DICT
        elif b is object:
            return BasedType.OBJECT
        elif b is None:
            break
        else:
            b = b.__base__
    return BasedType.UNKNOWN


def get_type_candidates(t: Type[T]) -> Tuple[Type[T]]:
    """
    `<T extends Union>(t: Union<T>): T | NoneType`

    Examples
    ----------
    >>> get_type_candidates(Optional[int])
    (<class 'int'>, <class 'NoneType'>)
    """
    if t.__class__ == UnionTType:
        can = get_args(t)
        return can  # type: ignore
    else:
        raise Exception()  # TODO:


def get_optional_candidates(t: Type) -> Optional[Tuple]:
    try:
        can = list(get_type_candidates(t))
        idx = can.index(NoneType)
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


def argstyping_parse(t: Type[T]) -> Dict[str, Type[T]]:
    based = get_based(t)
    if based is not BasedType.DICT and based is not BasedType.OBJECT:
        raise Exception(
            "t should be either `typing.TypedDict` or `object` for parsing"
        )  # TODO:
    key_dict: Dict[str, Type] = get_type_hints(t)
    typed: Dict[str, Type] = dict(((k, NoneType) for k in key_dict.keys()))

    def get_t(key: str, required: bool) -> Type:
        raw_t = key_dict[key]
        if required:
            return raw_t
        else:
            return Optional[raw_t]

    keys_req: Iterable[str]
    keys_opt: Iterable[str]
    if type(t) is TypedDictTType:
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
