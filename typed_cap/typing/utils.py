from typing import (
    Annotated,
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

from ..types import BasicArgOption, VALID_ALIAS_CANDIDATES
from ..utils import is_T_based
from .types import NoneType, TypedDictTType, UnionTType

# from .types import VALID_ALIAS_CANDIDATES

T = TypeVar("T")

NoneType = type(None)


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


def annotation_extra(
    alias: Optional[VALID_ALIAS_CANDIDATES] = None,
    about: Optional[str] = None,
) -> AnnoExtra:
    return AnnoExtra(about, alias)


def argstyping_parse(t: Type[T]) -> Dict[str, Type[T]]:
    if is_T_based(t) not in [dict, object]:
        raise Exception(
            "t should a `typing.TypedDict` or a `class` for parsing"
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
