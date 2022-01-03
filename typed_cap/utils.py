import re
import shutil
from sys import stderr
from typing import (
    Any,
    List,
    NoReturn,
    Optional,
    TypeVar,
    Union,
)


def flatten(a: List[List]) -> List:
    f = []
    for c in a:
        f = [*f, *c]
    return f


def get_terminal_width(max_width: int) -> int:
    s = shutil.get_terminal_size((999, 999))
    w = s.columns
    return min(w, max_width)


def join(a: List[str], j: str) -> str:
    return j.join(a)


def panic(msg: str, exit_code: int = 1) -> NoReturn:
    stderr.write(msg + "\n")
    exit(exit_code)


def remove_comments(code: Union[str, List[str]]) -> List[str]:
    if isinstance(code, list):
        code = "\n".join(code)
    code = re.sub(r"#[^$|^\n]+", "", code, flags=re.MULTILINE)
    code = re.sub(r"\"\"\"[^(\"\"\")]+\"\"\"", "", code, flags=re.MULTILINE)
    if isinstance(code, str):
        lines = code.split("\n")
    else:
        lines = code
    res = []
    for l in lines:
        if l.lstrip() == "":
            continue
        res.append(l)
    return res


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
                if remove_leading_space and len(tail) == 3 and tail[2] == " ":
                    text = join(splice(list(text), i + length, 1), "")
                else:
                    m = re.match(r"(?P<S>\s{1})?\w{2,}", tail)
                    if m != None:
                        if m.group("S") != None:
                            text = join(
                                splice(list(text), i + length - 2, 0, " "), ""
                            )
                        else:
                            text = join(
                                splice(list(text), i + length - 1, 0, "-"), ""
                            )
                lns.append(text[i : i + length])
                i += length
        return lns


def _to_color(text, code: str) -> str:
    return f"{code}{text}\x1b[0m"


def to_red(text) -> str:
    return _to_color(text, "\x1b[31m")


def to_green(text) -> str:
    return _to_color(text, "\x1b[32m")


def to_yellow(text) -> str:
    return _to_color(text, "\x1b[33m")


def to_blue(text) -> str:
    return _to_color(text, "\x1b[34m")


D = TypeVar("D")


def unwrap_or(d: Optional[D], alt: D) -> D:
    if d == None:
        return alt
    else:
        return d
