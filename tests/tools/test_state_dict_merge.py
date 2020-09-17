from sheraf.tools.dicttools import merge
from ZODB.ConflictResolution import PersistentReference as PR


def test_edit_both_different_with_pr():
    assert {"ref": PR("ref"), "foo": "after", "bar": "after"} == merge(
        {"ref": PR("ref"), "foo": "before", "bar": "before"},
        {"ref": PR("ref"), "foo": "after", "bar": "before"},
        {"ref": PR("ref"), "foo": "before", "bar": "after"},
    )


def test_edit_nested_both_different_with_pr():
    assert {"deeper": {"ref": PR("ref"), "foo": "after", "bar": "after"}} == merge(
        {"deeper": {"ref": PR("ref"), "foo": "before", "bar": "before"}},
        {"deeper": {"ref": PR("ref"), "foo": "after", "bar": "before"}},
        {"deeper": {"ref": PR("ref"), "foo": "before", "bar": "after"}},
    )


def test_edit_nested_both_different_with_nested_pr():
    assert {"ref": PR("ref"), "deeper": {"foo": "after", "bar": "after"},} == merge(
        {"ref": PR("ref"), "deeper": {"foo": "before", "bar": "before"}},
        {"ref": PR("ref"), "deeper": {"foo": "after", "bar": "before"}},
        {"ref": PR("ref"), "deeper": {"foo": "before", "bar": "after"}},
    )


def test_edit_nested_both_different_with_nested_pr_plus():
    assert {
        "ref": PR("ref"),
        "deeper": {"ref2": PR("ref2"), "foo": "after", "bar": "after"},
    } == merge(
        {
            "ref": PR("ref"),
            "deeper": {"ref2": PR("ref2"), "foo": "before", "bar": "before"},
        },
        {
            "ref": PR("ref"),
            "deeper": {"ref2": PR("ref2"), "foo": "after", "bar": "before"},
        },
        {
            "ref": PR("ref"),
            "deeper": {"ref2": PR("ref2"), "foo": "before", "bar": "after"},
        },
    )
