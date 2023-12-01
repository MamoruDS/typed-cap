from __future__ import annotations
from enum import IntEnum
from typing import Protocol, Union


class _ToStr(Protocol):
    def __str__(self) -> str:
        ...


class ColorPlane(IntEnum):
    Fg = 0
    Bg = 1


class BasicColors(IntEnum):
    Black = 0
    Red = 1
    Green = 2
    Yellow = 3
    Blue = 4
    Magenta = 5
    Cyan = 6
    White = 7
    BrightBlack = 8
    BrightRed = 9
    BrightGreen = 10
    BrightYellow = 11
    BrightBlue = 12
    BrightMagenta = 13
    BrightCyan = 14
    BrightWhite = 15


class Styles(IntEnum):
    Bold = 1
    Dim = 2
    Underline = 4
    Blink = 5


_ColorVal = Union[int, tuple[int, int, int], str]


def _get_text(t: Union[_Color, str]) -> str:
    if isinstance(t, _Color):
        t = t.text
    return t


def create_ansi_escape_code(param: str) -> str:
    return f"\x1b[{param}m"


def encode_ansi_color(c: _ColorVal, ct: ColorPlane) -> str:
    if isinstance(c, int) and 0 <= c < 16:
        if 8 <= c < 16:
            offset = 90 if ct is ColorPlane.Fg else 100
            c -= 8
        else:
            offset = 30 if ct is ColorPlane.Fg else 40
        return str(offset + c)
    elif isinstance(c, int) and c >= 16 and c < 256:
        if ct is ColorPlane.Fg:
            return f"38;5;{c}"
        else:
            return f"48;5;{c}"
    elif isinstance(c, str):
        if c.startswith("#"):
            c = c[1:]
        assert len(c) == 6
        rgb = tuple(int(c[i : i + 2], 16) for i in range(0, 6, 2))
        assert len(rgb) == 3
        return encode_ansi_color(rgb, ct)
    elif isinstance(c, tuple):
        assert len(c) == 3
        if ct is ColorPlane.Fg:
            return f"38;2;{c[0]};{c[1]};{c[2]}"
        else:
            return f"48;2;{c[0]};{c[1]};{c[2]}"
    else:
        raise ValueError


def get_ansi_style_code(s: Styles):
    if s is Styles.Bold:
        return "1"
    elif s is Styles.Dim:
        return "2"
    elif s is Styles.Underline:
        return "4"
    elif s is Styles.Blink:
        return "5"
    else:
        raise ValueError


class _Color:
    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_colorable(cls, target: Colorable) -> _Color:
        if isinstance(target, cls):
            return target
        elif hasattr(target, "__str__"):
            return cls(str(target))
        elif isinstance(target, str):
            return cls(target)
        else:
            raise ValueError

    @staticmethod
    def _reset(t: Union[_Color, str]) -> str:
        return _get_text(t) + "\x1b[0m"

    def _stylize(self, style: Styles) -> None:
        self.text = (
            create_ansi_escape_code(get_ansi_style_code(style)) + self.text
        )

    def _colorize(self, color: _ColorVal, color_type: ColorPlane) -> None:
        self.text = (
            create_ansi_escape_code(encode_ansi_color(color, color_type))
            + self.text
        )

    def fg(self, color: _ColorVal) -> _Color:
        self._colorize(color, ColorPlane.Fg)
        return self

    def bg(self, color: _ColorVal) -> _Color:
        self._colorize(color, ColorPlane.Bg)
        return self

    def bold(self) -> _Color:
        self._stylize(Styles.Bold)
        return self

    def dim(self) -> _Color:
        self._stylize(Styles.Dim)
        return self

    def underline(self) -> _Color:
        self._stylize(Styles.Underline)
        return self

    def blink(self) -> _Color:
        self._stylize(Styles.Blink)
        return self

    def __str__(self) -> str:
        return self._reset(self.text)


Colorable = Union[_Color, _ToStr, str]


def fg(target: Colorable, color: _ColorVal) -> _Color:
    target = _Color.from_colorable(target)
    return target.fg(color)


def bg(target: Colorable, color: _ColorVal) -> _Color:
    target = _Color.from_colorable(target)
    return target.bg(color)


def bold(target: Colorable) -> _Color:
    target = _Color.from_colorable(target)
    return target.bold()


def dim(target: Colorable) -> _Color:
    target = _Color.from_colorable(target)
    return target.dim()


def underline(target: Colorable) -> _Color:
    target = _Color.from_colorable(target)
    return target.underline()


def blink(target: Colorable) -> _Color:
    target = _Color.from_colorable(target)
    return target.blink()
