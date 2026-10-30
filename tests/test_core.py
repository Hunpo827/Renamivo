import os
import shutil
import tempfile
from datetime import datetime

import pytest

from renamer.core import naming as N
from renamer.core import rules as R
from renamer.core import validator as V
from renamer.core.executor import RenamePair, execute, undo, long_path


# ---------------------------------------------------------------- naming

def test_split_name():
    assert N.split_name("a.b.txt") == ("a.b", "txt")
    assert N.split_name(".gitignore") == (".gitignore", "")
    assert N.split_name("README") == ("README", "")
    assert N.split_name("a.") == ("a.", "")
    assert N.split_name("no_ext") == ("no_ext", "")


def test_natural_key_order():
    names = ["img10.jpg", "img2.jpg", "img1.jpg"]
    assert sorted(names, key=N.natural_key) == ["img1.jpg", "img2.jpg", "img10.jpg"]


def test_width_conversion():
    assert N.to_halfwidth("ＡＢＣ１２３（ｘ）") == "ABC123(x)"
    assert N.to_fullwidth("ABC123") == "ＡＢＣ１２３"
    # 只转字母数字，不动标点
    assert N.to_halfwidth("ＡＢ（１）", "alnum") == "AB（1）"


def test_case_helpers():
    assert N.to_title("my cool_file-name") == "My Cool_File-Name"
    assert N.to_capitalize("hello world") == "Hello world"


def test_spaces():
    assert N.collapse_spaces("a   b  c") == "a b c"
    assert N.collapse_spaces("a\u3000\u3000b") == "a b"
    assert N.remove_all_spaces(" a b ") == "ab"


def test_accents():
    assert N.strip_accents("Árvíztűrő") == "Arvizturo"


def test_date_format_friendly():
    assert N.normalize_date_format("YYYY-MM-DD") == "%Y-%m-%d"
    assert N.normalize_date_format("%Y%m%d") == "%Y%m%d"
    assert N.format_now("YYYYMMDD", datetime(2024, 3, 7)) == "20240307"


def test_seq():
    assert N.format_seq(0, 1, 1, 3) == "001"
    assert N.format_seq(4, 1, 1, 3) == "005"
    assert N.format_seq(0, 10, 5, 0) == "10"


# ---------------------------------------------------------------- add

def _ctx(**kw):
    return R.ApplyCtx(now=datetime(2024, 3, 7, 15, 30), parent="相册")


def test_add_prefix():
    r = R.Rule("add", params={"position": "prefix", "content": "IMG_"})
    assert R.apply_rules([r], "a.jpg", 0, _ctx()) == "IMG_a.jpg"


def test_add_stem_suffix_with_seq():
    r = R.Rule("add", params={"position": "stem_suffix", "content": "_{n}",
                              "seq_start": 1, "seq_step": 1, "seq_digits": 3})
    assert R.apply_rules([r], "a.jpg", 0, _ctx()) == "a_001.jpg"
    assert R.apply_rules([r], "a.jpg", 4, _ctx()) == "a_005.jpg"


def test_add_date_token():
    r = R.Rule("add", params={"position": "prefix", "content": "{date}_",
                              "date_format": "YYYYMMDD"})
    assert R.apply_rules([r], "x.txt", 0, _ctx()) == "20240307_x.txt"


def test_add_parent_token():
    r = R.Rule("add", params={"position": "prefix", "content": "{parent}-"})
    assert R.apply_rules([r], "x.txt", 0, _ctx()) == "相册-x.txt"


def test_add_seq_preserves_extension():
    r = R.Rule("add", params={"position": "stem_suffix", "content": "_v{n}",
                              "seq_digits": 2})
    assert R.apply_rules([r], "报告.docx", 0, _ctx()) == "报告_v01.docx"


# ---------------------------------------------------------------- delete

def test_delete_text_in_stem_only():
    r = R.Rule("delete", params={"scope": "stem", "mode": "text", "text": "副本"})
    assert R.apply_rules([r], "文件副本.txt", 0, _ctx()) == "文件.txt"
    # 扩展名里的内容不该被误删
    assert R.apply_rules([r], "a副本.副本", 0, _ctx()) == "a.副本"


def test_delete_first_only():
    r = R.Rule("delete", params={"mode": "text", "text": "a", "first_only": True})
    assert R.apply_rules([r], "aaa.txt", 0, _ctx()) == "aa.txt"


