from typing import (
    Generic,
    TypeVar,
    Union,
)


class Unbound:
    ...


class UnboundException(Exception):
    ...


T = TypeVar("T")


class Option(Generic[T]):
    _v: Union[T, Unbound]

    def __init__(self, val: Union[T, Unbound] = Unbound()) -> None:
        self._v = val

    @property
    def _val(self) -> T:
        if self.is_none():
            raise UnboundException
        return self._v

    def is_none(self) -> bool:
        return isinstance(self._v, Unbound)

    def is_some(self) -> bool:
        return not self.is_none()

    def unwrap(self) -> T:
        try:
            return self._val
        except UnboundException:
            raise ValueError(
                "called `Option::unwrap()` on unbound option value"
            )

    def unwrap_or(self, default: T) -> T:
        try:
            return self._val
        except UnboundException:
            return default

    def __str__(self) -> str:
        try:
            return f"Option::Some({self._val})"
        except UnboundException:
            return f"Option::None"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def NONE(cls):
        return cls()

    @classmethod
    def Some(cls, val: T):
        return cls(val)
