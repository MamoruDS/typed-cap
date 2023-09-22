import sys
from typing import (
    _GenericAlias,  # type: ignore
    _LiteralGenericAlias,  # type: ignore
    _TypedDictMeta,  # type: ignore
    _UnionGenericAlias,  # type: ignore
)

QueueTType = _GenericAlias
LiteralTType = _LiteralGenericAlias  # type: ignore
TypedDictTType = _TypedDictMeta  # type: ignore
UnionTType = _UnionGenericAlias  # type: ignore

if sys.version_info >= (3, 10):
    from types import NoneType
else:
    NoneType = type(None)