def test_delete_regex():
    r = R.Rule("delete", params={"mode": "regex", "pattern": r"\(\d+\)"})
    assert R.apply_rules([r], "图(3).png", 0, _ctx()) == "图.png"


def test_delete_position():
    r = R.Rule("delete", params={"mode": "position", "pos_from": "head", "count": 3})
    assert R.apply_rules([r], "abc报告.txt", 0, _ctx()) == "报告.txt"
    r2 = R.Rule("delete", params={"mode": "position", "pos_from": "tail", "count": 2})
    assert R.apply_rules([r2], "报告xy.txt", 0, _ctx()) == "报告.txt"


def test_delete_brackets():
    r = R.Rule("delete", params={"mode": "brackets", "bracket": "（）"})
    assert R.apply_rules([r], "图片（第2张）.jpg", 0, _ctx()) == "图片.jpg"
    r2 = R.Rule("delete", params={"mode": "brackets", "bracket": "()",
                                 "keep_bracket": True})
    assert R.apply_rules([r2], "photo(2).jpg", 0, _ctx()) == "photo().jpg"


# ---------------------------------------------------------------- replace

def test_replace_literal():
    r = R.Rule("replace", params={"find": " ", "repl": "_"})
    assert R.apply_rules([r], "my file name.txt", 0, _ctx()) == "my_file_name.txt"


def test_replace_regex_backref():
    r = R.Rule("replace", params={"find": r"(\d{4})-(\d{2})", "repl": r"\2_\1",
                                 "use_regex": True})
    assert R.apply_rules([r], "2024-03报告.xlsx", 0, _ctx()) == "03_2024报告.xlsx"


def test_replace_regex_dollar_backref():
    r = R.Rule("replace", params={"find": r"(\w+) \((\d+)\)", "repl": "$2-$1",
                                 "use_regex": True})
    assert R.apply_rules([r], "song (3).mp3", 0, _ctx()) == "3-song.mp3"


def test_replace_ignore_case():
    r = R.Rule("replace", params={"find": "abc", "repl": "X", "ignore_case": True})
    assert R.apply_rules([r], "ABCabc.txt", 0, _ctx()) == "XX.txt"


# ---------------------------------------------------------------- convert

def test_convert_ext_upper():
    r = R.Rule("convert", params={"scope": "ext", "case": "upper"})
    assert R.apply_rules([r], "a.jpg", 0, _ctx()) == "a.JPG"


def test_convert_stem_upper_keeps_ext():
    r = R.Rule("convert", params={"scope": "stem", "case": "upper"})
    assert R.apply_rules([r], "aB.jpg", 0, _ctx()) == "AB.jpg"


def test_convert_full_lower():
    r = R.Rule("convert", params={"scope": "full", "case": "lower"})
    assert R.apply_rules([r], "ABC.JPG", 0, _ctx()) == "abc.jpg"


def test_convert_fullwidth_symbols():
    r = R.Rule("convert", params={"scope": "stem", "width": "half", "width_scope": "punct"})
    assert R.apply_rules([r], "标题（二）.txt", 0, _ctx()) == "标题(二).txt"


def test_convert_collapse_and_trim():
    r = R.Rule("convert", params={"trim": True, "collapse": True})
    assert R.apply_rules([r], "a   b  c.txt", 0, _ctx()) == "a b c.txt"


def test_convert_set_ext():
    r = R.Rule("convert", params={"set_ext": "jpeg"})
    assert R.apply_rules([r], "a.png", 0, _ctx()) == "a.jpeg"
    # 没有扩展名的文件也能加上
    assert R.apply_rules([r], "README", 0, _ctx()) == "README.jpeg"


def test_multi_rule_pipeline():
    rs = [
        R.Rule("add", params={"position": "prefix", "content": "{date}_"}),
        R.Rule("replace", params={"find": " ", "repl": "-"}),
        R.Rule("convert", params={"scope": "ext", "case": "lower"}),
    ]
    out = R.apply_rules(rs, "My Photo.JPG", 0, _ctx())
    assert out == "20240307_My-Photo.jpg"


def test_disabled_rule_skipped():
    r = R.Rule("add", params={"position": "prefix", "content": "X_"}, )
    r.enabled = False
    assert R.apply_rules([r], "a.txt", 0, _ctx()) == "a.txt"


