import pytest
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    TypedDict,
    Union,
)


class _Cfg:
    cur: Optional[str]

    def __init__(self) -> None:
        self.cur = None


class DB(TypedDict):
    ...


class OB:
    ...


T = TypeVar("T", bound=Union[TypedDict, object])


class Profile(Generic[T]):
    def __init__(
        self, based: Type[T], val_getter: Callable[[T, str], Any]
    ) -> None:
        self.based = based
        self.val_getter = val_getter


p = Profile(OB, lambda x, k: x.__getattribute__(k))

PROFILES: Dict[str, Profile] = {
    "dict-based": Profile(DB, lambda x, k: x.__getitem__(k)),
    "object-based": Profile(OB, lambda x, k: x.__getattribute__(k)),
}


CFG = _Cfg()


def cmd(command: str) -> List[str]:
    return command.split(" ")


def get_profile(name: Optional[str]) -> Profile:
    if name is None:
        pytest.skip("profile name is None")
    else:
        p = PROFILES.get(name)
        if p is None:
            pytest.skip(f"can not get profile with name {name}")
        else:
            return p
