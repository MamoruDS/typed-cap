import inspect
import re
import shutil
from sys import stderr
from typing import (
    Any,
    Generic,
    List,
    NoReturn,
    Optional,
    Type,
    TypeVar,
    Union,
    _TypedDictMeta,  # type: ignore
)


T = TypeVar("T")
S = TypeVar("S", bound=Union[str, int, float, bool])


class RO(Generic[T]):
    """RealOptional"""

    value: Optional[T]
    _none: bool

    def __init__(self, is_none: bool, value: Optional[T] = None) -> None:
        self._none = is_none
        self.value = value

    def is_some(self) -> bool:
        return not self._none

    def is_none(self) -> bool:
        return self._none

    @classmethod
    def NONE(cls):
        return cls(is_none=True)

    @classmethod
    def Some(cls, value: Optional[T]):
        return cls(is_none=False, value=value)


def flatten(a: List[List]) -> List:
    f = []
    for c in a:
        f = [*f, *c]
    return f


def get_terminal_width(max_width: int) -> int:
    s = shutil.get_terminal_size((999, 999))
    w = s.columns
    return min(w, max_width)


# FIXME: potential issues
def is_T_based(x) -> Union[Type[dict], Type[object], None]:
    if not inspect.isclass(x):
        return None
    if type(x) is _TypedDictMeta:
        return dict
    b = x.__base__
    while True:
        if b is dict:
            return dict
        elif b is object:
            return object
        elif b is None:
            break
        else:
            b = b.__base__
    return None


def join(a: List[str], j: str) -> str:
    return j.join(a)


def panic(msg: str, exit_code: int = 1) -> NoReturn:
    stderr.write(msg + "\n")
    exit(exit_code)


def splice(
    array: List[Any], start: int, delete_count: int, *items: Any
) -> List[Any]:
    return [*array[:start], *items, *array[start + delete_count :]]


def split_by_length(
    text: str,
    length: int,
    add_hyphen: bool = True,
    remove_leading_space: bool = True,
) -> List[str]:
    text_lns = text.split("\n")
    if len(text_lns) != 1:
        lns = []
        for ln in text_lns:
            lns = [
                *lns,
                *split_by_length(
                    ln,
                    length,
                    add_hyphen,
                    remove_leading_space,
                ),
            ]
        return lns
    else:
        idx = range(0, len(text), length)
        if not add_hyphen:
            return [text[i : i + length] for i in idx]
        else:
            lns = []
            i = 0
            while i < len(text):
                sub = text[i : i + length]
                if len(sub) < length:
                    lns.append(sub)
                    break
                else:
                    # FIXME: potential issue
                    tail = text[i + length - 2 : i + length + 1]
                    if (
                        remove_leading_space
                        and len(tail) == 3
                        and tail[2] == " "
                    ):
                        text = join(splice(list(text), i + length, 1), "")
                    else:
                        m = re.match(r"(?P<S>\s{1})?\w{2,}", tail)
                        if m is not None:
                            if m.group("S") is not None:
                                text = join(
                                    splice(list(text), i + length - 2, 0, " "),
                                    "",
                                )
                            else:
                                text = join(
                                    splice(list(text), i + length - 1, 0, "-"),
                                    "",
                                )
                    lns.append(text[i : i + length])
                    i += length
            return lns


def str_eq(
    lhs: Optional[str], rhs: Optional[str], case_sensitive: bool
) -> bool:
    if lhs is None or rhs is None:
        return False
    elif case_sensitive:
        return lhs == rhs
    else:
        return lhs.lower() == rhs.lower()


def simple_eq(lhs: Optional[S], rhs: Optional[S]) -> bool:
    # prevent typing issue
    return lhs == rhs


D = TypeVar("D")


def unwrap_or(d: Optional[D], alt: D) -> D:
    if d is None:
        return alt
    else:
        return d
