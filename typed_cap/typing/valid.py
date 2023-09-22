from __future__ import annotations
from dataclasses import dataclass
import json
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    overload,
)
from ..utils.option import Option

T = TypeVar("T")


@dataclass
class ValidatorNotFound(Exception):
    type: Any

    def __str__(self) -> str:
        info = {
            "type": self.type,
            "type.__class__": self.type.__class__,
            "type(t)": type(self.type),
        }
        return "debug" + json.dumps(info, indent=4, default=str)


class ValidRes(Generic[T]):
    _valid: bool
    _data: Option[T]
    _error: Option[Exception]

    def __init__(self) -> None:
        self._valid = False
        self._data = Option.NONE()
        self._error = Option.NONE()

    def some(self, val: T):
        self._data = Option.Some(val)

    def none(self):
        self._data = Option.NONE()

    def error(self, err: Exception):
        self._error = Option.Some(err)

    def valid(self):
        self._valid = True

    def is_valid(self) -> bool:
        return self._valid

    @property
    def data(self) -> Option[T]:
        return self._data

    @property
    def value(self) -> T:
        return self._data.unwrap()

    def unwrap(self) -> Tuple[bool, T, Option[Exception]]:
        return self._valid, self.value, self._error

    def __str__(self) -> str:
        return json.dumps(
            {
                "valid": self._valid,
                "value": str(self._data),
                "error": str(self._error),
            },
            indent=4,
        )


ValidFunc = Callable[["ValidVal", Type[T], Any, bool], ValidRes[T]]


# TODO: change this:
class TypeInf(TypedDict):
    t: Any
    tt: Any
    c: Any
    v: ValidFunc


class ValidVal:
    attributes: Dict[str, Any]
    _validators: Dict[str, TypeInf]
    _delimiter: Option[Optional[str]]

    # temp only
    _temp_delimiter: Option[Optional[str]]

    def __init__(self, validators: Dict[str, TypeInf]) -> None:
        self.attributes = {}
        self._validators = validators
        self._delimiter = Option[Optional[str]].Some(",")
        self._temp_delimiter = Option.NONE()

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
    def delimiter(self) -> Option[Optional[str]]:
        if self._temp_delimiter.is_some():
            return self._temp_delimiter
        else:
            return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: Option[Optional[str]]) -> None:
        self._delimiter = delimiter

    @overload
    def extract(
        self,
        t: str,
        val: Any,
        cvt: bool,
        temp_delimiter: Option[Optional[str]] = Option.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes:
        ...

    @overload
    def extract(
        self,
        t: Type[T],
        val: Any,
        cvt: bool,
        temp_delimiter: Option[Optional[str]] = Option.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes[T]:
        ...

    def extract(
        self,
        t: Union[Type[T], str],
        val: Any,
        cvt: bool,
        temp_delimiter: Option[Optional[str]] = Option.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes[T]:
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
            self._temp_delimiter = Option.NONE()

        if res is None:
            raise ValidatorNotFound(t)
        else:
            return res
