from typing import Annotated, Optional

from typed_cap import Cap, annotation_extra as ae

from tests import CFG, cmd, get_profile


TEST_PROFILE = get_profile(CFG.cur)
B = TEST_PROFILE.based
G = TEST_PROFILE.val_getter


def test_anno_alias():
    class T(B):
        verbose: Annotated[Optional[bool], ae("v")]

    cap = Cap(T)
    res = cap.parse(cmd("-v"))
    assert res.count("verbose") == 1


def test_anno_about():
    cfg_about = "path to config file"

    class T(B):
        config: Annotated[Optional[bool], ae(None, cfg_about)]

    cap = Cap(T)
    assert cap._args["config"].alias == None
    assert cap._args["config"].about == cfg_about
