from typing import Dict, NoReturn, Optional, TypedDict, Union, get_args

from .types import (
    AliasCandidates,
    ArgOption,
    CmtParamInvalidFlagValue,
    CmtParamInvalidValue,
    CmtParamMissingValue,
)
from .utils.option import Option

_CmtParamVal = Optional[str]


class ValidParams(TypedDict, total=False):
    alias: AliasCandidates
    show_default: bool
    delimiter: Option[Optional[str]]
    enum_on_value: bool


NamedValidParams = Dict[str, ValidParams]


def _parse_flag_generic(
    name: str,
    flag_name: str,
    val: _CmtParamVal,
    flag_val: bool,
    allow_val: bool,
) -> Union[bool, NoReturn]:
    if val is None:
        return flag_val
    elif allow_val:
        if val in ["False", "True", "false", "true"]:
            if val.lower() == "true":
                return flag_val
            else:
                return not flag_val
        raise CmtParamInvalidFlagValue(name, flag_name, val)
    else:
        raise CmtParamInvalidValue(name, flag_name, val, "no value required")


def _parse_alias(
    name: str, val: _CmtParamVal
) -> Union[AliasCandidates, NoReturn]:
    if val is None:
        raise CmtParamMissingValue(name, "alias")

    if val in get_args(AliasCandidates):
        return val  # type: ignore
    else:
        raise CmtParamInvalidValue(name, "alias", val)


def _parse_show_default(
    name: str, val: _CmtParamVal, flag_val: bool
) -> Union[bool, NoReturn]:
    return _parse_flag_generic(
        name,
        "show_result",
        val,
        flag_val,
        allow_val=True,
    )


def _parse_hide_default(
    name: str, val: _CmtParamVal, flag_val: bool
) -> Union[bool, NoReturn]:
    return _parse_flag_generic(
        name,
        "hide_result",
        val,
        flag_val,
        allow_val=False,
    )


def _parse_delimiter(
    name: str, val: _CmtParamVal
) -> Union[Option[Optional[str]], NoReturn]:
    if val is None:
        raise CmtParamMissingValue(name, "delimiter")
    return Option[Optional[str]].Some(val)


def _parse_none_delimiter(
    name: str, val: _CmtParamVal
) -> Union[Option[Optional[str]], NoReturn]:
    _parse_flag_generic(
        name,
        "none_delimiter",
        val,
        flag_val=True,
        allow_val=False,
    )
    return Option[Optional[str]].Some("None")


def _parse_enum_on_value(
    name: str, val: _CmtParamVal
) -> Union[bool, NoReturn]:
    _parse_flag_generic(
        name,
        "enum_on_value",
        val,
        flag_val=True,
        allow_val=False,
    )
    return True


def parse_anno_cmt_params(
    args: Dict[str, ArgOption]
) -> Union[NamedValidParams, NoReturn]:
    named_param: NamedValidParams = {}
    for name, opt in args.items():
        params: ValidParams = {}
        for key, val in opt.cmt_params.items():
            if False:
                ...
            # @alias
            elif key == "alias":
                params["alias"] = _parse_alias(name, val)

            # @hide_default
            elif key == "hide_default":
                params["show_default"] = _parse_hide_default(
                    name,
                    val,
                    flag_val=False,
                )

            # @show_default
            elif key == "show_default":
                params["show_default"] = _parse_show_default(
                    name,
                    val,
                    flag_val=True,
                )

            # @delimiter
            elif key == "delimiter":
                params["delimiter"] = _parse_delimiter(name, val)

            # @none_delimiter
            elif key == "none_delimiter":
                params["delimiter"] = _parse_none_delimiter(
                    name,
                    val,
                )

            # @enum_on_value
            elif key == "enum_on_value":
                params["enum_on_value"] = _parse_enum_on_value(
                    name,
                    val,
                )

        named_param[name] = params
    return named_param
