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

NoneType = type(None)
