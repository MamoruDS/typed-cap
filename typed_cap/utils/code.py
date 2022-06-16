import ast
import inspect
import re
import sys
from typing import Dict, Optional


def reset_indent(code: str) -> str:
    lines = code.split("\n")
    zero = sys.maxsize
    for ln in lines:
        striped = ln.lstrip()
        if len(striped) != 0:
            left = len(ln) - len(striped)
            if left < zero:
                zero = left
    code = "\n".join([ln[zero:] for ln in lines])
    return code


def get_doc_from_ast(
    parsed: ast.Module, named_doc: Dict[str, str] = {}
) -> None:
    last = None
    for i in parsed.body:
        try:
            if isinstance(i, ast.Expr):
                if isinstance(last, ast.AnnAssign):
                    name = last.target.id
                    docs = i.value.value
                    named_doc[name] = docs
            elif isinstance(i, ast.ClassDef):
                get_doc_from_ast(i, named_doc)

        except TypeError:
            ...
        last = i


def get_named_doc(c: type, stop_at: Optional[type] = None) -> Dict[str, str]:
    _stop_before = [dict, object]
    named_doc: Dict[str, str] = {}

    bases = []
    try:
        for c in inspect.getmro(c):
            if stop_at is None and c in _stop_before:
                break
            bases.insert(0, c)
            if c is stop_at:
                break
    except TypeError:
        ...

    for c in bases:
        src = inspect.getsource(c)
        src = reset_indent(src)
        parsed = ast.parse(src)
        get_doc_from_ast(parsed, named_doc)

    for name, doc in named_doc.items():
        doc = re.sub(
            r"(\A\s+)|(^[\t| ]{0,})|([\t| ]{0,}$)",
            "",
            doc,
            flags=re.M,
        )
        doc = re.sub(
            r"(?<!^)\n([\w|-])",
            r" \g<1>",
            doc,
            flags=re.M,
        )
        doc = re.sub(r"\n$", "", doc, flags=re.M)
        doc = re.sub(
            r"\s(-{3,})\s",
            r"\n\g<1>\n",
            doc,
            flags=re.M,
        )
        named_doc[name] = doc
    return named_doc
