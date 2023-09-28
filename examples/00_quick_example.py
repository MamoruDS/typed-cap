from typed_cap import Cap


class Args:
    """description here"""

    config: str | None
    """file path to config file"""

    depth: int
    """depth of search"""

    dry_run: bool = True
    """run without making any changes"""


cap = Cap(Args)
parsed = cap.parse()

print(parsed.args.__dict__)
print(parsed.argv)
