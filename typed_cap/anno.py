from dataclasses import dataclass
from typing import (
    Annotated,
    Dict,
    Optional,
    Tuple,
    Type,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from .types import AliasCandidates
from .typing import argstyping_parse


T = TypeVar("T")


@dataclass
class AnnoExtra:
    about: Optional[str] = None
    alias: Optional[AliasCandidates] = None


def annotation_extra(
    alias: Optional[AliasCandidates] = None,
    about: Optional[str] = None,
) -> AnnoExtra:
    return AnnoExtra(about, alias)


def argstyping_parse_extra(
    t: Type[T],
) -> Tuple[Dict[str, Type[T]], Dict[str, AnnoExtra]]:
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
