from tests import CFG, cmd, get_profile
from typed_cap import Cap, annotation_extra as ae
from typing import Annotated as Anno, Optional


TEST_PROFILE = get_profile(CFG.cur)
B = TEST_PROFILE.based
G = TEST_PROFILE.val_getter


def test_anno_alias():
    class T(B):
        verbose: Anno[Optional[bool], ae("v")]

    cap = Cap(T)
    res = cap.parse(cmd("-v"))
    assert res.count("verbose") == 1


def test_anno_about():
    cfg_about = "path to config file"

    class T(B):
        config: Anno[Optional[bool], ae(None, cfg_about)]

    cap = Cap(T)
    assert cap._args["config"]["alias"] == None
    assert cap._args["config"]["about"] == cfg_about
