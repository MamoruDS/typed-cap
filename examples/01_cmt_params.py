from enum import Enum

from typed_cap import Cap


class CoinFlip(Enum):
    head = 0
    tail = 1


class Args:
    """
    docstring of T
    """

    # @alias=a
    all: bool = False
    """
    write counts for all files, not just directories
    """

    # @alias=c
    total: bool = False

    # @alias=d @hide_default
    max_depth: int = -1
    """
    print the total for a directory (or file, with --all) only if it is N or fewer levels below the command line argument
    """

    # @alias=h
    human_readable: bool | None
    """
    print sizes in human readable format (e.g., 1K 234M 2G)
    """

    # @alias=m @none_delimiter
    message: list[str] | None

    # @enum_on_value
    flip: CoinFlip


cap = Cap(Args)
parsed = cap.parse()

print(parsed.args.__dict__)
print(parsed.argv)
