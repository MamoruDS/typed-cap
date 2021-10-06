class ArgsParserKeyError(Exception):
    key: str

    def __init__(self, key: str, *args: object) -> None:
        self.key = key
        super().__init__(f"unknown option '{key}'")
