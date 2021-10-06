from typed_cap.utils import panic
from typing import Any, Callable, Dict, List, TypedDict


Parser = Callable[[str, bool, str], List[Any]]


class ParserInfo(TypedDict):
    parser: Parser
    allow_list: bool


ParserRegister = Dict[str, ParserInfo]


def _preset_parser_str(text: str, is_list: bool, delimiter: str) -> List[str]:
    if is_list:
        return text.split(delimiter)
    else:
        return [text]


def _preset_parser_bool(
    text: str, is_list: bool, delimiter: str
) -> List[bool]:
    pre = _preset_parser_str(text, is_list, delimiter)
    val: List[bool] = []
    for e in pre:
        if e in ["0", "false"]:
            val.append(False)
        elif e in ["1", "true"]:
            val.append(True)
    return val


def _preset_parser_int(text: str, is_list: bool, delimiter: str) -> List[int]:
    pre = _preset_parser_str(text, is_list, delimiter)
    val: List[int] = []
    for e in pre:
        val.append(int(e))
    return val


def _preset_parser_float(
    text: str, is_list: bool, delimiter: str
) -> List[float]:
    pre = _preset_parser_str(text, is_list, delimiter)
    val: List[float] = []
    for e in pre:
        val.append(float(e))
    return val


PRESET: ParserRegister = {
    "str": {"parser": _preset_parser_str, "allow_list": True},
    "bool": {"parser": _preset_parser_bool, "allow_list": True},
    "int": {"parser": _preset_parser_int, "allow_list": True},
    "float": {"parser": _preset_parser_float, "allow_list": True},
}
