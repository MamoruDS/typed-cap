from __future__ import annotations
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
from ..utils import RO

T = TypeVar("T")


class ValidRes(Generic[T]):
    _valid: bool
    _data: RO[T]
    _error: RO[Exception]

    def __init__(self) -> None:
        self._valid = False
        self._data = RO.NONE()
        self._error = RO.NONE()

    def some(self, val: T):
        self._data = RO.Some(val)

    def none(self):
        self._data = RO.NONE()

    def error(self, err: Exception):
        self._error = RO.Some(err)

    def valid(self):
        self._valid = True

    def is_valid(self) -> bool:
        return self._valid

    @property
    def data(self) -> RO[T]:
        return self._data

    @property
    def value(self) -> Optional[T]:
        return self._data.value

    def unwrap(self) -> Tuple[bool, Optional[T], RO[Exception]]:
        return self._valid, self._data.value, self._error

    def __str__(self) -> str:
        return json.dumps(
            {
                "valid": self._valid,
                "value": self._data.value,
                "error": self._error.value,
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
    _delimiter: RO[str]

    # temp only
    _temp_delimiter: RO[str]

    def __init__(self, validators: Dict[str, TypeInf]) -> None:
        self.attributes = {}
        self._validators = validators
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
    def validators(self) -> Dict[str, TypeInf]:
        return self._validators

    @property
    def delimiter(self) -> RO[str]:
        if self._temp_delimiter.is_some():
            return self._temp_delimiter
        else:
            return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: RO[str]) -> None:
        self._delimiter = delimiter

    @overload
    def extract(
        self,
        t: str,
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes:
        ...

    @overload
    def extract(
        self,
        t: Type[T],
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ) -> ValidRes[T]:
        ...

    def extract(
        self,
        t: Union[Type[T], str],
        val: Any,
        cvt: bool,
        temp_delimiter: RO[str] = RO.NONE(),
        leave_scope: bool = False,
    ):
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
            self._temp_delimiter = RO.NONE()

        if res is None:
            # TODO:
            print(f"\t> t.__class__: {t.__class__}")
            print(f"\t> type(t): {type(t)}")
            print(f"\t> t: {t}")
            raise Exception("not found")
        else:
            return res
