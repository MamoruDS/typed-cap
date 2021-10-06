from typing import Literal


class ArgsParserKeyError(Exception):
    key: str
    key_type: str

    def __init__(
        self,
        key: str,
        key_type: Literal["option", "flag"],
        *args: object,
    ) -> None:
        self.key = key
        self.key_type = key_type
        super().__init__(f"unknown {self.key_type} '{self.key}'", *args)


class ArgsParserUnexpectedValue(Exception):
    key: str
    value: str

    def __init__(self, key: str, value: str, *args: object) -> None:
        self.key = key
        self.value = value
        super().__init__(*args)


class ArgsParserMissingValue(Exception):
    key: str

    def __init__(self, key: str, *args: object) -> None:
        self.key = key
        super().__init__(*args)
