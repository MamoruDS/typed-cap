# typed-cap

[![pypi](https://img.shields.io/pypi/v/typed-cap?style=flat-square)](https://pypi.org/project/typed-cap/)
[![style](https://img.shields.io/badge/code%20style-black-black?style=flat-square)](https://github.com/psf/black)

Cap is a python **C**ommand-line **A**rgument **P**arser that provides **typing** support. Using Cap requires less code to generate a more easy to use parser.

## Usage

⚠️ `typed_cap` required `python>=3.9`

```
pip install typed_cap
```

### Quick Example

```python
from typed_cap import Cap


class Args:
    """description here"""

    # @alias=c
    config: str | None
    """file path to config file"""

    # @alias=d
    depth: int
    """depth of search"""

    dry_run: bool = True
    """run without making any changes"""


cap = Cap(Args)
parsed = cap.parse()

print(parsed.args.__dict__)
print(parsed.argv)
```

```shell
python demo.py
# Cap.parse: option depth:int is required but it is missing
#         ArgsParserMissingArgument

python demo.py --help
# description here
#
# OPTIONS:
#     -c,--config     file path to config file
#     -d,--depth      depth of search
#        --dry_run    run without making any changes (default: True)
#     -h,--help       display the help text

python demo.py -d 5 hello typed cap
# {'depth': 5, 'config': None, 'dry_run': True}
# ['hello', 'typed', 'cap']
```
