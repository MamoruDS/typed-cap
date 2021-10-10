# typed-cap

Cap is a python **C**ommand-line **A**rgument **P**arser that provides **typing** support. Using Cap requires less code to generate a more robust parser.

As you know python is a weakly typed programming language, and even if there is a typing module, its functionality is very weak compared to other languages like Typescript or Rust. We know it's ridiculous and pointless to compare python to any of these languages at the typing level, but properly handling these types in your code can really improve readability and reduce typing errors. And that gave us the motivation to write this package.

## Usage

⚠️ `typed_cap` required `python>=3.8`

```
pip install typed_cap
```

### Quick Example

```python
from typed_cap import Cap, helpers
from typing import List, Optional, TypedDict


class T(TypedDict):
    verbose: bool
    message: List[str]
    size: Optional[float]


cap = Cap(T)
cap.default(
    {
        "verbose": False,
    }
)
cap.helper(
    {
        "verbose": {
            "alias": "v",
            "about": "verbose output",
        },
        "message": {"alias": "m", "about": "your messages"},
        "size": {
            "alias": "n",
            "about": "optional number",
        },
    }
)
helpers["arg_help"](cap, "help", None)
helpers["arg_version"](cap, "version", "V")
args = cap.parse()

print(args.args)
print(args.val)
```

```shell
python demo.py
# DEMO: option 'message':list[str] is required but it is missing

python demo.py -vv -m="msg1" --message "msg2" -m "msg3" -n=0.1 -n=10 ~/.config
# ['/home/local/.config']
# {'verbose': True, 'message': ['msg1', 'msg2', 'msg3'], 'size': 10.0}
```

## Features

### Flags

flags are `bool` fields defined in input type

```python
class T(TypedDict):
    silent: bool
    yes: Optional[bool]
...
args = cap.parse()
yes = args.val['yes']
```

-   alias for flags and options
    adds short-version for convenient
    ```python
    cap.helper(
        { "ipv4": "4" }
    )
    ```
    `-4` equals to `--ipv4`
-   supports combining alias
    `-zxvf` equals to `-z -x -v -f`
-   supports multiple occurrences
    `-v -v` or `-vv`
    how to get occurrences of the argument
    ```python
    class T(TypedDict):
        ...
        verbose: bool
    ...
    args.count('verbose') # -> int
    ```

### Option Argument

named options which are take values

```python
class T(TypedDict):
    integer: int
    floating: float
    strings: List[str]
```

-   supports alias
    similar to flags
    ```python
    cap.helper(
        { "integer": "i" },
        { "floating": "f" },
        { "strings": "s" },
    )
    ```
    `-i 1` `-i=1` `--integer 1` `--integer=1`
-   supports multiple values
    `-m="msg1" --message "msg2" -m "msg3"`
    will get
    ```python
    { 'message': ['msg1', 'msg2', 'msg3'] }
    ```

### Typing

Cap takes an arbitrary `TypedDict` class (`T`) as input, processes the resulting arguments by the registered parser in the parse method, and finally returns a `dict` of type `T` to the user. The nice thing about this is that all the parsed arguments you get will be typing robust and can be supported by auto-completion, type checking and other features in modern editors.

<p align="center">
    <img width="550px" src="https://github.com/MamoruDS/typed-cap/raw/main/screenshots/clip00.gif">
</p>

The preset parser can help you perform basic parse functions, and the supported types include `str`, `bool`, `int` and `float`. In addition, Cap will handle `Optional` and `List` for these types (`list` in python 3.9). cap is still in its early stages, and support for `Tuple` and others will be refined in subsequent updates.

Want more type support? Use `set_parser` to make Cap support your custom types.

```python
Cap.set_parser(
        self, type_name: str, parser: Parser, allow_list: bool
    ) -> Cap
```

### Helpers

Cap proviedes some useful argument helpers

-   `help`
    generate help documents that automatically adapt to the terminal width
    usage:
    ```python
    helpers["arg_help"](
        cap: Cap,
        name: str,
        alias: Optional[VALID_ALIAS_CANDIDATES],
    ) -> None
    ```
    example:
    ```python
    from typed_cap import Cap, helpers
    ... # code from quick example
    cap.about("some descriptions") # optional
    helpers["arg_help"](cap, "help", None)
    args = cap.parse()
    ```
    ```shell
    python demo.py --help
    # some descriptions
    #
    # OPTIONS:
    #     -v,--verbose    verbose output
    #     -m,--message    your messages
    #     -n,--size       optional number
    #        --help       display the help text
    ```
-   `version`
    usage:

    ```python
    helpers["arg_help"](
        cap: Cap,
        name: str,
        alias: Optional[VALID_ALIAS_CANDIDATES],
    ) -> None
    ```

    example:

    ```python
    from typed_cap import Cap, helpers
    ... # code from quick example
    cap.name("your-demo") # optional
    cap.version("0.1.0")
    helpers["arg_version"](cap, "version", "V")
    args = cap.parse()
    ```

    ```shell
    python demo.py -V # or
    python demo.py --version
    # your-demo 0.1.0
    ```

### Others

using `Cap.raw_exception` to expose exceptions

## Examples

### Baisc Example

```python
from typed_cap import Cap
from typing import Optional, TypedDict


class T(TypedDict):
    all: Optional[bool]
    total: Optional[bool]
    max_depth: Optional[int]
    human_readable: Optional[bool]


cap = Cap(T)
args = cap.parse()

print(args.args)
print(args.val)
```

```shell
python demo.py --all --total /opt
# ['/opt']
# {'all': True, 'total': True, 'max_depth': None, 'human_readable': None}
```

### Advance Example

```python
from typed_cap import Cap
from typing import Optional, TypedDict


class T(TypedDict):
    all: bool
    total: bool
    max_depth: inta
    human_readable: Optional[bool]


cap = Cap(T)
cap.default(
    {
        "all": False,
        "total": False,
        "max_depth": -1,
    }
)
cap.helper(
    {
        "all": {
            "alias": "a",
            "about": "write counts for all files, not just directories",
        },
        "total": {"alias": "c", "about": "produce a grand total"},
        "max_depth": {
            "alias": "d",
            "about": "print the total for a directory (or file, with --all) only if it is N or fewer levels below the command line argument;",
        },
        "human_readable": {
            "alias": "h",
            "about": "print sizes in human readable format (e.g., 1K 234M 2G)",
        },
    }
)
args = cap.parse()

print(args.args)
print(args.val)
```

```shell
python demo.py -ah --max-depth=1 /tmp
# ['/tmp']
# {'all': True, 'human_readable': True, 'max_depth': 1, 'total': False}
```
