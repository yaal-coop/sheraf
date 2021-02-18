import pytest

from sheraf.tools.dicttools import DictConflictException, merge
from ZODB.ConflictResolution import PersistentReference as PR


def test_edited_once():
    assert {"ref": PR("bar")} == merge(
        {"ref": PR("foo")}, {"ref": PR("foo")}, {"ref": PR("bar")},
    )

    assert {"ref": PR("bar")} == merge(
        {"ref": PR("foo")}, {"ref": PR("bar")}, {"ref": PR("foo")},
    )


def test_added_once():
    assert {"ref": PR("foo")} == merge({}, {"ref": PR("foo")}, {},)

    assert {"ref": PR("foo")} == merge({}, {}, {"ref": PR("foo")},)


def test_deleted_twice():
    assert {} == merge({"ref": PR("foo")}, {}, {},)


def test_added_twice():
    with pytest.raises(DictConflictException):
        merge({}, {"foo": PR("DOH")}, {"foo": PR("NEH")})


def test_edited_twice():
    with pytest.raises(DictConflictException):
        merge({"foo": PR("ZBRLA")}, {"foo": PR("DOH")}, {"foo": PR("NEH")})
