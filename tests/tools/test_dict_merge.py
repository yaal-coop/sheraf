import pytest
from sheraf.tools.dicttools import DictConflictException
from sheraf.tools.dicttools import merge


def test_conflict():
    with pytest.raises(DictConflictException):
        merge({"deeper": {}}, {"deeper": {"foo": "DOH"}}, {"deeper": {"foo": "NEH"}})


def test_empty():
    assert {} == merge({}, {}, {})


def test_empty_apply_diff_left():
    assert {"foo": "bar"} == merge({}, {"foo": "bar"}, {})


def test_empty_apply_diff_right():
    assert {"foo": "bar"} == merge({}, {}, {"foo": "bar"})


def test_empty_apply_diff_both_same():
    assert {"foo": "bar"} == merge({}, {"foo": "bar"}, {"foo": "bar"})


def test_empty_apply_diff_both_different():
    assert {"foo": "bar", "boo": "far"} == merge({}, {"boo": "far"}, {"foo": "bar"})


def test_edit_both_different():
    assert {"foo": "after", "bar": "after"} == merge(
        {"foo": "before", "bar": "before"},
        {"foo": "after", "bar": "before"},
        {"foo": "before", "bar": "after"},
    )


def test_not_empty_deletion():
    assert {} == merge({"boo": "far"}, {}, {})


def test_not_empty_apply_diff_left():
    assert {"foo": "bar", "boo": "far"} == merge(
        {"boo": "far"}, {"boo": "far", "foo": "bar"}, {"boo": "far"}
    )


def test_not_empty_apply_diff_right():
    assert {"foo": "bar", "boo": "far"} == merge(
        {"boo": "far"}, {"boo": "far"}, {"boo": "far", "foo": "bar"}
    )


def test_not_empty_apply_diff_both_same():
    assert {"foo": "bar", "boo": "far"} == merge(
        {"boo": "far"}, {"boo": "far", "foo": "bar"}, {"boo": "far", "foo": "bar"}
    )


def test_not_empty_apply_diff_both_different():
    assert {"foo": "bar", "boo": "far", "bar": "buz"} == merge(
        {"boo": "far"}, {"boo": "far", "bar": "buz"}, {"boo": "far", "foo": "bar"}
    )


def test_nested():
    assert {"deeper": {}} == merge({"deeper": {}}, {"deeper": {}}, {"deeper": {}})


def test_nested_apply_diff_left():
    assert {"deeper": {"foo": "bar"}} == merge(
        {"deeper": {}}, {"deeper": {"foo": "bar"}}, {"deeper": {}}
    )


def test_nested_apply_diff_right():
    assert {"deeper": {"foo": "bar"}} == merge(
        {"deeper": {}}, {"deeper": {}}, {"deeper": {"foo": "bar"}}
    )


def test_nested_apply_diff_both_same():
    assert {"deeper": {"foo": "bar"}} == merge(
        {"deeper": {}}, {"deeper": {"foo": "bar"}}, {"deeper": {"foo": "bar"}}
    )


def test_nested_apply_diff_both_different():
    assert {"deeper": {"foo": "bar", "boo": "far"}} == merge(
        {"deeper": {}}, {"deeper": {"boo": "far"}}, {"deeper": {"foo": "bar"}}
    )
