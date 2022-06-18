import ast
import inspect
import re
import sys
from typing import Dict, Optional, TypedDict, Union


class _ParsedAnno:
    lineno: int
    doc: Optional[str] = None
    comment: Optional[str] = None

    def __init__(self, lineno: int) -> None:
        self.lineno = lineno


class AnnoDetail(TypedDict):
    doc: Optional[str]
    comment: Optional[str]


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
    parsed: Union[ast.Module, ast.ClassDef],
    named_doc: Dict[str, _ParsedAnno] = {},
) -> None:
    last = None
    for i in parsed.body:
        try:
            if isinstance(i, ast.Expr):
                if isinstance(last, ast.AnnAssign):
                    target: ast.Name = last.target  # type: ignore
                    name = target.id
                    if isinstance(i.value, ast.Constant):
                        docs: str = i.value.value
                        named_doc[name].doc = docs
            elif isinstance(i, ast.ClassDef):
                get_doc_from_ast(i, named_doc)
            elif isinstance(i, ast.AnnAssign):
                target: ast.Name = i.target  # type: ignore
                name = target.id
                named_doc[name] = _ParsedAnno(i.lineno)
            else:
                continue
        except TypeError:
            ...
        last = i


def get_annotations(
    c: type, stop_at: Optional[type] = None
) -> Dict[str, AnnoDetail]:
    _stop_before = [dict, object]
    named_anno: Dict[str, AnnoDetail] = {}

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

        local_anno: Dict[str, _ParsedAnno] = {}
        get_doc_from_ast(parsed, local_anno)

        for name, anno in local_anno.items():
            if named_anno.get(name) is None:
                named_anno[name] = {
                    "doc": None,
                    "comment": None,
                }
            if anno.doc is not None:
                named_anno[name]["doc"] = anno.doc
            try:
                comment = src.split("\n")[anno.lineno - 2].lstrip()
                if comment.startswith("#"):
                    named_anno[name]["comment"] = comment
            except IndexError:
                ...

    return named_anno


def get_docs_from_annotations(
    annotations: Dict[str, AnnoDetail]
) -> Dict[str, str]:
    named_docs: Dict[str, str] = {}
    for name, anno in annotations.items():
        if anno["doc"] is not None:
            doc = anno["doc"]
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
            named_docs[name] = doc
    return named_docs


def get_all_comments_parameters(
    annotations: Dict[str, AnnoDetail]
) -> Dict[str, Dict[str, Optional[str]]]:
    named_params: Dict[str, Dict[str, Optional[str]]] = {}
    reg = re.compile(r"@(?P<key>\w+)(=(?P<val>((\\@)|([^@]))+))?", re.M)

    for name, anno in annotations.items():
        comment = anno["comment"]
        params: Dict[str, Optional[str]] = {}

        if comment is not None:
            comment = comment[1:].lstrip()

            for match in reg.finditer(comment):
                key = match.group("key")
                val = match.group("val")

                if val is not None:
                    val = val.rstrip()
                params[key] = val

        named_params[name] = params
    return named_params