def test_broken_regex_does_not_crash():
    r = R.Rule("replace", params={"find": "(", "use_regex": True, "repl": ""})
    assert R.apply_rules([r], "a(b.txt", 0, _ctx()) == "a(b.txt"


# ---------------------------------------------------------------- validator

def test_validate_bad_names():
    assert V.validate_name("") is not None
    assert V.validate_name("a/b.txt") is not None
    assert V.validate_name("a:b.txt") is not None
    assert V.validate_name("CON.txt") is not None
    assert V.validate_name(".hidden") is None
    assert V.validate_name("正常文件名.txt") is None


class FakeItem:
    def __init__(self, name):
        self.name = name


def test_evaluate_duplicates():
    items = [FakeItem("a.txt"), FakeItem("b.txt")]
    ps = V.evaluate(items, ["same.txt", "SAME.txt"], {})
    assert all(p.status == V.STATUS_CONFLICT for p in ps)


def test_evaluate_unchanged_and_exists():
    items = [FakeItem("a.txt")]
    assert V.evaluate(items, ["a.txt"], {"": {"a.txt"}})[0].status == V.STATUS_UNCHANGED
    assert V.evaluate(items, ["b.txt"], {"": {"b.txt", "a.txt"}})[0].status == V.STATUS_CONFLICT


def test_evaluate_swap_is_allowed():
    items = [FakeItem("a.txt"), FakeItem("b.txt")]
    ps = V.evaluate(items, ["b.txt", "a.txt"], {"": {"a.txt", "b.txt"}})
    assert all(p.status == V.STATUS_OK for p in ps)


# ---------------------------------------------------------------- executor

@pytest.fixture
def tmpdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _touch(d, name, content="x"):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


def test_execute_basic(tmpdir):
    a = _touch(tmpdir, "a.txt", "A")
    b = _touch(tmpdir, "b.txt", "B")
    pairs = [RenamePair(a, os.path.join(tmpdir, "a2.txt")),
             RenamePair(b, os.path.join(tmpdir, "b2.txt"))]
    r = execute(pairs)
    assert r.ok and r.done == 2
    assert sorted(os.listdir(tmpdir)) == ["a2.txt", "b2.txt"]
    with open(os.path.join(tmpdir, "a2.txt"), encoding="utf-8") as f:
        assert f.read() == "A"


def test_execute_case_only_rename(tmpdir):
    a = _touch(tmpdir, "photo.JPG")
    r = execute([RenamePair(a, os.path.join(tmpdir, "photo.jpg"))])
    assert r.ok
    assert os.listdir(tmpdir) == ["photo.jpg"]


def test_execute_swap(tmpdir):
    a = _touch(tmpdir, "a.txt", "A")
    b = _touch(tmpdir, "b.txt", "B")
    pairs = [RenamePair(a, os.path.join(tmpdir, "b.txt")),
             RenamePair(b, os.path.join(tmpdir, "a.txt"))]
    r = execute(pairs)
    assert r.ok
    with open(os.path.join(tmpdir, "a.txt"), encoding="utf-8") as f:
        assert f.read() == "B"
    with open(os.path.join(tmpdir, "b.txt"), encoding="utf-8") as f:
        assert f.read() == "A"


def test_execute_refuses_existing_target(tmpdir):
    a = _touch(tmpdir, "a.txt")
    _touch(tmpdir, "taken.txt")
    r = execute([RenamePair(a, os.path.join(tmpdir, "taken.txt"))])
    assert not r.ok
    assert os.path.exists(a)


def test_execute_no_temp_left_behind(tmpdir):
    a = _touch(tmpdir, "a.txt")
    execute([RenamePair(a, os.path.join(tmpdir, "z.txt"))])
    assert not any(n.startswith(".~brn_") for n in os.listdir(tmpdir))


def test_undo_restores(tmpdir):
    a = _touch(tmpdir, "a.txt", "A")
    new = os.path.join(tmpdir, "a-new.txt")
    assert execute([RenamePair(a, new)]).ok
    r = undo([{"old": a, "new": new}])
    assert r.ok
    assert os.listdir(tmpdir) == ["a.txt"]


def test_long_path_helper():
    p = long_path(os.path.join(os.getcwd(), "x.txt"))
    assert p
