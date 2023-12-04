from PIL import Image
from typed_cap import Cap
from typed_cap.typing import ValidUnit, ValidRes, ValidVal


class Args:
    image: Image.Image
    """path to image wanted to be loaded"""


def valid_image(vv, t, val, cvt):
    v = ValidRes[Image.Image]()
    if cvt:
        try:
            v.some(Image.open(val))
            v.valid()
        except Exception as err:
            v.error(err)
    else:
        if isinstance(val, Image.Image):
            v.some(val)
            v.valid()
    return v


cap = Cap(
    Args,
    extra_validator_units={
        "image": ValidUnit(
            exact=Image.Image,
            type_of=None,
            class_of=None,
            valid_fn=valid_image,
        ),
    },
)
parsed = cap.parse()
# python 02_custom_unit.py --image demo.jpg

print(parsed.args.image)
